import io
import streamlit as st
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as pe

st.set_page_config(page_title="16 Squared", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Crimson+Pro:wght@400;500;600&display=swap');

    .block-container { padding-top: 0.4rem; padding-bottom: 0rem; }
    html, body, [class*="css"] { font-family: 'Crimson Pro', Georgia, serif; }

    header { visibility: hidden; }
    footer { visibility: hidden; }

    .game-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.6rem;
        font-weight: 700;
        text-align: center;
        color: #2C1810;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin: 0 0 4px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.15);
    }
    .game-subtitle {
        font-family: 'Crimson Pro', Georgia, serif;
        font-size: 0.72rem;
        text-align: center;
        color: #7A5C3A;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .side-box {
        background: linear-gradient(160deg, #F5ECD7 0%, #EDD9B0 60%, #E5CC96 100%);
        padding: 14px;
        border-radius: 10px;
        border: 2px solid #C4A265;
        box-shadow: inset 0 1px 3px rgba(255,255,255,0.6), 0 3px 8px rgba(0,0,0,0.18);
        height: 100%;
    }
    .score-row { display: flex; gap: 8px; margin-bottom: 10px; }
    .score-card {
        flex: 1;
        padding: 8px 6px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.22);
    }
    .score-card.player {
        background: linear-gradient(135deg, #1B4F8A 0%, #2E6DB4 100%);
        border: 1px solid #4A8FD4;
    }
    .score-card.game {
        background: linear-gradient(135deg, #8B1A1A 0%, #C0392B 100%);
        border: 1px solid #E05A4A;
    }
    .score-label {
        font-family: 'Crimson Pro', serif;
        font-size: 0.62rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.82);
        margin-bottom: 1px;
    }
    .score-value {
        font-family: 'Playfair Display', serif;
        font-size: 1.7rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1;
    }
    .round-info {
        font-family: 'Crimson Pro', serif;
        font-size: 0.88rem;
        text-align: center;
        color: #4A2E10;
        margin: 6px 0;
        letter-spacing: 0.04em;
    }
    .divider {
        border: none;
        border-top: 1px solid #C4A265;
        margin: 8px 0;
    }
    .preview-note {
        font-family: 'Crimson Pro', serif;
        font-size: 0.75rem;
        color: #7A5C3A;
        text-align: center;
        font-style: italic;
        margin-top: 2px;
    }
    .stButton > button {
        font-family: 'Playfair Display', serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:first-child {
        background: linear-gradient(135deg, #2C5F2E 0%, #3A7D44 100%) !important;
        color: white !important;
        border: 1px solid #4A9D5A !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    .stButton > button:first-child:hover {
        background: linear-gradient(135deg, #3A7D44 0%, #4A9D5A 100%) !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.25) !important;
    }
    .stNumberInput input, .stSelectbox select {
        font-family: 'Crimson Pro', serif !important;
        background: rgba(255,255,255,0.55) !important;
        border: 1px solid #C4A265 !important;
        border-radius: 5px !important;
    }
    .gameover-banner {
        font-family: 'Playfair Display', serif;
        font-size: 1.3rem;
        font-weight: 700;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        letter-spacing: 0.08em;
        margin-top: 8px;
    }
    .gameover-win  { background: linear-gradient(135deg,#2C5F2E,#3A7D44); color:#fff; }
    .gameover-lose { background: linear-gradient(135deg,#8B1A1A,#C0392B); color:#fff; }
    .gameover-tie  { background: linear-gradient(135deg,#5C4A1E,#8B6914); color:#fff; }
</style>
""", unsafe_allow_html=True)


class SixteenSquaredEngine:
    def __init__(self):
        self.vectors = {
            'N': (0,1),'S': (0,-1),'E': (1,0),'W': (-1,0),
            'NE': (1,1),'NW': (-1,1),'SE': (1,-1),'SW': (-1,-1)
        }

    def is_border(self, x, y):
        return x == 0 or x == 15 or y == 0 or y == 15

    def is_legal_direction(self, sx, sy, dx, dy):
        if sy == 0  and dy <= 0: return False
        if sy == 15 and dy >= 0: return False
        if sx == 0  and dx <= 0: return False
        if sx == 15 and dx >= 0: return False
        return True

    def simulate_path(self, board, player, start_x, start_y, direction, count):
        sx, sy = start_x - 1, start_y - 1

        if count == 0:
            return True, [], None
        if not self.is_border(sx, sy):
            return False, [], "Your starting square must be on the Grey Border."
        if board[sy, sx] != 0:
            return False, [], "That border square is already occupied. Choose an empty one."
        if count == 1:
            return True, [(sx, sy)], None

        dx, dy = self.vectors[direction]
        if not self.is_legal_direction(sx, sy, dx, dy):
            off_board = (
                (sx == 0  and dx < 0) or (sx == 15 and dx > 0) or
                (sy == 0  and dy < 0) or (sy == 15 and dy > 0)
            )
            if off_board:
                return False, [], "That direction leads off the board. Choose a direction that moves into the battlefield."
            else:
                return False, [], "That direction would Wall-Crawl along the border. Multi-token paths must enter the White Battlefield."

        path, tokens_left, cx, cy = [], count, sx, sy
        has_touched_interior = False
        hit_opponent = False

        while 0 <= cx < 16 and 0 <= cy < 16:
            if board[cy, cx] != 0 and board[cy, cx] != player:
                hit_opponent = True
                break
            if not self.is_border(cx, cy):
                has_touched_interior = True
            if board[cy, cx] == 0:
                if tokens_left > 0:
                    path.append((cx, cy))
                    tokens_left -= 1
                else:
                    break
            else:
                path.append((cx, cy))
            if self.is_border(cx, cy) and (cx != sx or cy != sy):
                break
            cx, cy = cx + dx, cy + dy

        if hit_opponent:
            tokens_placed = sum(1 for px, py in path if board[py, px] == 0)
            if path:
                return True, path, f"Your path was blocked by an opponent's token. Only {tokens_placed} of your {count} tokens were placed."
            else:
                return False, [], "Your path is immediately blocked by an opponent's token. Choose a different starting position or direction."

        if len(path) > 1 and not has_touched_interior:
            return False, [], "Your path must cross into the White Battlefield. You cannot Wall-Crawl along the border."
        if not path:
            return False, [], "No valid path exists from that position in that direction."

        return True, path, None

    def _evaluate_scoring(self, board, path):
        """Returns (complete_gain, partial_gain) for placing path on board as player 2.
        complete_gain: points from new completed scoring lines created by this move.
        partial_gain: total length of new partial lines (interior-touching, not yet complete).
        """
        temp = board.copy()
        new_squares = [(px, py) for px, py in path if board[py, px] == 0]
        for px, py in path:
            temp[py, px] = 2

        complete_gain = 0
        partial_gain = 0
        seen = set()

        for nx, ny in new_squares:
            for dx, dy in self.vectors.values():
                # Walk back to find the start of this line
                cx, cy = nx, ny
                while 0 <= cx - dx < 16 and 0 <= cy - dy < 16 and temp[cy - dy, cx - dx] == 2:
                    cx -= dx
                    cy -= dy
                if not self.is_border(cx, cy):
                    continue
                # Collect the full consecutive line
                line, lx, ly = [], cx, cy
                while 0 <= lx < 16 and 0 <= ly < 16 and temp[ly, lx] == 2:
                    line.append((lx, ly))
                    lx += dx
                    ly += dy
                if len(line) < 2:
                    continue
                if not any(0 < lx2 < 15 and 0 < ly2 < 15 for lx2, ly2 in line):
                    continue
                lid = tuple(sorted(line))
                if lid in seen:
                    continue
                seen.add(lid)
                if len(line) >= 3 and self.is_border(line[-1][0], line[-1][1]):
                    complete_gain += len(line)
                else:
                    partial_gain += len(line)

        return complete_gain, partial_gain

    def _build_blocking_map(self, board):
        """
        Deterministically scan the board for player (1) token chains that are
        within 1–4 empty cells of completing a border-to-border scoring line.
        Returns a 16×16 array of pre-scaled blocking bonus values.

        Unlike the heatmap (which samples hypothetical future moves), this method
        reads actual board state — so it reliably catches lines that are already
        80–90% built. Urgency values are calibrated against the scoring weights
        in get_ai_move so that near-complete player threats compete correctly:
          1 gap  → ×140  blocks a 10-token threat at ~1540, beating a 10-token
                         AI completion (~1290) — near-mandatory block
          2 gaps → ×75   blocks a 12-token threat at ~1050, beating medium
                         scoring but losing to large AI completions
          3 gaps → ×30   soft hint, usually loses to any scoring move
          4 gaps → ×15   very low; AI notes it but almost always scores instead
        The far border cell is included in the gap count when empty because
        the player must fill it to complete the scoring line.
        """
        blocking = np.zeros((16, 16))

        for y in range(16):
            for x in range(16):
                if not (self.is_border(x, y) and board[y, x] == 1):
                    continue
                for dx, dy in self.vectors.values():
                    if not self.is_legal_direction(x, y, dx, dy):
                        continue

                    cx, cy = x, y
                    player_cells = 0
                    empty_cells  = []
                    has_interior = False
                    reached_far_border = False

                    while 0 <= cx < 16 and 0 <= cy < 16:
                        if board[cy, cx] == 2:
                            break  # AI token already blocks this line — skip
                        if not self.is_border(cx, cy):
                            has_interior = True
                        if board[cy, cx] == 1:
                            player_cells += 1
                        else:
                            empty_cells.append((cx, cy))
                        if self.is_border(cx, cy) and (cx != x or cy != y):
                            reached_far_border = True
                            break
                        cx += dx
                        cy += dy

                    if not reached_far_border or not has_interior:
                        continue
                    total_len = player_cells + len(empty_cells)
                    if total_len < 3 or not (1 <= len(empty_cells) <= 4):
                        continue  # skip complete lines (0 gaps) and distant lines (5+ gaps)

                    # Pre-scaled bonus = potential_line_score × urgency_multiplier.
                    # Urgency tiers calibrated against complete_gain × 120 scoring
                    # (see docstring above for derivation).
                    urgency = {1: 140, 2: 75, 3: 30, 4: 15}[len(empty_cells)]
                    block_val = total_len * urgency
                    for ex, ey in empty_cells:
                        blocking[ey, ex] = max(blocking[ey, ex], block_val)

        return blocking

    def get_ai_move(self, board, max_tokens, round_num):
        best_move, best_weight = None, -float('inf')
        threat_map = np.zeros((16, 16))

        # ── Medium-range threat heatmap ────────────────────────────────────────
        # 150 random (border, direction) samples build a probabilistic heat map of
        # player-accessible corridors. Cells in many plausible player paths
        # accumulate threat weight, nudging the AI toward contested regions.
        # Threshold changed from > 3 to >= 3: a 3-token player path is already
        # near-complete and worth registering as a genuine threat.
        for _ in range(150):
            tx, ty = self.get_random_border_coord()
            td = random.choice(list(self.vectors.keys()))
            for tc in range(1, max_tokens + 1):
                ok, t_path, _ = self.simulate_path(board, 1, tx, ty, td, tc)
                if ok and len(t_path) >= 3:
                    for px, py in t_path:
                        # +12 per cell per sample. Cells in many player paths
                        # compound, making high-traffic corridors visibly costly
                        # to leave uncontested.
                        threat_map[py, px] += 12

        # ── Near-complete threat scan ──────────────────────────────────────────
        # Deterministic — reads actual board state rather than sampling. Catches
        # lines the heatmap misses when the specific start cell was never sampled.
        blocking_map = self._build_blocking_map(board)

        token_counts = self._get_token_counts(max_tokens, round_num)

        for _ in range(600):
            ax, ay = self.get_random_border_coord()
            ad = random.choice(list(self.vectors.keys()))
            tc = random.choice(token_counts)
            ok, path, _ = self.simulate_path(board, 2, ax, ay, ad, tc)
            if ok and path:
                # Base: raw path length — longer placements are broadly better.
                weight = len(path)

                # +80 if the path ends on a border square. Necessary (but not
                # sufficient) condition for a scoring line; kept as a lightweight
                # directional nudge toward border-to-border moves.
                if self.is_border(path[-1][0], path[-1][1]):
                    weight += 80

                # +20 per AI token already on board that this path bridges through.
                # Rewards extending connected groups toward completion at zero extra
                # token cost — the AI actively nurtures its existing chains.
                weight += sum(20 for px, py in path if board[py, px] == 2)

                # Heatmap threat blocking: sum threat values for all cells in this
                # path, scaled by 1.8. Provides a soft nudge toward contesting
                # high-traffic corridors; not strong enough to override clear
                # scoring opportunities, but tips close decisions toward defence.
                weight += sum(threat_map[py, px] for px, py in path) * 1.8

                # Direct blocking bonus: pre-scaled values from _build_blocking_map.
                # A path covering a 1-gap player threat cell adds ~1300 — enough to
                # make blocking near-complete lines reliably competitive with most
                # offensive moves. The AI will never miss an obvious block.
                weight += sum(blocking_map[py, px] for px, py in path)

                # Late-game bridge bonus (rounds 10+): re-using existing AI tokens
                # is increasingly valuable as open board space fills up. +15 extra
                # per bridged token on top of the base +20 above.
                if round_num >= 10:
                    weight += sum(1 for px, py in path if board[py, px] == 2) * 15

                # ── Scoring evaluation — primary offensive objective ────────────
                # complete_gain × 120: the dominant signal. Completing a scoring
                # line (border-to-border, interior-touching, ≥3 tokens) is always
                # the top priority. A 5-token completion adds 600; a 10-token
                # completion adds 1200 — both well above any non-blocking move.
                #
                # partial_gain × 8: raised from 5. An intermediate AI actively
                # builds partial lines rather than ignoring half-built progress.
                # Enough to influence route selection without overriding completions.
                complete_gain, partial_gain = self._evaluate_scoring(board, path)
                weight += complete_gain * 120 + partial_gain * 8

                if weight > best_weight:
                    best_weight, best_move = weight, (ax, ay, ad, tc)

        return best_move

    def _get_token_counts(self, max_tokens, round_num):
        if max_tokens <= 2:
            return list(range(0, max_tokens + 1))
        if round_num <= 5:
            # Early game: assertive, high-volume opening.
            # [high×4, mid×1] = 80% chance of playing at maximum capacity.
            # The AI opens boldly, establishing strong cross-board lines from
            # round 1. Increased from [high×3, mid, 1] (60% max) to match
            # playtesting feedback: the opening should feel competitive, not timid.
            high = max(1, max_tokens)
            mid  = max(1, max_tokens // 2)
            return [high, high, high, high, mid]
        if round_num <= 10:
            # Mid game: balanced range. Board space is contested; the AI
            # evaluates all token counts equally and picks by weight.
            return list(range(1, max_tokens + 1))
        # Late game: include passing (0). With few tokens remaining a well-placed
        # pass avoids wasting the last moves on low-value placements.
        return list(range(0, max_tokens + 1))

    def should_ai_pass(self, board, max_tokens, round_num):
        # Only consider passing in the final two rounds (max_tokens ≤ 2).
        # With 3+ tokens there is almost always a worthwhile move available.
        if max_tokens > 2:
            return False
        best_move = self.get_ai_move(board, max_tokens, round_num)
        if best_move is None:
            return True
        _, path, _ = self.simulate_path(board, 2, best_move[0], best_move[1], best_move[2], best_move[3])
        if not path:
            return True
        # Pass only if the best available move does none of:
        #   (a) complete a scoring line (path ends on far border)
        #   (b) place a token directly adjacent to a player token (proximity block)
        #   (c) bridge through existing AI tokens (free positional extension)
        # This ensures the AI stays active when it matters and avoids burning
        # its last tokens on purely neutral moves.
        completes_line = self.is_border(path[-1][0], path[-1][1]) if path else False
        blocks_threat  = any(
            any(0 <= px + ddx < 16 and 0 <= py + ddy < 16 and board[py + ddy, px + ddx] == 1
                for ddx, ddy in self.vectors.values())
            for px, py in path if board[py, px] == 0
        )
        bridges        = any(board[py, px] == 2 for px, py in path)
        return not completes_line and not blocks_threat and not bridges

    def get_random_border_coord(self):
        border_squares = (
            [(x, 1)  for x in range(1, 17)] +
            [(x, 16) for x in range(1, 17)] +
            [(1, y)  for y in range(2, 16)] +
            [(16, y) for y in range(2, 16)]
        )
        coord = random.choice(border_squares)
        return coord[0], coord[1]

    def calculate_scores(self, board):
        s = {1: 0, 2: 0}
        for p in [1, 2]:
            lines = set()
            for y in range(16):
                for x in range(16):
                    if self.is_border(x, y) and board[y, x] == p:
                        for d in ['E', 'S', 'SE', 'SW']:
                            dx, dy = self.vectors[d]
                            l, cx, cy = [], x, y
                            while 0 <= cx < 16 and 0 <= cy < 16 and board[cy, cx] == p:
                                l.append((cx, cy)); cx += dx; cy += dy
                            if len(l) >= 3 and self.is_border(l[-1][0], l[-1][1]):
                                if any(0 < lx < 15 and 0 < ly < 15 for lx, ly in l):
                                    l_id = tuple(sorted(l))
                                    if l_id not in lines:
                                        lines.add(l_id); s[p] += len(l)
        return s[1], s[2]

    def get_scoring_lines(self, board):
        result = {1: [], 2: []}
        for p in [1, 2]:
            lines = set()
            for y in range(16):
                for x in range(16):
                    if self.is_border(x, y) and board[y, x] == p:
                        for d in ['E', 'S', 'SE', 'SW']:
                            dx, dy = self.vectors[d]
                            l, cx, cy = [], x, y
                            while 0 <= cx < 16 and 0 <= cy < 16 and board[cy, cx] == p:
                                l.append((cx, cy)); cx += dx; cy += dy
                            if len(l) >= 3 and self.is_border(l[-1][0], l[-1][1]):
                                if any(0 < lx < 15 and 0 < ly < 15 for lx, ly in l):
                                    l_id = tuple(sorted(l))
                                    if l_id not in lines:
                                        lines.add(l_id)
                                        result[p].append(l)
        return result


# ── COLOURS ────────────────────────────────────────────────────────
OAK_DARK    = "#8B5E3C"   # border zone
OAK_MID     = "#C49A6C"   # border squares
OAK_LIGHT   = "#F2DEB0"   # battlefield squares
OAK_GRAIN   = "#D4B483"   # subtle grain lines
FELT_CREAM  = "#FAF3E0"   # battlefield center
PLAYER_FILL = "#1B4F8A"   # deep navy blue — player
PLAYER_EDGE = "#4A8FD4"
GAME_FILL   = "#8B1A1A"   # deep burgundy red — the game
GAME_EDGE   = "#E05A4A"
PREVIEW_COL = "#3A7D44"   # forest green for preview ghost
HIGHLIGHT   = "#F4C842"   # gold for newly placed tokens
SCORE_LINE_P = "#4A8FD4"
SCORE_LINE_G = "#E05A4A"


@st.cache_data
def _board_bg_colors():
    """Precompute the 16×16 RGB color array for the board background. Cached once."""
    bg = np.full((16, 16, 3), [0xFA / 255, 0xF3 / 255, 0xE0 / 255], dtype=np.float32)
    oak = np.array([0xC4 / 255, 0x9A / 255, 0x6C / 255], dtype=np.float32)
    bg[0, :] = oak
    bg[15, :] = oak
    bg[:, 0] = oak
    bg[:, 15] = oak
    return bg


def draw_board(board, new_cells=None, game_over=False):
    fig, ax = plt.subplots(figsize=(5.6, 5.6), facecolor=OAK_DARK)
    ax.set_xlim(-0.5, 16.5)
    ax.set_ylim(-0.5, 16.5)
    ax.axis('off')
    fig.patch.set_facecolor(OAK_DARK)

    # Outer frame
    ax.add_patch(patches.FancyBboxPatch(
        (-0.4, -0.4), 16.8, 16.8,
        boxstyle="round,pad=0.1",
        facecolor=OAK_DARK, edgecolor="#5C3A1E", linewidth=3
    ))

    # Wood grain lines
    for i in range(0, 17, 2):
        ax.plot([i - 0.5, i + 0.2], [-0.5, 16.5],
                color=OAK_GRAIN, alpha=0.12, lw=0.5)

    # Board background: single pcolormesh call replaces 256 Rectangle patches
    edges = np.arange(17, dtype=float)
    ax.pcolormesh(edges, edges, _board_bg_colors(), zorder=1)

    # Grid lines — two vectorized calls each replace per-cell Rectangle edges
    # Interior battlefield: light cream, thin (matches original edgecolor="#E8D8B0", lw=0.4)
    ax.vlines(range(2, 15), ymin=1, ymax=15, colors='#E8D8B0', linewidths=0.4, zorder=2)
    ax.hlines(range(2, 15), xmin=1, xmax=15, colors='#E8D8B0', linewidths=0.4, zorder=2)
    # Border/interior boundary + within-border strips: warm brown (matches edgecolor="#A07840", lw=0.7)
    ax.vlines([1, 15], ymin=0, ymax=16, colors='#A07840', linewidths=0.7, zorder=2)
    ax.hlines([1, 15], xmin=0, xmax=16, colors='#A07840', linewidths=0.7, zorder=2)
    ax.vlines(range(2, 15), ymin=0, ymax=1,  colors='#A07840', linewidths=0.7, zorder=2)
    ax.vlines(range(2, 15), ymin=15, ymax=16, colors='#A07840', linewidths=0.7, zorder=2)
    ax.hlines(range(2, 15), xmin=0, xmax=1,  colors='#A07840', linewidths=0.7, zorder=2)
    ax.hlines(range(2, 15), xmin=15, xmax=16, colors='#A07840', linewidths=0.7, zorder=2)

    # Inner battlefield border highlight
    ax.add_patch(patches.Rectangle(
        (1, 1), 14, 14,
        facecolor='none', edgecolor=OAK_DARK, linewidth=2.2, zorder=2
    ))
    ax.add_patch(patches.Rectangle(
        (1, 1), 14, 14,
        facecolor='none', edgecolor="#C49A6C", linewidth=0.8, zorder=3
    ))

    # Scoring line highlights at game over
    if game_over:
        scoring = engine.get_scoring_lines(board)
        for line in scoring[1]:
            xs = [cx + 0.5 for cx, cy in line]
            ys = [cy + 0.5 for cx, cy in line]
            ax.plot(xs, ys, color=SCORE_LINE_P, lw=2.2, alpha=0.55,
                    zorder=5, solid_capstyle='round')
        for line in scoring[2]:
            xs = [cx + 0.5 for cx, cy in line]
            ys = [cy + 0.5 for cx, cy in line]
            ax.plot(xs, ys, color=SCORE_LINE_G, lw=2.2, alpha=0.55,
                    zorder=5, solid_capstyle='round')

    # Tokens: PatchCollection batches all patches per layer into one draw call
    r = 0.34
    new_set = set(map(tuple, new_cells)) if new_cells else set()

    for player, fill, edge_col, hi in (
        (1, PLAYER_FILL, PLAYER_EDGE, "#6BAED6"),
        (2, GAME_FILL,   GAME_EDGE,   "#F4836A"),
    ):
        pos = [(x + 0.5, y + 0.5) for y in range(16) for x in range(16) if board[y, x] == player]
        if not pos:
            continue

        ax.add_collection(PatchCollection(
            [patches.Circle((cx + 0.045, cy - 0.045), r) for cx, cy in pos],
            facecolors='#00000033', linewidths=0, zorder=5))
        ax.add_collection(PatchCollection(
            [patches.Circle((cx, cy), r) for cx, cy in pos],
            facecolors=fill, linewidths=0, zorder=6))
        ax.add_collection(PatchCollection(
            [patches.Circle((cx, cy), r) for cx, cy in pos],
            facecolors='none', edgecolors=edge_col, linewidths=1.1, zorder=7))
        ax.add_collection(PatchCollection(
            [patches.Circle((cx - 0.09, cy + 0.09), r * 0.38) for cx, cy in pos],
            facecolors=hi, alpha=0.38, linewidths=0, zorder=8))

    # New-token gold rings
    if new_set:
        new_pos = [(x + 0.5, y + 0.5) for x, y in new_set
                   if 0 <= x < 16 and 0 <= y < 16 and board[y, x] != 0]
        if new_pos:
            ax.add_collection(PatchCollection(
                [patches.Circle((cx, cy), r + 0.06) for cx, cy in new_pos],
                facecolors='none', edgecolors=HIGHLIGHT, linewidths=1.6, alpha=0.9, zorder=9))

    # Coordinate labels
    for i in range(16):
        ax.text(i + 0.5, -0.22, str(i + 1),
                fontsize=5.2, ha='center', va='center',
                color='#F2DEB0', weight='bold', zorder=10)
        ax.text(-0.22, i + 0.5, str(i + 1),
                fontsize=5.2, ha='center', va='center',
                color='#F2DEB0', weight='bold', zorder=10)

    plt.tight_layout(pad=0.3)
    return fig


@st.cache_data
def render_board_image(board_bytes: bytes, new_cells_tuple: tuple, game_over: bool) -> bytes:
    """Render the board to PNG bytes. Cached by board state so input changes are instant."""
    board = np.frombuffer(board_bytes, dtype=np.int64).reshape(16, 16)
    new_cells = [list(c) for c in new_cells_tuple] if new_cells_tuple else None
    fig = draw_board(board, new_cells=new_cells, game_over=game_over)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor=OAK_DARK, edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── SESSION STATE ──────────────────────────────────────────────────
@st.cache_resource
def _create_engine():
    return SixteenSquaredEngine()

engine = _create_engine()

if 'board' not in st.session_state:
    st.session_state.board        = np.zeros((16, 16), dtype=int)
    st.session_state.turn         = 0
    st.session_state.token_groups = list(range(15, 0, -1))
    st.session_state.scores       = (0, 0)
    st.session_state.ai_message   = None
    st.session_state.new_cells    = []

# ── LAYOUT ─────────────────────────────────────────────────────────
col_left, col_center, col_right = st.columns([1, 2.4, 1])

game_active    = st.session_state.turn < 15
current_tokens = st.session_state.token_groups[st.session_state.turn] if game_active else 0
round_num      = min(st.session_state.turn + 1, 15)

# ── LEFT COLUMN ────────────────────────────────────────────────────
with col_left:
    st.markdown('<div class="side-box">', unsafe_allow_html=True)
    st.markdown('<div class="game-title">16²</div>', unsafe_allow_html=True)
    st.markdown('<div class="game-subtitle">Build Your Path · Block Theirs</div>', unsafe_allow_html=True)

    b_s, r_s = st.session_state.scores
    st.markdown(f"""
    <div class="score-row">
        <div class="score-card player">
            <div class="score-label">Player</div>
            <div class="score-value">{b_s}</div>
        </div>
        <div class="score-card game">
            <div class="score-label">The Game</div>
            <div class="score-value">{r_s}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="round-info">Round <b>{round_num}</b> of 15 &nbsp;·&nbsp; <b>{current_tokens}</b> tokens available</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if st.session_state.ai_message:
        st.info(st.session_state.ai_message)
        st.session_state.ai_message = None

    sx = st.number_input("X Start (Horizontal)", 1, 16, 1, disabled=not game_active)
    sy = st.number_input("Y Start (Vertical)",   1, 16, 1, disabled=not game_active)
    sc = st.number_input(
        "Tokens to Place",
        min_value=0,
        max_value=current_tokens if game_active else 0,
        value=current_tokens if game_active else 0,
        disabled=not game_active
    )

    dir_labels = {
        'N':'North (Up)','S':'South (Down)','E':'East (Right)','W':'West (Left)',
        'NE':'North-East','NW':'North-West','SE':'South-East','SW':'South-West'
    }
    sd = st.selectbox(
        "Direction",
        options=list(engine.vectors.keys()),
        format_func=lambda x: dir_labels.get(x),
        disabled=(not game_active or sc == 0)
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if st.button("⚔ CONFIRM MOVE", use_container_width=True, disabled=not game_active):
        if sc > current_tokens:
            st.error(f"Only {current_tokens} tokens are allowed this round.")
        else:
            ok, path, reason = engine.simulate_path(
                st.session_state.board, 1, sx, sy, sd, sc
            )
            if ok:
                new_player_cells = [(px, py) for px, py in path
                                    if st.session_state.board[py, px] == 0]
                for px, py in path:
                    st.session_state.board[py, px] = 1

                if reason:
                    st.warning(reason)

                ai_new_cells = []
                with st.spinner("The Game is thinking..."):
                    if engine.should_ai_pass(st.session_state.board, current_tokens, round_num):
                        st.session_state.ai_message = "The Game chose to pass this round."
                    else:
                        ai_move = engine.get_ai_move(
                            st.session_state.board, current_tokens, round_num
                        )
                        if ai_move:
                            _, ai_path, _ = engine.simulate_path(
                                st.session_state.board, 2,
                                ai_move[0], ai_move[1], ai_move[2], ai_move[3]
                            )
                            ai_new_cells = [(px, py) for px, py in ai_path
                                            if st.session_state.board[py, px] == 0]
                            for px, py in ai_path:
                                st.session_state.board[py, px] = 2
                        else:
                            st.session_state.ai_message = "The Game found no valid move and was forced to pass."

                st.session_state.scores   = engine.calculate_scores(st.session_state.board)
                st.session_state.new_cells = new_player_cells + ai_new_cells
                st.session_state.turn += 1
                st.rerun()
            else:
                st.error(reason or "Illegal move.")

    if st.button("↺ RESET GAME", use_container_width=True):
        st.session_state.board        = np.zeros((16, 16), dtype=int)
        st.session_state.turn         = 0
        st.session_state.token_groups = list(range(15, 0, -1))
        st.session_state.scores       = (0, 0)
        st.session_state.ai_message   = None
        st.session_state.new_cells    = []
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── CENTER COLUMN ──────────────────────────────────────────────────
with col_center:
    board_img = render_board_image(
        st.session_state.board.tobytes(),
        tuple(tuple(c) for c in st.session_state.new_cells) if st.session_state.new_cells else (),
        not game_active
    )
    st.image(board_img, use_container_width=True)

    if not game_active:
        b_s, r_s = st.session_state.scores
        if b_s > r_s:
            st.markdown('<div class="gameover-banner gameover-win">🏆 VICTORY — You are Master of the Grid!</div>', unsafe_allow_html=True)
            st.balloons()
        elif r_s > b_s:
            st.markdown('<div class="gameover-banner gameover-lose">⚔ DEFEATED — The Game claims the Grid.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="gameover-banner gameover-tie">⚖ A DRAW — The Grid remains unclaimed.</div>', unsafe_allow_html=True)

    # Rules collapsible
    with st.expander("📜 Rules & Objective", expanded=False):
        st.markdown("""
        **Objective:** Forge straight scoring lines across the board — horizontally, vertically, or diagonally.
        A line must start and end on the **Oak Border** and pass through at least one **Parchment Battlefield** square.

        1. **Deployment:** Start on an empty Oak Border square. Tokens are placed in a straight line.
        2. **Engagement:** Multi-token moves must enter the Parchment Battlefield. No Wall-Crawling.
        3. **Obstacles:** You cannot pass through opponent tokens. Your path stops at collision.
        4. **Bridges:** Passing through your own tokens costs nothing from your supply.
        5. **Quantity:** Place any amount up to the round limit. Unused tokens are discarded.
        6. **Passing:** Set tokens to 0 to forfeit your turn.
        7. **Scoring:** Each valid scoring line earns points equal to its total token count (min 3, max 16).
        """)

# ── RIGHT COLUMN ──────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="side-box">', unsafe_allow_html=True)
    st.markdown('<div class="game-title" style="font-size:1.0rem;">OBJECTIVE</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Crimson Pro',serif;font-size:0.85rem;color:#2C1810;line-height:1.5;">
    Forge straight scoring lines across the board — <b>horizontally, vertically, or diagonally.</b>
    A line must start and end on the <b>Oak Border</b> and pass through at least one square in the <b>Parchment Battlefield</b>.
    </div>
    <hr class="divider">
    <div class="game-title" style="font-size:1.0rem;">THE RULES</div>
    <ol style="font-family:'Crimson Pro',serif;font-size:0.82rem;color:#2C1810;padding-left:18px;line-height:1.6;margin:0;">
        <li><b>Deployment:</b> Start on an empty <b>Oak Border</b> square. Tokens are placed in a straight line from that square inward.</li>
        <li><b>Engagement:</b> Multi-token moves must enter the <b>Parchment Battlefield</b>. No Wall-Crawling along the border.</li>
        <li><b>Obstacles:</b> Cannot pass through opponent tokens. Your path stops at the point of collision.</li>
        <li><b>Bridges:</b> Passing through your own tokens costs nothing from your supply.</li>
        <li><b>Quantity:</b> Place any amount up to the round limit. Unused tokens are discarded.</li>
        <li><b>Passing:</b> Set tokens to 0 to forfeit your turn for that round.</li>
        <li><b>Scoring:</b> Valid lines earn points equal to their total token count (min 3, max 16).</li>
    </ol>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
