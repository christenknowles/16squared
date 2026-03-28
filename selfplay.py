#!/usr/bin/env python3
"""
selfplay.py — 16 Squared AI self-play analysis
Runs NUM_GAMES AI vs AI games and produces a detailed balance/strategy report.

Usage:  python selfplay.py
"""

import sys
import time
import random
import numpy as np
from collections import defaultdict

# Force UTF-8 output so box-drawing and symbol characters print correctly on
# Windows terminals that default to cp1252.
sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────────────────────────────────────
# Import SixteenSquaredEngine directly from app.py without running Streamlit.
# We extract the class source between its definition line and the colour
# constants block, then exec it so the class lands in this module's namespace.
# app.py is never modified.
# ─────────────────────────────────────────────────────────────────────────────
with open('app.py', encoding='utf-8') as _f:
    _src = _f.read()

_cls_src = _src[
    _src.index('class SixteenSquaredEngine:') :
    _src.index('# ── COLOURS')          # stop before colour constants
]
exec(compile(_cls_src, 'app.py', 'exec'))
# SixteenSquaredEngine is now available in this module's scope.


# ─────────────────────────────────────────────────────────────────────────────
# Baseline results from the previous 500-game run (pre-90/10 framework)
# Used for direct comparison in the report.
# ─────────────────────────────────────────────────────────────────────────────
BASELINE = {
    'N': 500,
    'wins_p1_pct': 68.0,
    'wins_p2_pct': 29.2,
    'draws_pct':    2.8,
    'avg_p1':      62.9,
    'avg_p2':      51.7,
    'avg_combined': 114.6,
    'avg_margin':   18.5,
    'blocking_pct': 16.7,   # combined blocking rate
    # Direction usage (total moves across all 500 games, both players)
    'dir_usage': {'N': 1171, 'S': 1147, 'E': 1058, 'W': 1092,
                  'NE': 2605, 'NW': 2678, 'SE': 2609, 'SW': 2640},
    # Scoring efficiency per direction
    'dir_eff': {'N': 7.7, 'S': 7.4, 'E': 7.5, 'W': 6.9,
                'NE': 60.0, 'NW': 61.1, 'SE': 62.0, 'SW': 60.7},
    # First player advantage
    'fp_win_rate': 0.680,
    'score_gap':   11.2,
    # Token waste
    'waste_pct': 26.7,
}

CARDINAL_DIRS  = {'N', 'S', 'E', 'W'}
DIAGONAL_DIRS  = {'NE', 'NW', 'SE', 'SW'}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _flip(board: np.ndarray) -> np.ndarray:
    """
    Return a copy of `board` with player-1 and player-2 tokens swapped.
    Because SixteenSquaredEngine.get_ai_move / should_ai_pass always evaluate
    from the perspective of player 2, we flip the board so player 1 can use
    the exact same AI logic.
    """
    b = board.copy()
    b[board == 1] = 2
    b[board == 2] = 1
    return b


# ─────────────────────────────────────────────────────────────────────────────
# Core game runner
# ─────────────────────────────────────────────────────────────────────────────

def run_game(game_idx: int) -> dict:
    """
    Play one complete AI vs AI game and return a stats dictionary.

    Alternation:
      even game_idx → player 1 = side A  (goes first)
      odd  game_idx → player 1 = side B  (goes first)

    Both sides use the same SixteenSquaredEngine AI; the _flip() trick lets
    player 1 evaluate moves with a player-2-perspective engine.
    """
    engine       = SixteenSquaredEngine()
    board        = np.zeros((16, 16), dtype=int)
    token_groups = list(range(15, 0, -1))   # [15, 14, 13, …, 1]

    # Per-game accumulators
    passes          = {1: 0, 2: 0}
    tokens_used     = {1: 0, 2: 0}
    tokens_avail    = {1: 0, 2: 0}
    starts_used     = {1: [], 2: []}
    dirs_used       = {1: [], 2: []}
    dirs_scored     = {1: [], 2: []}   # direction of a move that produced points
    blocking_moves  = {1: 0, 2: 0}
    offensive_moves = {1: 0, 2: 0}
    rounds_data     = []
    prev_s          = {1: 0, 2: 0}    # scores at end of each player's last turn

    # ── New: 90/10 framework tracking ────────────────────────────────────────
    # Territory denial counts for each cardinal move (both players combined)
    cardinal_denials = []

    # Early-round (rounds 1-5) direction breakdown per player
    early_dirs = {1: {'cardinal': 0, 'diagonal': 0},
                  2: {'cardinal': 0, 'diagonal': 0}}

    # Late-round (rounds 6-15) direction breakdown per player
    late_dirs  = {1: {'cardinal': 0, 'diagonal': 0},
                  2: {'cardinal': 0, 'diagonal': 0}}

    # Strategic lockup: rounds where neither player made a meaningful move
    # Meaningful Offensive Move: ends on far border (border-to-border) OR
    #     bridges through at least one existing own token (extends partial line)
    # Meaningful Block: covers a cell in the near-complete threat scan map
    lockup_round_nums = []

    for turn in range(15):
        max_tk = token_groups[turn]
        rn     = turn + 1

        tokens_avail[1] += max_tk
        tokens_avail[2] += max_tk

        rdata = {
            'round': rn, 'max_tokens': max_tk,
            'p1_pass': True, 'p2_pass': True,
            'p1_tokens': 0,  'p2_tokens': 0,
            'p1_gain': 0,    'p2_gain': 0,
            'p1_meaningful': False, 'p2_meaningful': False,
            'p1_cardinal': False,   'p2_cardinal': False,
        }

        for p in [1, 2]:
            # Board from the AI's (player-2) perspective
            eff       = board if p == 2 else _flip(board)
            made_move = False

            if not engine.should_ai_pass(eff, max_tk, rn):
                move = engine.get_ai_move(eff, max_tk, rn)
                if move is not None:
                    ax, ay, ad, tc = move
                    ok, path, _   = engine.simulate_path(eff, 2, ax, ay, ad, tc)
                    if ok and path:
                        # Detect blocking intent: does this path cover any cell
                        # flagged by the near-complete-threat scanner?
                        bmap        = engine._build_blocking_map(eff)
                        is_blocking = any(bmap[py, px] > 0 for px, py in path)

                        # ── Direction type ────────────────────────────────────
                        is_cardinal = ad in CARDINAL_DIRS

                        # ── Territory denial count for cardinal moves ─────────
                        if is_cardinal:
                            denial = engine._evaluate_territory_denial(eff, path)
                            cardinal_denials.append(denial)
                        else:
                            denial = 0

                        # ── Meaningful move classification ────────────────────
                        # Meaningful Offensive Move — any ONE of three criteria:
                        #   1. Reaches far border (border-to-border potential scoring line)
                        #   2. Bridges ≥1 own existing token (extends a partial line)
                        #   3. Denies ≥5 opponent corridors via territory denial
                        #      (captures large cardinal walls that don't reach the far
                        #      border yet — e.g. a 15-token R1 horizontal wall is a
                        #      strong strategic move even if it stops 1 cell short)
                        bridges_own    = any(eff[py, px] == 2 for px, py in path)
                        reaches_border = engine.is_border(path[-1][0], path[-1][1])
                        high_denial    = is_cardinal and denial >= 5
                        is_meaningful_offensive = reaches_border or bridges_own or high_denial
                        # Meaningful Block: covers near-complete threat cell
                        is_meaningful_block = is_blocking
                        is_meaningful = is_meaningful_offensive or is_meaningful_block

                        # ── Apply new tokens to the original board ────────────
                        new_cells = [(px, py) for px, py in path
                                     if board[py, px] == 0]
                        for px, py in new_cells:
                            board[py, px] = p

                        tokens_used[p] += len(new_cells)
                        starts_used[p].append((ax, ay))
                        dirs_used[p].append(ad)

                        if is_blocking:
                            blocking_moves[p]  += 1
                        else:
                            offensive_moves[p] += 1

                        # Early vs late direction tracking
                        bucket = early_dirs if rn <= 5 else late_dirs
                        if is_cardinal:
                            bucket[p]['cardinal'] += 1
                        else:
                            bucket[p]['diagonal'] += 1

                        rdata[f'p{p}_pass']        = False
                        rdata[f'p{p}_tokens']      = len(new_cells)
                        rdata[f'p{p}_meaningful']  = is_meaningful
                        rdata[f'p{p}_cardinal']    = is_cardinal
                        made_move = True

            if not made_move:
                passes[p] += 1

            # Score delta: compare against this player's score before their move
            cur_s         = engine.calculate_scores(board)
            gain          = cur_s[p - 1] - prev_s[p]
            prev_s[p]     = cur_s[p - 1]
            rdata[f'p{p}_gain'] = gain

            # Record direction→scored association
            if gain > 0 and dirs_used[p]:
                dirs_scored[p].append(dirs_used[p][-1])

        rdata['both_passed'] = rdata['p1_pass'] and rdata['p2_pass']

        # Strategic lockup: neither player made a meaningful move this round
        if not rdata['p1_meaningful'] and not rdata['p2_meaningful']:
            lockup_round_nums.append(rn)

        rounds_data.append(rdata)

    final  = engine.calculate_scores(board)
    winner = 1 if final[0] > final[1] else (2 if final[1] > final[0] else 0)

    # Count scoring lines for each player at end of game
    scoring_lines = engine.get_scoring_lines(board)
    lines_p1 = len(scoring_lines[1])
    lines_p2 = len(scoring_lines[2])

    return {
        'game_idx':          game_idx,
        'first_is_A':        (game_idx % 2 == 0),
        'score_p1':          final[0],
        'score_p2':          final[1],
        'winner':            winner,
        'lines_p1':          lines_p1,
        'lines_p2':          lines_p2,
        'rounds':            rounds_data,
        'passes':            passes,
        'tokens_used':       tokens_used,
        'tokens_avail':      tokens_avail,
        'starts_used':       starts_used,
        'dirs_used':         dirs_used,
        'dirs_scored':       dirs_scored,
        'blocking_moves':    blocking_moves,
        'offensive_moves':   offensive_moves,
        'cardinal_denials':  cardinal_denials,
        'early_dirs':        early_dirs,
        'late_dirs':         late_dirs,
        'lockup_round_nums': lockup_round_nums,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation
# ─────────────────────────────────────────────────────────────────────────────

def analyse(games: list) -> dict:
    N = len(games)

    # ── Game results ─────────────────────────────────────────────────────────
    wins_p1  = sum(1 for g in games if g['winner'] == 1)
    wins_p2  = sum(1 for g in games if g['winner'] == 2)
    draws    = sum(1 for g in games if g['winner'] == 0)
    scores_p1 = [g['score_p1'] for g in games]
    scores_p2 = [g['score_p2'] for g in games]
    margins   = [abs(g['score_p1'] - g['score_p2']) for g in games]
    non_draw_margins = [m for m in margins if m > 0]

    all_scores = scores_p1 + scores_p2
    score_buckets = defaultdict(int)
    for s in all_scores:
        score_buckets[(s // 10) * 10] += 1

    # ── First-player advantage ────────────────────────────────────────────────
    fp_win_rate = wins_p1 / N
    sp_win_rate = wins_p2 / N

    # ── Strategic patterns ────────────────────────────────────────────────────
    start_counts = defaultdict(int)
    dir_usage    = defaultdict(int)
    dir_scoring  = defaultdict(int)

    for g in games:
        for p in [1, 2]:
            for xy in g['starts_used'][p]:
                start_counts[xy] += 1
            for d in g['dirs_used'][p]:
                dir_usage[d] += 1
            for d in g['dirs_scored'][p]:
                dir_scoring[d] += 1

    # Score gained per round (sum over all games and both players)
    round_total_gain  = defaultdict(int)
    round_p1_gain     = defaultdict(int)
    round_p2_gain     = defaultdict(int)
    for g in games:
        for r in g['rounds']:
            rn = r['round']
            round_total_gain[rn] += r['p1_gain'] + r['p2_gain']
            round_p1_gain[rn]    += r['p1_gain']
            round_p2_gain[rn]    += r['p2_gain']

    # Scoring lines per player
    avg_lines_p1 = np.mean([g['lines_p1'] for g in games])
    avg_lines_p2 = np.mean([g['lines_p2'] for g in games])

    # ── Board lockup analysis ─────────────────────────────────────────────────
    double_pass_by_round = defaultdict(int)
    unused_by_round      = defaultdict(int)
    total_unused = 0
    total_avail  = 0

    for g in games:
        for r in g['rounds']:
            rn = r['round']
            if r['both_passed']:
                double_pass_by_round[rn] += 1
            unused = (r['max_tokens'] - r['p1_tokens']) + \
                     (r['max_tokens'] - r['p2_tokens'])
            unused_by_round[rn] += unused
            total_unused += unused
            total_avail  += r['max_tokens'] * 2

    lockup_games = sum(
        1 for g in games
        if sum(1 for r in g['rounds']
               if 7 <= r['round'] <= 10 and r['both_passed']) >= 2
    )

    # ── AI behaviour ─────────────────────────────────────────────────────────
    total_passes   = {p: sum(g['passes'][p]          for g in games) for p in [1, 2]}
    total_tok_used = {p: sum(g['tokens_used'][p]     for g in games) for p in [1, 2]}
    total_tok_avail= {p: sum(g['tokens_avail'][p]    for g in games) for p in [1, 2]}
    total_blocking = {p: sum(g['blocking_moves'][p]  for g in games) for p in [1, 2]}
    total_offensive= {p: sum(g['offensive_moves'][p] for g in games) for p in [1, 2]}

    # ── New: 90/10 framework metrics ──────────────────────────────────────────

    # Territory denial — aggregate over all cardinal moves
    all_denials = []
    for g in games:
        all_denials.extend(g['cardinal_denials'])
    avg_denial_per_cardinal = np.mean(all_denials) if all_denials else 0.0
    total_cardinal_moves    = len(all_denials)

    # Early vs late direction breakdown (both players combined)
    early_cardinal = sum(g['early_dirs'][p]['cardinal']
                         for g in games for p in [1, 2])
    early_diagonal = sum(g['early_dirs'][p]['diagonal']
                         for g in games for p in [1, 2])
    late_cardinal  = sum(g['late_dirs'][p]['cardinal']
                         for g in games for p in [1, 2])
    late_diagonal  = sum(g['late_dirs'][p]['diagonal']
                         for g in games for p in [1, 2])

    # Per-round direction breakdown (cardinal vs diagonal, both players)
    round_cardinal = defaultdict(int)
    round_diagonal = defaultdict(int)
    for g in games:
        for r in g['rounds']:
            rn = r['round']
            for p_label in ['p1', 'p2']:
                if not r[f'{p_label}_pass']:
                    if r[f'{p_label}_cardinal']:
                        round_cardinal[rn] += 1
                    else:
                        round_diagonal[rn] += 1

    # Early cardinals correlation with win rate:
    # For each game, count total early cardinals and note winner
    winner_early_cards   = []
    loser_early_cards    = []
    winner_early_denials = []
    loser_early_denials  = []

    for g in games:
        if g['winner'] == 0:
            continue
        w = g['winner']
        l = 3 - w  # 1→2, 2→1
        winner_early_cards.append(g['early_dirs'][w]['cardinal'])
        loser_early_cards.append(g['early_dirs'][l]['cardinal'])

    avg_winner_early_cards = np.mean(winner_early_cards) if winner_early_cards else 0.0
    avg_loser_early_cards  = np.mean(loser_early_cards)  if loser_early_cards  else 0.0

    # Games split by high/low early cardinal usage (combined both players)
    combined_early_cards = [
        g['early_dirs'][1]['cardinal'] + g['early_dirs'][2]['cardinal']
        for g in games
    ]
    median_early = np.median(combined_early_cards)
    high_card_games = [g for g, c in zip(games, combined_early_cards) if c > median_early]
    low_card_games  = [g for g, c in zip(games, combined_early_cards) if c <= median_early]

    high_card_avg_combined = (
        np.mean([g['score_p1'] + g['score_p2'] for g in high_card_games])
        if high_card_games else 0.0
    )
    low_card_avg_combined  = (
        np.mean([g['score_p1'] + g['score_p2'] for g in low_card_games])
        if low_card_games else 0.0
    )
    high_card_p1_winrate = (
        sum(1 for g in high_card_games if g['winner'] == 1) / len(high_card_games)
        if high_card_games else 0.0
    )
    low_card_p1_winrate = (
        sum(1 for g in low_card_games if g['winner'] == 1) / len(low_card_games)
        if low_card_games else 0.0
    )

    # ── Strategic lockup (official definitions) ───────────────────────────────
    lockup_by_round   = defaultdict(int)   # how many games had lockup in round N
    total_lockup_rounds = 0                # total lockup rounds across all games
    games_with_lockup   = 0               # games with ≥1 lockup round

    for g in games:
        had_lockup = False
        for r in g['rounds']:
            rn = r['round']
            # A round is a strategic lockup round if neither player made
            # a meaningful move (pass counts as non-meaningful)
            if not r['p1_meaningful'] and not r['p2_meaningful']:
                lockup_by_round[rn] += 1
                total_lockup_rounds += 1
                had_lockup = True
        if had_lockup:
            games_with_lockup += 1

    avg_lockup_per_game = total_lockup_rounds / N

    return dict(
        N=N,
        wins_p1=wins_p1, wins_p2=wins_p2, draws=draws,
        scores_p1=scores_p1, scores_p2=scores_p2,
        margins=margins, non_draw_margins=non_draw_margins,
        score_buckets=score_buckets,
        fp_win_rate=fp_win_rate, sp_win_rate=sp_win_rate,
        start_counts=start_counts,
        dir_usage=dir_usage, dir_scoring=dir_scoring,
        round_total_gain=round_total_gain,
        round_p1_gain=round_p1_gain, round_p2_gain=round_p2_gain,
        avg_lines_p1=avg_lines_p1, avg_lines_p2=avg_lines_p2,
        double_pass_by_round=double_pass_by_round,
        unused_by_round=unused_by_round,
        total_unused=total_unused, total_avail=total_avail,
        lockup_games=lockup_games,
        total_passes=total_passes,
        total_tok_used=total_tok_used, total_tok_avail=total_tok_avail,
        total_blocking=total_blocking, total_offensive=total_offensive,
        # 90/10 framework
        all_denials=all_denials,
        avg_denial_per_cardinal=avg_denial_per_cardinal,
        total_cardinal_moves=total_cardinal_moves,
        early_cardinal=early_cardinal, early_diagonal=early_diagonal,
        late_cardinal=late_cardinal,   late_diagonal=late_diagonal,
        round_cardinal=round_cardinal, round_diagonal=round_diagonal,
        avg_winner_early_cards=avg_winner_early_cards,
        avg_loser_early_cards=avg_loser_early_cards,
        median_early_cards=median_early,
        high_card_avg_combined=high_card_avg_combined,
        low_card_avg_combined=low_card_avg_combined,
        high_card_p1_winrate=high_card_p1_winrate,
        low_card_p1_winrate=low_card_p1_winrate,
        high_card_n=len(high_card_games), low_card_n=len(low_card_games),
        # Strategic lockup
        lockup_by_round=lockup_by_round,
        total_lockup_rounds=total_lockup_rounds,
        games_with_lockup=games_with_lockup,
        avg_lockup_per_game=avg_lockup_per_game,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Report printer
# ─────────────────────────────────────────────────────────────────────────────

def print_report(games: list, a: dict) -> None:
    N    = a['N']
    WIDE = '═' * 70
    B    = BASELINE

    def section(title):
        pad = '─' * (68 - len(title))
        print(f'\n┌─ {title} {pad}')

    def delta(new_val, old_val, unit='', higher_is='good', fmt='.1f'):
        diff = new_val - old_val
        arrow = '↑' if diff > 0 else ('↓' if diff < 0 else '→')
        sign  = '+' if diff >= 0 else ''
        if higher_is == 'good':
            flag = '✓' if diff > 0.05 * abs(old_val) else ('✗' if diff < -0.05 * abs(old_val) else '~')
        elif higher_is == 'bad':
            flag = '✗' if diff > 0.05 * abs(old_val) else ('✓' if diff < -0.05 * abs(old_val) else '~')
        else:
            flag = '~'
        return f'{arrow}{sign}{diff:{fmt}}{unit}  [{flag} vs baseline {old_val:{fmt}}{unit}]'

    print()
    print(WIDE)
    print('  16 SQUARED — AI SELF-PLAY ANALYSIS REPORT')
    print(f'  {N} games  ·  AI-A vs AI-B  ·  alternating first player')
    print('  Run: TWO-PHASE OPENING + x22 DENIAL  (vs baseline: 500-game pre-framework run)')
    print(WIDE)

    # ── GAME RESULTS ─────────────────────────────────────────────────────────
    section('GAME RESULTS')
    avg_p1 = np.mean(a['scores_p1'])
    avg_p2 = np.mean(a['scores_p2'])
    all_scores = a['scores_p1'] + a['scores_p2']
    print(f'  First mover  (P1) wins : {a["wins_p1"]:3d} / {N}  ({a["wins_p1"]/N*100:.1f}%)'
          f'  {delta(a["wins_p1"]/N*100, B["wins_p1_pct"], "%", higher_is="neutral")}')
    print(f'  Second mover (P2) wins : {a["wins_p2"]:3d} / {N}  ({a["wins_p2"]/N*100:.1f}%)')
    print(f'  Draws                  : {a["draws"]:3d} / {N}  ({a["draws"]/N*100:.1f}%)')
    print()
    print(f'  Average final score  —  P1: {avg_p1:.1f}  {delta(avg_p1, B["avg_p1"], "pts")}')
    print(f'                          P2: {avg_p2:.1f}  {delta(avg_p2, B["avg_p2"], "pts")}')
    avg_comb = avg_p1 + avg_p2
    print(f'  Average combined score  :  {avg_comb:.1f}  {delta(avg_comb, B["avg_combined"], "pts")}')
    print(f'  Highest single score : {max(all_scores)}')
    print(f'  Lowest  single score : {min(all_scores)}')
    if a['non_draw_margins']:
        print(f'  Biggest  win margin  : {max(a["non_draw_margins"])} pts')
        print(f'  Smallest win margin  : {min(a["non_draw_margins"])} pts')
    print(f'  Average win margin   : {np.mean(a["margins"]):.1f} pts  '
          f'{delta(np.mean(a["margins"]), B["avg_margin"], "pts", higher_is="neutral")}')
    print()
    print(f'  Score distribution (both sides, all {N} games):')
    for bucket in sorted(a['score_buckets']):
        count = a['score_buckets'][bucket]
        bar   = '█' * (count // 2)
        print(f'    {bucket:3d}–{bucket+9:3d} pts : {count:3d}  {bar}')

    # ── FIRST PLAYER ADVANTAGE ────────────────────────────────────────────────
    section('FIRST PLAYER ADVANTAGE')
    fp_wr  = a['fp_win_rate']
    sp_wr  = a['sp_win_rate']
    fp_avg = avg_p1
    sp_avg = avg_p2
    score_gap = fp_avg - sp_avg
    adv_gap   = abs(fp_wr - sp_wr)

    print(f'  Win rate — first mover  : {fp_wr*100:.1f}%  (baseline: {B["fp_win_rate"]*100:.1f}%)')
    print(f'  Win rate — second mover : {sp_wr*100:.1f}%')
    print(f'  Avg score — first mover : {fp_avg:.1f}')
    print(f'  Avg score — second mover: {sp_avg:.1f}')
    print(f'  Score gap (1st − 2nd)   : {score_gap:+.1f} pts  (baseline: +{B["score_gap"]:.1f} pts)')

    if adv_gap < 0.08:
        fpa_verdict = 'No meaningful first-player advantage detected.'
        fpa_rec     = 'No rule change needed for starting order.'
    elif adv_gap < 0.15:
        fpa_verdict = 'Moderate first-player advantage — monitor in player testing.'
        fpa_rec     = 'Consider a minor compensation (e.g. second player gets +2 bonus pts).'
    else:
        fpa_verdict = 'SIGNIFICANT first-player advantage.'
        fpa_rec     = 'Recommend a compensation rule before public beta testing.'

    print(f'\n  Assessment   : {fpa_verdict}')
    print(f'  Recommendation: {fpa_rec}')

    # ── DIRECTION USAGE CHANGES ───────────────────────────────────────────────
    section('DIRECTION USAGE CHANGES')

    total_moves = sum(a['dir_usage'].values())
    card_total  = sum(a['dir_usage'].get(d, 0) for d in CARDINAL_DIRS)
    diag_total  = sum(a['dir_usage'].get(d, 0) for d in DIAGONAL_DIRS)
    card_pct    = card_total / total_moves * 100 if total_moves > 0 else 0
    diag_pct    = diag_total / total_moves * 100 if total_moves > 0 else 0

    b_card_total = sum(B['dir_usage'].get(d, 0) for d in CARDINAL_DIRS)
    b_diag_total = sum(B['dir_usage'].get(d, 0) for d in DIAGONAL_DIRS)
    b_total      = b_card_total + b_diag_total
    b_card_pct   = b_card_total / b_total * 100
    b_diag_pct   = b_diag_total / b_total * 100

    print(f'  Overall direction split (both players, all rounds):')
    print(f'    Cardinals  (N/S/E/W)  : {card_total:5d} moves  ({card_pct:.1f}%)  '
          f'[baseline: {b_card_pct:.1f}%  Δ {card_pct-b_card_pct:+.1f}%]')
    print(f'    Diagonals (NE/NW/SE/SW): {diag_total:5d} moves  ({diag_pct:.1f}%)  '
          f'[baseline: {b_diag_pct:.1f}%  Δ {diag_pct-b_diag_pct:+.1f}%]')

    print()
    print('  Direction usage vs scoring efficiency:')
    all_dirs = ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']
    for d in all_dirs:
        usage   = a['dir_usage'].get(d, 0)
        scored  = a['dir_scoring'].get(d, 0)
        eff_pct = scored / usage * 100 if usage > 0 else 0
        b_usage = B['dir_usage'].get(d, 0)
        b_eff   = B['dir_eff'].get(d, 0.0)
        bar     = '█' * (usage // 20)
        usage_delta = usage - b_usage
        eff_delta   = eff_pct - b_eff
        print(f'    {d:2s}  used {usage:4d} ({usage_delta:+4d})  scored {scored:3d}'
              f'  ({eff_pct:4.1f}%  Δeff {eff_delta:+.1f}%)  {bar}')

    print()
    # Early vs late direction breakdown
    early_total = a['early_cardinal'] + a['early_diagonal']
    late_total  = a['late_cardinal']  + a['late_diagonal']
    early_card_pct = a['early_cardinal'] / early_total * 100 if early_total > 0 else 0
    early_diag_pct = a['early_diagonal'] / early_total * 100 if early_total > 0 else 0
    late_card_pct  = a['late_cardinal']  / late_total  * 100 if late_total  > 0 else 0
    late_diag_pct  = a['late_diagonal']  / late_total  * 100 if late_total  > 0 else 0

    print('  Early-game (rounds 1–5) vs late-game (rounds 6–15) direction split:')
    print(f'    Rounds 1–5  — Cardinals: {a["early_cardinal"]:4d} ({early_card_pct:.1f}%)  '
          f'Diagonals: {a["early_diagonal"]:4d} ({early_diag_pct:.1f}%)')
    print(f'    Rounds 6–15 — Cardinals: {a["late_cardinal"]:4d} ({late_card_pct:.1f}%)  '
          f'Diagonals: {a["late_diagonal"]:4d} ({late_diag_pct:.1f}%)')

    print()
    print('  Per-round direction breakdown (cardinal vs diagonal moves, both players):')
    print('  Rd │ Cardinals │ Diagonals │  Cardinal%')
    print('  ───┼───────────┼───────────┼───────────')
    for rn in range(1, 16):
        nc = a['round_cardinal'].get(rn, 0)
        nd = a['round_diagonal'].get(rn, 0)
        nt = nc + nd
        cp = nc / nt * 100 if nt > 0 else 0
        bar = '█' * int(cp // 5)
        print(f'  {rn:2d} │ {nc:9d} │ {nd:9d} │ {cp:7.1f}%  {bar}')

    # ── TERRITORY DENIAL EFFECTIVENESS ───────────────────────────────────────
    section('TERRITORY DENIAL EFFECTIVENESS')

    total_card = a['total_cardinal_moves']
    avg_denial = a['avg_denial_per_cardinal']
    all_d      = a['all_denials']

    print(f'  Total cardinal moves tracked : {total_card}')
    print(f'  Avg corridors denied / cardinal move : {avg_denial:.2f}')
    if all_d:
        print(f'  Denial distribution:')
        print(f'    Min : {min(all_d)}   Max : {max(all_d)}'
              f'   Median : {np.median(all_d):.1f}   Std : {np.std(all_d):.2f}')
        # Denial buckets
        d_buckets = defaultdict(int)
        for v in all_d:
            d_buckets[v] += 1
        print('  Denials per cardinal move (count of moves):')
        for k in sorted(d_buckets)[:20]:   # cap at 20 to avoid runaway output
            bar = '█' * (d_buckets[k] // max(1, total_card // 200))
            print(f'    {k:2d} corridors : {d_buckets[k]:5d}  {bar}')
        if len(d_buckets) > 20:
            print(f'    ... ({len(d_buckets)-20} more unique denial counts)')

    print()
    print(f'  Winner vs loser early cardinal usage (rounds 1–5):')
    print(f'    Winners used avg {a["avg_winner_early_cards"]:.2f} early cardinal moves')
    print(f'    Losers  used avg {a["avg_loser_early_cards"]:.2f} early cardinal moves')
    diff_early = a['avg_winner_early_cards'] - a['avg_loser_early_cards']
    if diff_early > 0.3:
        print('    → Winners played more early cardinals — territory denial is '
              'positively correlated with winning.')
    elif diff_early < -0.3:
        print('    → Losers played more early cardinals — early cardinal emphasis '
              'may reduce scoring efficiency enough to hurt overall performance.')
    else:
        print('    → No strong correlation between early cardinal usage and outcome.')

    print()
    hi_n  = a['high_card_n']
    lo_n  = a['low_card_n']
    hi_sc = a['high_card_avg_combined']
    lo_sc = a['low_card_avg_combined']
    hi_wr = a['high_card_p1_winrate']
    lo_wr = a['low_card_p1_winrate']
    print(f'  Games split by early cardinal volume (median = {a["median_early_cards"]:.0f} moves):')
    print(f'    High-cardinal games (n={hi_n}): avg combined score {hi_sc:.1f}  '
          f'P1 win rate {hi_wr*100:.1f}%')
    print(f'    Low-cardinal  games (n={lo_n}): avg combined score {lo_sc:.1f}  '
          f'P1 win rate {lo_wr*100:.1f}%')
    score_diff_hilo = hi_sc - lo_sc
    if abs(score_diff_hilo) > 3:
        direction = 'lower' if score_diff_hilo < 0 else 'higher'
        print(f'    → High-cardinal games produce {direction} combined scores ({score_diff_hilo:+.1f} pts).')
        if score_diff_hilo < 0:
            print('      Cardinal walls are suppressing total scoring — territory denial is working.')
        else:
            print('      Cardinals are not limiting opponent scoring as expected.')
    else:
        print('    → No significant difference in combined scores between groups.')

    # ── STRATEGIC PATTERNS ────────────────────────────────────────────────────
    section('STRATEGIC PATTERNS')

    print('  Most-used starting border squares (top 12):')
    top_starts = sorted(a['start_counts'].items(), key=lambda x: -x[1])[:12]
    for (x, y), cnt in top_starts:
        print(f'    ({x:2d},{y:2d})  →  {cnt:4d} uses')

    print()
    print(f'  Average scoring lines per game — P1: {a["avg_lines_p1"]:.2f}   P2: {a["avg_lines_p2"]:.2f}')

    print()
    print('  Score gained per round (both players combined, all games):')
    peak_round = max(a['round_total_gain'], key=a['round_total_gain'].get)
    for rn in range(1, 16):
        gain = a['round_total_gain'].get(rn, 0)
        bar  = '█' * (gain // 100)
        peak = '  ← peak' if rn == peak_round else ''
        print(f'    Round {rn:2d}  +{gain:5d} pts  {bar}{peak}')

    # ── BOARD LOCKUP ANALYSIS ─────────────────────────────────────────────────
    section('BOARD LOCKUP ANALYSIS')

    print('  Double-passes per round (both players passed in same round):')
    for rn in range(1, 16):
        cnt  = a['double_pass_by_round'].get(rn, 0)
        pct  = cnt / N * 100
        bar  = '█' * cnt
        flag = '  ← mid-game focus' if 7 <= rn <= 10 and cnt > 5 else ''
        print(f'    Round {rn:2d} : {cnt:3d} ({pct:4.1f}%)  {bar}{flag}')

    print()
    print('  Unused tokens per round (both players combined):')
    for rn in range(1, 16):
        max_tk = 16 - rn
        avail  = max_tk * 2 * N
        unused = a['unused_by_round'].get(rn, 0)
        pct    = unused / avail * 100 if avail > 0 else 0
        bar    = '█' * (int(pct) // 5)
        print(f'    Round {rn:2d} : {unused:5d}/{avail:5d} unused ({pct:5.1f}%)  {bar}')

    lockup_pct = a['lockup_games'] / N * 100
    waste_pct  = a['total_unused'] / a['total_avail'] * 100
    print()
    print(f'  Games with ≥2 double-passes in rounds 7–10 : {a["lockup_games"]} ({lockup_pct:.1f}%)')
    print(f'  Overall token waste rate                   : '
          f'{a["total_unused"]}/{a["total_avail"]} ({waste_pct:.1f}%)'
          f'  [baseline: {B["waste_pct"]:.1f}%  Δ {waste_pct - B["waste_pct"]:+.1f}%]')
    print()
    if lockup_pct > 20:
        print('  RECOMMENDATION: Mid-game lockup is frequent. Consider reducing')
        print('  peak token count or expanding the board to 18×18.')
    elif lockup_pct > 10:
        print('  RECOMMENDATION: Some mid-game congestion. Monitor in player testing.')
    else:
        print('  RECOMMENDATION: Board lockup is rare. Current token structure')
        print('  and board size appear healthy for 15-round games.')

    # ── AI BEHAVIOR ───────────────────────────────────────────────────────────
    section('AI BEHAVIOR')

    tb_combined = a['total_blocking'][1]  + a['total_blocking'][2]
    to_combined = a['total_offensive'][1] + a['total_offensive'][2]
    blk_overall = tb_combined / (tb_combined + to_combined) * 100 if (tb_combined + to_combined) > 0 else 0

    for p in [1, 2]:
        label     = 'First mover (P1)' if p == 1 else 'Second mover (P2)'
        tp        = a['total_passes'][p]
        tu        = a['total_tok_used'][p]
        ta        = a['total_tok_avail'][p]
        tb        = a['total_blocking'][p]
        to_       = a['total_offensive'][p]
        total_mvs = tb + to_
        pass_pct  = tp / (N * 15) * 100
        waste_p   = (ta - tu) / ta * 100 if ta > 0 else 0
        blk_pct   = tb / total_mvs * 100 if total_mvs > 0 else 0
        avg_used  = tu / N / 15

        print(f'  {label}:')
        print(f'    Pass rate        : {tp}/{N*15} rounds ({pass_pct:.1f}%)')
        print(f'    Avg tokens/round : {avg_used:.1f}')
        print(f'    Token waste      : {ta-tu}/{ta} ({waste_p:.1f}%)')
        print(f'    Blocking moves   : {tb}/{total_mvs} ({blk_pct:.1f}%)'
              f'  [baseline: {B["blocking_pct"]:.1f}%  Δ {blk_pct - B["blocking_pct"]:+.1f}%]')
        print(f'    Offensive moves  : {to_}/{total_mvs} ({100-blk_pct:.1f}%)')
        print()

    print(f'  Combined blocking rate: {blk_overall:.1f}%  '
          f'[baseline: {B["blocking_pct"]:.1f}%  Δ {blk_overall - B["blocking_pct"]:+.1f}%]')

    # ── STRATEGIC LOCKUP ──────────────────────────────────────────────────────
    section('STRATEGIC LOCKUP  (Official Definitions)')

    print('  Definitions used:')
    print('    Meaningful Offensive Move: path ends on far border (border-to-border)')
    print('      OR bridges through ≥1 own existing token (extends partial line).')
    print('    Meaningful Block: path covers a cell flagged by _build_blocking_map()')
    print('      (i.e. directly intersects an opponent near-complete threat line).')
    print('    Strategic Lockup Round: neither player made a meaningful move (passes')
    print('      and non-meaningful placements both count as non-meaningful).')
    print()

    print(f'  Total strategic lockup rounds (all {N} games) : {a["total_lockup_rounds"]}')
    print(f'  Average lockup rounds per game               : {a["avg_lockup_per_game"]:.2f}')
    print(f'  Games with ≥1 lockup round                  : '
          f'{a["games_with_lockup"]} ({a["games_with_lockup"]/N*100:.1f}%)')
    print()
    print('  Lockup rounds by round number:')
    print('  Rd │ Count │ % of games │ Bar')
    print('  ───┼───────┼────────────┼───────────────────────')
    for rn in range(1, 16):
        cnt = a['lockup_by_round'].get(rn, 0)
        pct = cnt / N * 100
        bar = '█' * (cnt // max(1, N // 100))
        focus = '  ← mid-game' if 7 <= rn <= 10 and cnt > N * 0.05 else ''
        print(f'  {rn:2d} │ {cnt:5d} │ {pct:8.1f}%  │ {bar}{focus}')
    print()

    # Verdict on strategic lockup
    lockup_rate = a['avg_lockup_per_game']
    if lockup_rate < 1.0:
        print('  VERDICT: Strategic lockup is rare. Both players consistently find')
        print('  meaningful moves throughout the game. The 90/10 framework has not')
        print('  introduced non-productive move patterns.')
    elif lockup_rate < 3.0:
        print('  VERDICT: Occasional strategic lockup. A small number of rounds per')
        print('  game produce non-meaningful moves for both players. This is typical')
        print('  in late-game phases as the board fills and options narrow.')
    else:
        print('  VERDICT: Frequent strategic lockup detected. The AI may be choosing')
        print('  moves that are neither clearly offensive nor clearly blocking.')
        print('  Review weight calibration for cardinal and diagonal paths.')

    # ── BALANCE ASSESSMENT ────────────────────────────────────────────────────
    section('BALANCE ASSESSMENT')

    avg_combined = avg_p1 + avg_p2
    avg_margin   = np.mean(a['margins'])
    min_score    = min(all_scores)
    max_score    = max(all_scores)

    print(f'  Average combined score per game : {avg_combined:.1f} pts  '
          f'[baseline: {B["avg_combined"]:.1f}]')
    print(f'  Average score differential      : {avg_margin:.1f} pts  '
          f'[baseline: {B["avg_margin"]:.1f}]')
    print(f'  Score range (single player)     : {min_score} – {max_score} pts')
    print()

    if avg_combined > 130:
        sv = 'Very high. Consider reducing token budgets or board size.'
    elif avg_combined > 80:
        sv = 'Healthy for a strategy game of this length.'
    elif avg_combined > 40:
        sv = 'Low-moderate. Players may struggle to feel meaningful progress.'
    else:
        sv = 'Low. Very few scoring lines complete. Board may be over-constraining.'
    print(f'  Scoring level : {sv}')
    print()

    print('  Structural notes:')
    side_gap = abs(a['wins_p1'] - a['wins_p2']) / N
    if side_gap > 0.10 and a['wins_p1'] > a['wins_p2']:
        print('  • First mover wins consistently more often. A compensation rule')
        print('    (e.g. second player gets a small bonus) may be worth testing.')
    elif side_gap > 0.10:
        print('  • Second mover wins more often than expected.')
    else:
        print('  • Win distribution is balanced between first and second mover.')

    if blk_overall < 10:
        print('  • AI rarely blocks (< 10% of moves). Game skews heavily offensive.')
    elif blk_overall > 35:
        print('  • High blocking rate. AI vs AI games may be unusually defensive.')
    else:
        print(f'  • Blocking rate of {blk_overall:.1f}% reflects a healthy offense/defense mix.')

    overall_waste = a['total_unused'] / a['total_avail'] * 100
    if overall_waste > 35:
        print(f'  • {overall_waste:.0f}% of tokens went unused. Late rounds have low activity.')
    else:
        print(f'  • Token utilisation is healthy ({100-overall_waste:.0f}% of tokens placed).')

    print()
    print('  OVERALL BALANCE VERDICT:')
    balanced_wr = 0.40 <= a['fp_win_rate'] <= 0.60
    if balanced_wr:
        print('  ✓ Win rate is within the 40–60% balanced range.')
    else:
        print('  ⚠ First-mover win rate outside 40–60% range. Consider a small')
        print('    compensation rule before broad beta release.')

    print()
    print('  MID-GAME LOCKUP VERDICT:')
    if lockup_pct > 20:
        print('  ⚠ Board congestion causes meaningful mid-game lockup.')
    elif lockup_pct > 10:
        print('  ⚠ Mild congestion in some games. Worth flagging to beta testers.')
    else:
        print('  ✓ Mid-game lockup is not a significant issue in the current config.')

    # ── OVERALL ASSESSMENT vs BASELINE ───────────────────────────────────────
    section('OVERALL ASSESSMENT — 90/10 FRAMEWORK IMPACT')

    print('  Comparison: POST-FRAMEWORK vs PRE-FRAMEWORK (500 games each)')
    print()

    # Win rate change
    wr_change = a['fp_win_rate'] - B['fp_win_rate']
    print(f'  1. FIRST PLAYER ADVANTAGE')
    print(f'     Pre : {B["fp_win_rate"]*100:.1f}%   Post: {a["fp_win_rate"]*100:.1f}%   '
          f'Δ {wr_change*100:+.1f}%')
    if abs(wr_change) < 0.03:
        print('     → Essentially unchanged. The framework did not meaningfully shift')
        print('       structural first-player advantage.')
    elif wr_change > 0:
        print('     → First-player advantage increased. Cardinals may benefit P1 more')
        print('       by locking down territory P2 needs to catch up.')
    else:
        print('     → First-player advantage decreased. Territory denial may be helping')
        print('       the second player limit P1\'s scoring opportunities.')

    print()

    # Scoring change
    sc_change = (avg_p1 + avg_p2) - B['avg_combined']
    print(f'  2. SCORING LEVELS')
    print(f'     Pre combined avg : {B["avg_combined"]:.1f}   Post: {avg_p1+avg_p2:.1f}   '
          f'Δ {sc_change:+.1f} pts')
    if sc_change < -5:
        print('     → Combined scoring dropped noticeably. Cardinal walls are reducing')
        print('       total scoring — which is the intended effect of territory denial.')
    elif sc_change > 5:
        print('     → Combined scoring increased. Diagonal-heavy evaluation may be')
        print('       producing more completions faster.')
    else:
        print('     → Scoring levels essentially stable. The framework shifted strategic')
        print('       intent without dramatically changing total point output.')

    print()

    # Direction shift
    b_card_pct_val = b_card_pct
    card_shift = card_pct - b_card_pct_val
    print(f'  3. DIRECTION USAGE SHIFT')
    print(f'     Pre  cardinals: {b_card_pct_val:.1f}%   Post: {card_pct:.1f}%   '
          f'Δ {card_shift:+.1f}%')
    if card_shift > 3:
        print('     → AI is now meaningfully more likely to choose cardinal directions,')
        print('       confirming the territory denial bonus is influencing move selection.')
    elif card_shift < -3:
        print('     → AI is choosing fewer cardinals than baseline — diagonal scoring')
        print('       bonuses may be dominating over territory denial.')
    else:
        print('     → Direction split is similar to baseline. The framework tweaked')
        print('       weights but the underlying move pool hasn\'t shifted dramatically.')

    print()

    # Territory denial
    print(f'  4. TERRITORY DENIAL')
    print(f'     Avg corridors denied per cardinal move : {a["avg_denial_per_cardinal"]:.2f}')
    if a['avg_denial_per_cardinal'] > 5:
        print('     → Each cardinal placement blocks multiple opponent corridors on')
        print('       average — territory denial is a meaningful strategic pressure.')
    elif a['avg_denial_per_cardinal'] > 2:
        print('     → Cardinals block a moderate number of corridors per move.')
        print('       Territory denial is having some effect but could be stronger.')
    else:
        print('     → Cardinals are denying few corridors per move. The board geometry')
        print('       may limit how many corridors a single placement can block.')

    print()

    # Strategic lockup
    print(f'  5. STRATEGIC LOCKUP')
    print(f'     Avg lockup rounds per game : {a["avg_lockup_per_game"]:.2f}')
    if a['avg_lockup_per_game'] < 1.0:
        print('     → The framework has not introduced non-productive move patterns.')
        print('       The AI consistently finds meaningful moves throughout each game.')
    else:
        print(f'     → {a["avg_lockup_per_game"]:.2f} rounds per game on average where both players')
        print('       made non-meaningful moves. Investigate if this clusters in specific rounds.')

    print()

    # Single most impactful finding
    print(f'  6. MOST IMPACTFUL FINDING')
    # Determine the most notable change
    findings = []
    if abs(card_shift) > 3:
        findings.append(('direction_shift', abs(card_shift),
                         f'Cardinal usage shifted by {card_shift:+.1f}% — '
                         f'the framework is actively changing AI direction selection.'))
    if abs(sc_change) > 5:
        findings.append(('score', abs(sc_change),
                         f'Combined scoring changed by {sc_change:+.1f} pts — '
                         f'territory denial is {"compressing" if sc_change < 0 else "expanding"} '
                         f'total point output.'))
    if abs(wr_change) > 0.03:
        findings.append(('winrate', abs(wr_change) * 100,
                         f'First-player win rate shifted {wr_change*100:+.1f}% — '
                         f'the framework has structural balance implications.'))
    if a['avg_denial_per_cardinal'] > 5:
        findings.append(('denial', a['avg_denial_per_cardinal'],
                         f'Each cardinal move blocks {a["avg_denial_per_cardinal"]:.1f} opponent '
                         f'corridors on average — territory denial is geometrically meaningful.'))
    if findings:
        findings.sort(key=lambda x: -x[1])
        print(f'     {findings[0][2]}')
    else:
        print('     The framework produced subtle shifts across multiple dimensions')
        print('     rather than one dominant change. Scores, direction usage, and win')
        print('     rates all changed within ±5% of baseline — the AI is different')
        print('     in strategic intent while remaining similar in measurable outcomes.')

    print()
    print('  7. RECOMMENDED NEXT STEPS')
    issues = []
    if a['fp_win_rate'] > 0.60:
        issues.append('• First-player advantage remains significant (>60%). Add a '
                      'second-player compensation rule before beta.')
    if a['avg_denial_per_cardinal'] < 2:
        issues.append('• Low territory denial per cardinal move. Increase the x15 '
                      'territory denial weight or inspect _evaluate_territory_denial() coverage.')
    if abs(card_shift) < 2:
        issues.append('• Cardinal usage barely changed from baseline. The x15 denial '
                      'bonus may not be large enough to shift move selection significantly.')
    if a['avg_lockup_per_game'] > 3:
        issues.append('• High strategic lockup rate. Review weight calibration — AI '
                      'may be choosing moves that serve neither scoring nor blocking.')
    if not issues:
        issues.append('• Framework appears to be working as intended. Next step: run '
                      'human playtesting to validate whether the AI feels harder to beat.')
        issues.append('• Consider whether the diagonal complete_gain × 140 bonus is '
                      'dominant enough to make the AI reliably finish scoring lines '
                      'before building territory.')
    for line in issues:
        print(f'  {line}')

    print()
    print(WIDE)
    print('  End of report.')
    print(WIDE)
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    NUM_GAMES = 500
    print(f'Running {NUM_GAMES} AI vs AI games (90/10 Strategic Framework run)...')
    t0    = time.time()
    games = []

    for i in range(NUM_GAMES):
        games.append(run_game(i))
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            eta     = elapsed / (i + 1) * (NUM_GAMES - i - 1)
            print(f'  {i+1:3d}/{NUM_GAMES}  ({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)')

    total = time.time() - t0
    print(f'All {NUM_GAMES} games complete in {total:.1f}s.\n')

    stats = analyse(games)
    print_report(games, stats)


if __name__ == '__main__':
    main()
