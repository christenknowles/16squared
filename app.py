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
    /* Inactive compass direction buttons (secondary type) — dark/gold to contrast
       with the active direction button which uses the primary green style. */
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background: rgba(44, 24, 16, 0.45) !important;
        color: #C4A265 !important;
        border: 1px solid rgba(196,162,101,0.5) !important;
        box-shadow: none !important;
    }
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(44, 24, 16, 0.65) !important;
        color: #F5ECD7 !important;
        border: 1px solid #C4A265 !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3) !important;
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

    .early-end-box {
        background: linear-gradient(160deg, #2C1810 0%, #4A2E10 100%);
        border: 2px solid #C4A265;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
        font-family: 'Crimson Pro', Georgia, serif;
        font-size: 0.92rem;
        color: #F5ECD7;
        line-height: 1.55;
        box-shadow: 0 3px 10px rgba(0,0,0,0.4);
    }
    .early-end-title {
        font-family: 'Playfair Display', serif;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #C4A265;
        margin-bottom: 6px;
    }
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
            return False, [], "Your starting square must be on the Border."
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
                return False, [], "That direction would Wall-Crawl along the border. Multi-token paths must enter the Internal Grid."

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
            return False, [], "Your path must cross into the Internal Grid. You cannot Wall-Crawl along the border."
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
                    # Viability check: scan the remaining cells ahead of this
                    # partial chain toward the far border. If any player token
                    # (value 1) is found, the line is permanently blocked and
                    # dead — do not credit partial_gain and stop investing in it.
                    # lx, ly is already the first cell past the end of the chain.
                    fx, fy = lx, ly
                    viable = False
                    while 0 <= fx < 16 and 0 <= fy < 16:
                        if board[fy, fx] == 1:
                            break  # player token permanently blocks the far border
                        if self.is_border(fx, fy):
                            viable = True
                            break
                        fx += dx
                        fy += dy
                    if viable:
                        partial_gain += len(line)

        return complete_gain, partial_gain

    def _evaluate_territory_denial(self, board, path):
        """Returns the number of unique player border-start corridors that newly
        placed tokens in `path` would physically block.

        A corridor is a straight line (any of the 8 directions) that:
          - starts at a player-reachable border cell (board value 0 or 1)
          - passes through at least one interior cell
          - ends at the far border
          - has no existing AI token already blocking it

        For each empty cell in path (new AI placement), we walk back along each
        direction to find a border start, then forward to the far border. If the
        corridor is valid and unblocked, it is added to a deduplication set.

        Only new placements (board[py,px]==0) contribute — bridging through
        existing AI tokens does not add new denials.

        Returns the count of unique denied corridors.
        """
        denied = set()
        for px, py in path:
            if board[py, px] != 0:
                continue  # only newly placed tokens block corridors
            for dx, dy in self.vectors.values():
                # Walk backward to find a border start cell for this corridor.
                # Use an explicit found flag — Python while-else fires on natural
                # loop exit (including when is_border() becomes True), which would
                # incorrectly skip valid corridors.
                bx, by = px - dx, py - dy
                found_start = False
                while 0 <= bx < 16 and 0 <= by < 16:
                    if self.is_border(bx, by):
                        found_start = True
                        break
                    if board[by, bx] == 2:  # AI token blocks this backward path
                        break
                    bx -= dx
                    by -= dy
                if not found_start:
                    continue  # walked off board or hit AI token — no valid start
                if board[by, bx] == 2:
                    continue  # AI token at start border — corridor already blocked
                if not self.is_legal_direction(bx, by, dx, dy):
                    continue

                # Walk forward from the new cell to find the far border.
                fx, fy = px + dx, py + dy
                found_end = False
                while 0 <= fx < 16 and 0 <= fy < 16:
                    if self.is_border(fx, fy):
                        found_end = True
                        break
                    if board[fy, fx] == 2:  # AI token blocks this forward path
                        break
                    fx += dx
                    fy += dy
                if not found_end:
                    continue  # walked off board or hit AI token — no valid end
                if board[fy, fx] == 2:
                    continue  # AI token at far border

                # Require at least one interior cell between the two borders.
                # Adjacent-border corridors (bx+dx==fx and by+dy==fy) are trivial.
                if bx + dx == fx and by + dy == fy:
                    continue

                # Deduplicate: same corridor walked from either end must match.
                # Sort endpoints and use abs(dx),abs(dy) so NE and SW give same id.
                ep = tuple(sorted([(bx, by), (fx, fy)]))
                corridor_id = (ep, (abs(dx), abs(dy)))
                denied.add(corridor_id)
        return len(denied)

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

        TWO-PASS ARCHITECTURE:
          Pass 1 (border-anchored): starts from every border cell containing a
            player token, walks inward. Catches chains where the player has
            already occupied the border entry point.
          Pass 2 (interior-anchored): starts from interior player tokens that
            are the back end of their chain in a given direction. Catches chains
            that have grown purely from the interior outward — where neither
            border endpoint yet contains a player token. Both passes use max()
            to write urgency values, so a cell detected by both passes keeps the
            higher value and is never double-counted.
        """
        blocking = np.zeros((16, 16))

        # ── Pass 1: border-anchored scan ─────────────────────────────────────
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
                    urgency = {1: 140, 2: 75, 3: 40, 4: 15}[len(empty_cells)]
                    block_val = total_len * urgency
                    for ex, ey in empty_cells:
                        blocking[ey, ex] = max(blocking[ey, ex], block_val)

        # ── Pass 2: interior-anchored scan ────────────────────────────────────
        # Pass 1 is blind to chains where neither border endpoint contains a
        # player token — the player built inward from the interior outward, so
        # the border cells at both ends are still empty or AI-occupied. These
        # chains are invisible to a border-start scan no matter how long they
        # grow, until the player finally steps onto a border square.
        #
        # This pass finds those chains by starting from interior player tokens
        # that are the "back end" of their chain in a given line direction — i.e.,
        # the cell one step behind them (in the negative direction) is NOT a
        # player token. This guarantees each chain is scanned exactly once per
        # axis, avoiding redundant work.
        #
        # Urgency tiers and max() deduplication are identical to Pass 1.
        # Cells already assigned a higher value by Pass 1 are not lowered.
        #
        # Four unique line axes cover all eight directions without duplication:
        #   (1,0) = horizontal   (0,1) = vertical
        #   (1,1) = diagonal /   (1,-1) = diagonal \
        UNIQUE_AXES = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for y in range(1, 15):   # interior rows only (border rows handled by Pass 1)
            for x in range(1, 15):  # interior cols only
                if board[y, x] != 1:
                    continue
                for dx, dy in UNIQUE_AXES:
                    # Only scan from this token if it is the back end of its chain
                    # in direction (dx, dy): the cell behind it must NOT be a player
                    # token. If it is, that earlier token will start this same scan
                    # and this token's scan would be a duplicate.
                    bx, by = x - dx, y - dy
                    if 0 <= bx < 16 and 0 <= by < 16 and board[by, bx] == 1:
                        continue

                    # Walk FORWARD (positive direction) collecting the rest of the
                    # chain and any empty cells until hitting an AI token or border.
                    player_fwd = 1   # starting token
                    empty_fwd  = []
                    reached_fwd = False
                    fx, fy = x + dx, y + dy
                    while 0 <= fx < 16 and 0 <= fy < 16:
                        if board[fy, fx] == 2:
                            break  # AI token blocks forward path
                        if board[fy, fx] == 1:
                            player_fwd += 1
                        else:
                            empty_fwd.append((fx, fy))
                        if self.is_border(fx, fy):
                            reached_fwd = True
                            break
                        fx += dx
                        fy += dy

                    if not reached_fwd:
                        continue  # forward path blocked by AI or walked off board

                    # Walk BACKWARD (negative direction) collecting empty cells
                    # until hitting an AI token or the far border.
                    # (No player tokens behind the chain start by definition above.)
                    player_bwd = 0   # starting token already in player_fwd
                    empty_bwd  = []
                    reached_bwd = False
                    rx, ry = x - dx, y - dy
                    while 0 <= rx < 16 and 0 <= ry < 16:
                        if board[ry, rx] == 2:
                            break  # AI token blocks backward path
                        if board[ry, rx] == 1:
                            player_bwd += 1  # shouldn't happen given chain-start check, but safe
                        else:
                            empty_bwd.append((rx, ry))
                        if self.is_border(rx, ry):
                            reached_bwd = True
                            break
                        rx -= dx
                        ry -= dy

                    if not reached_bwd:
                        continue  # backward path blocked by AI or walked off board

                    total_player = player_fwd + player_bwd
                    all_empty    = empty_fwd + empty_bwd
                    total_len    = total_player + len(all_empty)

                    if total_len < 3 or not (1 <= len(all_empty) <= 4):
                        continue

                    urgency   = {1: 140, 2: 75, 3: 40, 4: 15}[len(all_empty)]
                    block_val = total_len * urgency
                    for ex, ey in all_empty:
                        blocking[ey, ex] = max(blocking[ey, ex], block_val)

        return blocking

    def _assess_board_state(self, board, player_score, ai_score):
        """
        Unified board state assessment — the holistic layer of AI decision-making.

        The three aspects below must be assessed together to produce one strategic
        posture, not evaluated separately and summed. A human player sees the entire
        board as one picture; this method does the same, deriving one set of
        multipliers that shapes the entire move evaluation framework in get_ai_move().

        ASPECTS COMBINED INTO ONE POSTURE:
          1. Score differential (score_diff = ai_score - player_score):
             Am I ahead or behind, and by how much? Shifts the AI's risk/reward
             balance between completing its own lines vs disrupting the opponent.
          2. Board density (interior battlefield occupancy, 0.0–1.0):
             How full is the battlefield? A congested board favours bridging through
             existing tokens over starting new lines, regardless of round number.
          3. Combined overlay: score + density together determine the final posture.
             A congested board with the AI behind gets both sets of multipliers.
          4. Quadrant analysis: which 7×7 region does the player have the most tokens?
             Returned as active_quadrant for use by get_ai_move() sampling bias.

        POSTURE MULTIPLIERS compose ON TOP of the existing phase multipliers
        (diag_score_mult, denial_mult) inside get_ai_move(). They do not replace
        any calibrated values — they modulate them.

        BLOCKING MAP CALIBRATION CONSTRAINT:
          The _build_blocking_map() urgency tiers were calibrated against the base
          diagonal complete_gain multiplier of ×140. When complete_gain_mult rises,
          the effective multiplier becomes 140 × complete_gain_mult:
            behind (×1.3)  → effective ×182: 1-gap block (~1400) still near-mandatory
            crisis (×1.5)  → effective ×210: blocking_mult is also raised to ×1.5
                             so the blocking urgency scales in tandem, preserving the
                             relative urgency-vs-scoring calibration.
          INVARIANT: blocking_mult must always scale alongside complete_gain_mult in
          crisis posture so the blocking map urgency tiers remain competitive.

        ACTIVE QUADRANT:
          The 14×14 interior is divided into four 7×7 quadrants. The one with the
          most player tokens is flagged as active if it holds ≥1.3× the average
          count across all four quadrants. The 1.3× threshold prevents false
          positives on balanced boards — if all four quadrants are roughly equal,
          no quadrant is flagged and sampling stays fully random. When active,
          get_ai_move() routes 40% of its 600 samples through border cells adjacent
          to that quadrant, directing search budget toward the player's actual
          building zone without eliminating global exploration.
        """
        score_diff = ai_score - player_score
        # Interior battlefield only (14×14 cells), not the border ring.
        # Border occupancy is not contested space; only interior density matters.
        density = np.count_nonzero(board[1:15, 1:15]) / (14 * 14)

        complete_gain_mult = 1.0
        partial_gain_mult  = 1.0
        blocking_mult      = 1.0
        bridge_bonus_mult  = 1.0

        # ── Score-based posture ───────────────────────────────────────────────
        if score_diff <= -8:
            posture = "crisis"
            # Severely behind: must score AND disrupt simultaneously.
            # complete_gain_mult and blocking_mult are raised in tandem to
            # preserve the calibrated blocking-map urgency relationships
            # (see BLOCKING MAP CALIBRATION CONSTRAINT in docstring above).
            complete_gain_mult = 1.5
            blocking_mult      = 1.5
        elif score_diff <= -3:
            posture = "behind"
            # Moderately behind: prioritise completing lines over territory.
            complete_gain_mult = 1.3
        elif score_diff >= 3 and density < 0.50:
            posture = "ahead"
            # Ahead on an open board: protect lead by deprioritising speculative
            # partial lines. Do not apply this on a congested board — congestion
            # already forces conservative play via the density overlay below.
            partial_gain_mult = 0.7
        else:
            posture = "even"

        # ── Density overlay (applies on top of score-based posture) ──────────
        # A congested board requires bridging through existing tokens rather than
        # starting new lines, regardless of score differential.
        if density >= 0.50:
            bridge_bonus_mult *= 1.5
            partial_gain_mult *= 0.6  # stacks with any score-based adjustment

        # ── Quadrant analysis ─────────────────────────────────────────────────
        # Divide the 14×14 interior into four 7×7 quadrants and count player
        # tokens in each. The active quadrant is the one most above average —
        # requiring ≥1.3× average to avoid flagging on balanced boards.
        # board[row_slice, col_slice] where rows/cols 1–14 are the interior.
        quad_counts = {
            'bottom-left':  int(np.sum(board[1:8,  1:8]  == 1)),
            'bottom-right': int(np.sum(board[1:8,  8:15] == 1)),
            'top-left':     int(np.sum(board[8:15, 1:8]  == 1)),
            'top-right':    int(np.sum(board[8:15, 8:15] == 1)),
        }
        total_player_interior = sum(quad_counts.values())
        avg_quad = total_player_interior / 4.0
        active_quadrant = None
        active_quadrant_player_density = 0.0
        if avg_quad > 0:
            best_quad = max(quad_counts, key=quad_counts.get)
            if quad_counts[best_quad] >= avg_quad * 1.3:
                active_quadrant = best_quad
                active_quadrant_player_density = quad_counts[best_quad] / 49.0

        return {
            'score_diff':                    score_diff,
            'density':                       density,
            'posture':                       posture,
            'complete_gain_mult':            complete_gain_mult,
            'partial_gain_mult':             partial_gain_mult,
            'blocking_mult':                 blocking_mult,
            'bridge_bonus_mult':             bridge_bonus_mult,
            'active_quadrant':               active_quadrant,
            'active_quadrant_player_density': active_quadrant_player_density,
        }

    def get_ai_move(self, board, max_tokens, round_num, player_score=0, ai_score=0):
        best_move, best_weight = None, -float('inf')
        threat_map = np.zeros((16, 16))

        # ── Completed player scoring line analysis ─────────────────────────────
        # Count how many scoring lines the player has already completed, and how
        # many are diagonal. This is a direct pattern signal — it reads what the
        # player has proven they can do, not just the score differential (which
        # lags) or near-complete gap counts (which fire too late when full lines
        # are being built each round). Used below to amplify heatmap sampling
        # and weight contribution when the player is executing a diagonal strategy.
        _player_lines    = self.get_scoring_lines(board)[1]
        player_line_count = len(_player_lines)
        player_diag_count = sum(
            1 for line in _player_lines
            if len(line) >= 2
            and (line[1][0] - line[0][0]) != 0
            and (line[1][1] - line[0][1]) != 0
        )

        # ── Heatmap weight multiplier ──────────────────────────────────────────
        # Baseline 1.8: soft nudge that loses to almost any AI scoring move.
        # Diagonal threat response is now handled by the synergy bonus (see below)
        # rather than amplifying the heatmap multiplier per diagonal line count.
        _heatmap_mult = 1.8

        # ── Medium-range threat heatmap ────────────────────────────────────────
        # 150 random (border, direction) samples build a probabilistic heat map of
        # player-accessible corridors. Cells in many plausible player paths
        # accumulate threat weight, nudging the AI toward contested regions.
        # Threshold changed from > 3 to >= 3: a 3-token player path is already
        # near-complete and worth registering as a genuine threat.
        _ALL_DIRS  = list(self.vectors.keys())
        for _ in range(150):
            tx, ty = self.get_random_border_coord()
            td = random.choice(_ALL_DIRS)
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

        # ── Holistic Board State Assessment ────────────────────────────────────
        # Single unified evaluation of score differential, board density, and
        # strategic posture. Produces multipliers that shape the weight formula
        # below without replacing any existing calibrated values. Must be called
        # after blocking_map is built so the full board picture is available.
        bs = self._assess_board_state(board, player_score, ai_score)

        # ── Active-quadrant biased sampling ────────────────────────────────────
        # When the player is concentrated in one quadrant (active_quadrant is not
        # None), 40% of the 600 samples start from border cells adjacent to that
        # quadrant. This directs search budget toward the player's actual building
        # zone without eliminating global exploration (60% remain fully random).
        # Bias changes WHERE moves are sampled, not how they are scored — it
        # composes additively with all existing weight multipliers and does not
        # alter the scoring formula in any way.
        # Adjacent border cells: the two border edges that bound the active quadrant.
        # Only unoccupied cells (value == 0) are kept — occupied cells cannot be
        # valid starting squares and would just waste sample budget.
        _quad_border_candidates = {
            'bottom-left':  [(0, y) for y in range(0, 9)] + [(x, 0) for x in range(0, 9)],
            'bottom-right': [(15, y) for y in range(0, 9)] + [(x, 0) for x in range(7, 16)],
            'top-left':     [(0, y) for y in range(7, 16)] + [(x, 15) for x in range(0, 9)],
            'top-right':    [(15, y) for y in range(7, 16)] + [(x, 15) for x in range(7, 16)],
        }
        aq = bs['active_quadrant']
        if aq:
            biased_borders = [
                (x, y) for x, y in _quad_border_candidates[aq]
                if board[y, x] == 0
            ]
            use_bias = bool(biased_borders)
        else:
            biased_borders = []
            use_bias = False

        token_counts = self._get_token_counts(max_tokens, round_num)

        # ── 90/10 Strategic Framework ──────────────────────────────────────────
        # Diagonal lines (NE/NW/SE/SW) are 90% a SCORING tool.
        # Cardinal lines (N/S/E/W) are 90% a TERRITORY CONTROL tool.
        # Weights reflect this: diagonals prioritise completion bonuses;
        # cardinals prioritise blocking + territory denial with lighter scoring.
        CARDINALS = {'N', 'S', 'E', 'W'}

        # ── Two-Phase Opening Principle ────────────────────────────────────────
        # The opening (rounds 1–5) follows a deliberate two-phase strategy:
        #
        # PHASE 1 — Round 1 (max_tokens=15): Diagonal Anchor
        #   The AI strongly favours establishing one long diagonal line across
        #   the board. Diagonal scoring weights are boosted by ×1.3 to make a
        #   border-to-border diagonal the dominant opening move. This anchors
        #   the AI's scoring position from the very first turn and gives it a
        #   structural lead the opponent must respond to.
        #
        # PHASE 2 — Rounds 2–5 (max_tokens 14–11): Cardinal Wall Building
        #   Having planted a diagonal anchor, the AI shifts to building cardinal
        #   (N/S/E/W) walls. Territory denial weight is boosted by an additional
        #   ×1.5 (effective denial weight = ×22 × 1.5 = ×33) to make wide
        #   horizontal or vertical placements the preferred choice during these
        #   rounds. These walls compress the opponent's available diagonal
        #   corridors, protecting the anchor and limiting the opponent's scoring
        #   angles before they can establish their own long lines.
        #
        # PHASE 3 — Rounds 6+ (max_tokens ≤10): Standard Weights
        #   As the board fills the two-phase logic gives way to the standard
        #   90/10 direction-aware weights. The mid-game is evaluated on its
        #   merits: diagonals for scoring, cardinals for territory control,
        #   near-complete blocking maps for threat response.
        if max_tokens == 15:       # Round 1 — Diagonal Anchor phase
            diag_score_mult = 1.3
            denial_mult     = 1.0
        elif max_tokens >= 11:     # Rounds 2–5 — Cardinal Wall phase
            diag_score_mult = 1.0
            denial_mult     = 1.5
        else:                      # Rounds 6+ — Standard play
            diag_score_mult = 1.0
            denial_mult     = 1.0

        for _ in range(600):
            if use_bias and random.random() < 0.4:
                ax, ay = random.choice(biased_borders)
            else:
                ax, ay = self.get_random_border_coord()
            ad = random.choice(list(self.vectors.keys()))
            tc = random.choice(token_counts)
            ok, path, _ = self.simulate_path(board, 2, ax, ay, ad, tc)
            if ok and path:
                is_cardinal = ad in CARDINALS

                # Base: raw path length — longer placements are broadly better.
                weight = len(path)

                # +80 if the path ends on a border square. Necessary (but not
                # sufficient) condition for a scoring line; kept as a lightweight
                # directional nudge toward border-to-border moves.
                if self.is_border(path[-1][0], path[-1][1]):
                    weight += 80

                # +20 per AI token already on board that this path bridges through.
                # bridge_bonus_mult (from holistic assessment) rises on congested
                # boards where extending existing chains is worth more than starting
                # new lines from scratch.
                bridge_count = sum(1 for px, py in path if board[py, px] == 2)
                weight += bridge_count * 20 * bs['bridge_bonus_mult']

                # Heatmap threat blocking: sum threat values for all cells in this
                # path, scaled by _heatmap_mult. Baseline is 1.8 (soft nudge).
                # Escalates to 3.0–5.5 when the player has completed scoring lines,
                # making diagonal corridor disruption genuinely competitive with
                # the AI's own scoring when the player is executing a diagonal
                # strategy. See player_diag_count / _heatmap_mult above.
                weight += sum(threat_map[py, px] for px, py in path) * _heatmap_mult

                # Direct blocking bonus: pre-scaled values from _build_blocking_map.
                # blocking_mult (from holistic assessment) is raised in crisis posture
                # in tandem with complete_gain_mult, preserving the calibrated
                # urgency-vs-scoring relationships (see _assess_board_state docstring).
                # blocking_hit is stored raw (pre-mult) for synergy bonus evaluation.
                blocking_hit = sum(blocking_map[py, px] for px, py in path)
                weight += blocking_hit * bs['blocking_mult']

                # Late-game bridge bonus (rounds 10+): re-using existing AI tokens
                # is increasingly valuable as open board space fills up. +15 extra
                # per bridged token on top of the base +20 above. Also scaled by
                # bridge_bonus_mult to stay consistent with the holistic assessment.
                if round_num >= 10:
                    weight += bridge_count * 15 * bs['bridge_bonus_mult']

                complete_gain, partial_gain = self._evaluate_scoring(board, path)

                # territory_denial computed for ALL directions (cardinal and diagonal)
                # so the synergy bonus below can fire on any multi-purpose move.
                territory_denial = self._evaluate_territory_denial(board, path)

                if is_cardinal:
                    # ── Cardinal (N/S/E/W) — territory control primary ──────────
                    # Cardinals score at only 7-8% efficiency (vs 60%+ for diagonals)
                    # so their value is in denying corridors to the player, not scoring.
                    #
                    # complete_gain × 80 × complete_gain_mult: when behind, even rare
                    # cardinal completions should be weighted more heavily to close
                    # the score gap. complete_gain_mult from holistic assessment.
                    #
                    # partial_gain × 4 × partial_gain_mult: reduced when ahead or on
                    # congested board — half-built cardinal lines rarely complete and
                    # should not be chased. partial_gain_mult from holistic assessment.
                    #
                    # territory_denial × 22 × denial_mult: the primary signal for
                    # cardinals. denial_mult is the phase multiplier (unchanged).
                    weight += (complete_gain * 80  * bs['complete_gain_mult']
                             + partial_gain  * 4   * bs['partial_gain_mult']
                             + territory_denial * 22 * denial_mult)
                else:
                    # ── Diagonal (NE/NW/SE/SW) — scoring primary ───────────────
                    # Diagonals score at 60%+ efficiency and are the AI's primary
                    # way to accumulate points.
                    #
                    # complete_gain × 140 × diag_score_mult × complete_gain_mult:
                    # diag_score_mult is the phase multiplier (×1.3 in round 1).
                    # complete_gain_mult from holistic assessment shifts aggressiveness
                    # based on the score gap. Both compose independently.
                    #
                    # partial_gain × 10 × diag_score_mult × partial_gain_mult:
                    # partial_gain_mult reduces speculative diagonal building when
                    # ahead or congested, focusing resources on completable lines.
                    weight += (complete_gain * 140 * diag_score_mult * bs['complete_gain_mult']
                             + partial_gain  * 10  * diag_score_mult * bs['partial_gain_mult'])

                # ── Synergy bonus ─────────────────────────────────────────────────
                # Rewards moves that serve two or more strategic purposes at once:
                # scoring, blocking a near-complete threat, denying territory, or
                # bridging existing AI tokens.
                #
                # WHY FLAT 200: isolation tests showed a flat +200 per extra purpose
                # is well-calibrated against the existing weight formula. A quality-
                # scaled bonus would introduce calibration complexity without benefit
                # because the individual thresholds (blocking_hit > 200, denial >= 3,
                # bridge >= 2) already act as quality filters — only genuine signals
                # fire, so the marginal reward can safely be uniform.
                #
                # CROSSOVER POINT: a dual-purpose move (score + block) beats a pure
                # 12-token diagonal only when complete_gain >= ~8.5 tokens. This means
                # the bonus does not inflate weak multi-purpose moves — a 3-token
                # completion that happens to block is still worth less than a strong
                # pure-scoring move. Critical-tier blocks (blocking_hit > 500) lower
                # the crossover to ~7 tokens, correctly making them easier to prefer.
                #
                # FIRES ONLY when 2+ purposes are served simultaneously — a move that
                # does one thing well gets no bonus; synergy requires actual overlap.
                purposes_served = 0
                if complete_gain > 0:     purposes_served += 1
                if blocking_hit > 200:    purposes_served += 1
                if territory_denial >= 3: purposes_served += 1
                if bridge_count >= 2:     purposes_served += 1
                if purposes_served >= 2:
                    weight += 200 * (purposes_served - 1)

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

    def should_ai_pass(self, board, max_tokens, round_num, player_score=0, ai_score=0):
        # Only consider passing in the final two rounds (max_tokens ≤ 2).
        # With 3+ tokens there is almost always a worthwhile move available.
        if max_tokens > 2:
            return False
        best_move = self.get_ai_move(board, max_tokens, round_num, player_score, ai_score)
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


def _has_any_meaningful_move(board: np.ndarray, player: int, max_tokens: int) -> bool:
    """Return True if the given player has at least one meaningful move.

    A meaningful move is one that:
      - Reaches the far border directly (border-to-border path with the placed tokens),
      - Completes a border-to-border line via bridge completion (see below), OR
      - Covers a cell flagged by the near-complete threat scanner (meaningful block).

    BRIDGE COMPLETION FIX:
    simulate_path() stops when tokens_left reaches 0 and the next cell is empty —
    even if the only remaining cell is an empty far-border square. In that case
    path[-1] is the last own token before the border, not the border itself, so
    the direct is_border(path[-1]) check fails. After each simulate_path call we
    therefore extend from path[-1] through any consecutive own tokens in the same
    direction. If that extension reaches the far border and the full line has at
    least one interior cell, it qualifies as a meaningful scoring move.

    TOKEN SAMPLING FIX:
    A line completable only at a specific tc (e.g., exactly 3 tokens) would be
    found with probability 1/max_tokens per sample if tc were chosen randomly.
    Instead, all token counts 1..max_tokens are tried for every sampled
    (border, direction) pair — identical to the threat-heatmap approach in
    get_ai_move(). This guarantees that every completable tc value is evaluated
    for each starting position.

    Note: bridging alone (without reaching the far border) is intentionally excluded.
    On a congested board almost every valid path bridges an existing token, making
    that criterion trivially true and preventing early-end detection from firing.

    Sample count: 600 when max_tokens ≤ 4 (late rounds have fewer valid paths and
    a narrower token budget, so extra coverage reduces false impasse detection).
    400 otherwise.
    """
    if max_tokens <= 0:
        return False
    # Engine always evaluates from player-2 perspective; flip board for player 1.
    if player == 1:
        eff = np.where(board == 1, 2, np.where(board == 2, 1, 0)).astype(int)
    else:
        eff = board.copy()
    bmap = engine._build_blocking_map(eff)
    has_block_targets = bool(np.any(bmap > 0))

    # More samples in late rounds: smaller token budgets mean fewer valid paths
    # exist, so a larger sample is needed for reliable coverage.
    n_samples = 600 if max_tokens <= 4 else 400

    for _ in range(n_samples):
        ax, ay = engine.get_random_border_coord()
        ad = random.choice(list(engine.vectors.keys()))

        # Try every token count from 1 to max_tokens for this (start, direction).
        # This ensures the one specific tc that completes the line is always tested,
        # rather than hoping a single random tc value happens to match.
        for tc in range(1, max_tokens + 1):
            ok, path, _ = engine.simulate_path(eff, 2, ax, ay, ad, tc)
            if not ok or not path:
                continue

            # ── Direct far-border check ───────────────────────────────────────
            # Requires len >= 2: a tc=1 path is just [(start_border)]; is_border
            # would be trivially True there but it is not a scoring move.
            if len(path) >= 2 and engine.is_border(path[-1][0], path[-1][1]):
                return True

            # ── Bridge-completion check ───────────────────────────────────────
            # Extend from the last placed/bridged cell through any consecutive own
            # tokens in the same direction. If we reach a far-border cell via those
            # own tokens and the full line touches at least one interior cell, the
            # player can complete a scoring line with the available token budget.
            dx, dy = engine.vectors[ad]
            ex, ey = path[-1][0] + dx, path[-1][1] + dy
            # Interior was touched if any cell in the placed path is non-border.
            touches_interior = any(
                not engine.is_border(px, py) for px, py in path
            )
            while 0 <= ex < 16 and 0 <= ey < 16:
                if eff[ey, ex] == 2:  # own token — free bridge
                    if not engine.is_border(ex, ey):
                        touches_interior = True
                    elif touches_interior:
                        # Far border reached via own tokens; full line is valid.
                        return True
                    ex += dx
                    ey += dy
                else:
                    break  # empty cell or opponent — bridge chain ends here

            if has_block_targets and any(bmap[py, px] > 0 for px, py in path):
                return True

    return False


if 'board' not in st.session_state:
    st.session_state.board                = np.zeros((16, 16), dtype=int)
    st.session_state.turn                 = 0
    st.session_state.token_groups         = list(range(15, 0, -1))
    st.session_state.scores               = (0, 0)
    st.session_state.ai_message           = None
    st.session_state.new_cells            = []
    st.session_state.early_end_prompt     = False
    st.session_state.early_end_skip_until = 0
    st.session_state["x_start"]           = 1
    st.session_state["y_start"]           = 1
    st.session_state["direction"]         = "N"

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

    # Apply any pending widget reset BEFORE the widgets are instantiated.
    # Session state keys bound to widgets cannot be set after instantiation,
    # so the reset handler sets a flag and we action it here on the next rerun.
    if st.session_state.get("_reset_inputs"):
        st.session_state["x_start"]  = 1
        st.session_state["y_start"]  = 1
        st.session_state["direction"] = "N"
        del st.session_state["_reset_inputs"]

    sx = st.number_input("X Start (Horizontal)", 1, 16, disabled=not game_active, key="x_start")
    sy = st.number_input("Y Start (Vertical)",   1, 16, disabled=not game_active, key="y_start")
    sc = st.number_input(
        "Tokens to Place",
        min_value=0,
        max_value=current_tokens if game_active else 0,
        value=current_tokens if game_active else 0,
        disabled=not game_active
    )

    # ── Direction compass ──────────────────────────────────────────────
    # 3×3 grid of arrow buttons; "Direction" label sits in the center cell.
    # Clicking a button immediately sets st.session_state["direction"].
    _ARROW  = {'N':'↑','S':'↓','E':'→','W':'←','NE':'↗','NW':'↖','SE':'↘','SW':'↙'}
    _CROWS  = [['NW','N','NE'], ['W',None,'E'], ['SW','S','SE']]
    _dir_disabled = not game_active or sc == 0
    _cur_dir = st.session_state.get("direction", "N")
    for _crow in _CROWS:
        _ccols = st.columns(3, gap="small")
        for _ci, _d in enumerate(_crow):
            with _ccols[_ci]:
                if _d is None:
                    st.markdown(
                        '<div style="display:flex;align-items:center;justify-content:center;'
                        'height:100%;padding:4px 0;font-family:\'Crimson Pro\',serif;'
                        'font-size:0.875rem;color:#5C4A1E;font-weight:500;text-align:center;">'
                        'Direction</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    _btn_type = "primary" if _d == _cur_dir else "secondary"
                    if st.button(
                        f"{_ARROW[_d]} {_d}",
                        key=f"_cdir_{_d}",
                        type=_btn_type,
                        disabled=_dir_disabled,
                        use_container_width=True,
                    ):
                        st.session_state["direction"] = _d
                        st.rerun()
    sd = st.session_state.get("direction", "N")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if st.button("⚔ CONFIRM MOVE", type="primary", use_container_width=True, disabled=not game_active):
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
                # Compute scores after the player's move so the AI evaluates
                # the board holistically from the correct score differential.
                p_score, a_score = engine.calculate_scores(st.session_state.board)
                with st.spinner("The Game is thinking..."):
                    if engine.should_ai_pass(st.session_state.board, current_tokens, round_num, p_score, a_score):
                        st.session_state.ai_message = "The Game chose to pass this round."
                    else:
                        ai_move = engine.get_ai_move(
                            st.session_state.board, current_tokens, round_num, p_score, a_score
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

                # Early-end detection: from round 6 onward, outside skip window
                next_turn = st.session_state.turn + 1
                next_round = next_turn + 1
                next_tokens = st.session_state.token_groups[next_turn] if next_turn < 15 else 0
                if (round_num >= 6
                        and next_round > st.session_state.early_end_skip_until
                        and not st.session_state.early_end_prompt
                        and next_tokens > 0):
                    player_has_move = _has_any_meaningful_move(
                        st.session_state.board, 1, next_tokens
                    )
                    ai_has_move = _has_any_meaningful_move(
                        st.session_state.board, 2, next_tokens
                    )
                    if not player_has_move and not ai_has_move:
                        st.session_state.early_end_prompt = True

                st.session_state.scores    = engine.calculate_scores(st.session_state.board)
                st.session_state.new_cells = new_player_cells + ai_new_cells
                st.session_state.turn += 1
                st.rerun()
            else:
                st.error(reason or "Illegal move.")

    if st.button("↺ RESET GAME", type="primary", use_container_width=True):
        st.session_state.board                = np.zeros((16, 16), dtype=int)
        st.session_state.turn                 = 0
        st.session_state.token_groups         = list(range(15, 0, -1))
        st.session_state.scores               = (0, 0)
        st.session_state.ai_message           = None
        st.session_state.new_cells            = []
        st.session_state.early_end_prompt     = False
        st.session_state.early_end_skip_until = 0
        st.session_state["_reset_inputs"] = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── CENTER COLUMN ──────────────────────────────────────────────────
with col_center:
    # Early-end prompt
    if st.session_state.early_end_prompt and game_active:
        st.markdown(
            '<div class="early-end-box">'
            '<div class="early-end-title">Impasse Detected</div>'
            'It appears neither player has any moves that would score or block a scoring line. '
            'Would you like to end the game here?'
            '</div>',
            unsafe_allow_html=True
        )
        _ecol1, _ecol2 = st.columns(2)
        with _ecol1:
            if st.button("End Game Now", use_container_width=True):
                st.session_state.turn = 15
                st.session_state.early_end_prompt = False
                st.rerun()
        with _ecol2:
            if st.button("Keep Playing", use_container_width=True):
                st.session_state.early_end_skip_until = round_num + 2
                st.session_state.early_end_prompt = False
                st.rerun()

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
        elif r_s > b_s:
            st.markdown('<div class="gameover-banner gameover-lose">⚔ DEFEATED — The Game claims the Grid.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="gameover-banner gameover-tie">⚖ A DRAW — The Grid remains unclaimed.</div>', unsafe_allow_html=True)


# ── RIGHT COLUMN ──────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="side-box">', unsafe_allow_html=True)
    st.markdown('<div class="game-title" style="font-size:1.3rem;">OBJECTIVE</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Crimson Pro',serif;font-size:0.95rem;color:#2C1810;line-height:1.5;">
    Build scoring lines to outscore your opponent. A valid scoring line must be perfectly straight, connect two different
    <b>Border</b> edges, and pass through at least one square in the <b>Internal Grid</b>.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _body_style = "font-family:'Crimson Pro',serif;font-size:0.83rem;color:#2C1810;line-height:1.55;"

    with st.expander("The Grid", expanded=False):
        st.markdown(f"""<div style="{_body_style}">
        The board is a 16×16 grid divided into two zones. The <b>Border</b> is the outer ring of 60 squares —
        every move starts here and all scoring lines must start and end here. The <b>Internal Grid</b> is the
        central 14×14 area of 196 squares — no scoring line counts unless it passes through here.
        </div>""", unsafe_allow_html=True)

    with st.expander("Gameplay", expanded=False):
        st.markdown(f"""<div style="{_body_style}">
        The game consists of 15 rounds. Each round your token supply decreases by one — starting at 15 tokens
        in Round 1 down to 1 token in Round 15.
        </div>""", unsafe_allow_html=True)

    with st.expander("Placement Rules", expanded=False):
        st.markdown(f"""<ol style="{_body_style}padding-left:16px;margin:0;">
        <li><b>Deployment:</b> Start on an empty Border square. Tokens are placed in a straight line from that square inward toward the Internal Grid.</li>
        <li><b>Engagement:</b> Multi-token moves must enter the Internal Grid. No Wall-Crawling — a multi-token path cannot stay entirely on the Border.</li>
        <li><b>Obstacles:</b> Cannot pass through opponent tokens. Your path stops at the point of collision. Tokens placed before the collision remain on the grid.</li>
        <li><b>Bridges:</b> You may pass through your own existing tokens freely. This costs nothing from your supply, allowing you to extend a line far beyond what your current round would normally permit.</li>
        <li><b>Quantity:</b> Place any number of tokens up to the round maximum. Choosing to place fewer is a valid strategic decision. Unused tokens are permanently discarded.</li>
        <li><b>Passing:</b> If you so choose, set tokens to 0 to forfeit your turn for that round.</li>
        </ol>""", unsafe_allow_html=True)

    with st.expander("Scoring", expanded=False):
        st.markdown(f"""<div style="{_body_style}">
        A sequence of tokens qualifies as a Scoring Line only if it meets all three criteria: (1) it is a
        perfectly straight line, (2) it connects two different Border edges, and (3) it contains at least one
        token in the Internal Grid. Each valid line scores points equal to the total number of tokens in that
        line. A token that is part of two intersecting scoring lines counts for both lines. Minimum score per
        line: 3 points. Maximum score per line: 16 points.
        </div>""", unsafe_allow_html=True)

    with st.expander("Winning", expanded=False):
        st.markdown(f"""<div style="{_body_style}">
        The game concludes after Round 15, or earlier if both players agree that no meaningful moves remain.
        The player with the highest cumulative score is declared the <b>Master of the Grid</b>.
        </div>""", unsafe_allow_html=True)

    with st.expander("Tiebreaker", expanded=False):
        st.markdown(f"""<div style="{_body_style}">
        If scores are tied after 15 rounds, the player who completed the single highest-value scoring line
        wins. If still tied, the player who completed the most scoring lines wins.
        </div>""", unsafe_allow_html=True)
