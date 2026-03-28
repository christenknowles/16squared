import streamlit as st
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
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

    def get_ai_move(self, board, max_tokens, round_num):
        best_move, best_weight = None, -float('inf')
        threat_map = np.zeros((16, 16))

        for _ in range(150):
            tx, ty = self.get_random_border_coord()
            td = random.choice(list(self.vectors.keys()))
            for tc in range(1, max_tokens + 1):
                ok, t_path, _ = self.simulate_path(board, 1, tx, ty, td, tc)
                if ok and len(t_path) > 3:
                    for px, py in t_path:
                        threat_map[py, px] += 12

        token_counts = self._get_token_counts(max_tokens, round_num)

        for _ in range(600):
            ax, ay = self.get_random_border_coord()
            ad = random.choice(list(self.vectors.keys()))
            tc = random.choice(token_counts)
            ok, path, _ = self.simulate_path(board, 2, ax, ay, ad, tc)
            if ok and path:
                weight = len(path)
                if self.is_border(path[-1][0], path[-1][1]):
                    weight += 80
                weight += sum(20 for px, py in path if board[py, px] == 2)
                weight += sum(threat_map[py, px] for px, py in path) * 1.8
                if round_num >= 10:
                    weight += sum(1 for px, py in path if board[py, px] == 2) * 15
                if weight > best_weight:
                    best_weight, best_move = weight, (ax, ay, ad, tc)

        return best_move

    def _get_token_counts(self, max_tokens, round_num):
        if max_tokens <= 2:
            return list(range(0, max_tokens + 1))
        if round_num <= 5:
            high = max(1, max_tokens)
            mid  = max(1, max_tokens // 2)
            return [high, high, high, mid, 1]
        if round_num <= 10:
            return list(range(1, max_tokens + 1))
        return list(range(0, max_tokens + 1))

    def should_ai_pass(self, board, max_tokens, round_num):
        if max_tokens > 2:
            return False
        best_move = self.get_ai_move(board, max_tokens, round_num)
        if best_move is None:
            return True
        _, path, _ = self.simulate_path(board, 2, best_move[0], best_move[1], best_move[2], best_move[3])
        if not path:
            return True
        completes_line = self.is_border(path[-1][0], path[-1][1]) if path else False
        blocks_threat  = any(board[py, px] == 0 for px, py in path)
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


def draw_board(board, preview_cells=None, new_cells=None, game_over=False):
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

    # Draw grain lines for wood effect
    for i in range(0, 17, 2):
        ax.plot([i - 0.5, i + 0.2], [-0.5, 16.5],
                color=OAK_GRAIN, alpha=0.12, lw=0.5)

    # Border and battlefield squares
    for y in range(16):
        for x in range(16):
            is_b = engine.is_border(x, y)
            if is_b:
                face = OAK_MID
                edge = "#A07840"
                lw   = 0.7
            else:
                face = FELT_CREAM
                edge = "#E8D8B0"
                lw   = 0.4
            ax.add_patch(patches.Rectangle(
                (x, y), 1, 1,
                facecolor=face, edgecolor=edge, linewidth=lw, zorder=1
            ))

    # Inner battlefield border highlight
    ax.add_patch(patches.Rectangle(
        (1, 1), 14, 14,
        facecolor='none', edgecolor=OAK_DARK, linewidth=2.2, zorder=2
    ))
    ax.add_patch(patches.Rectangle(
        (1, 1), 14, 14,
        facecolor='none', edgecolor="#C49A6C", linewidth=0.8, zorder=3
    ))

    # Preview ghost tokens
    if preview_cells:
        for px, py in preview_cells:
            if board[py, px] == 0:
                circ = patches.Circle(
                    (px + 0.5, py + 0.5), 0.33,
                    color=PREVIEW_COL, alpha=0.38, zorder=4
                )
                ax.add_patch(circ)
                ax.add_patch(patches.Circle(
                    (px + 0.5, py + 0.5), 0.33,
                    facecolor='none', edgecolor=PREVIEW_COL,
                    linewidth=1.2, alpha=0.7, zorder=4
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

    # Tokens
    for y in range(16):
        for x in range(16):
            val = board[y, x]
            if val == 0:
                continue
            is_new   = new_cells and (x, y) in new_cells
            cx_      = x + 0.5
            cy_      = y + 0.5
            r        = 0.34

            if val == 1:
                fill = PLAYER_FILL
                edge = PLAYER_EDGE
                hi   = "#6BAED6"
            else:
                fill = GAME_FILL
                edge = GAME_EDGE
                hi   = "#F4836A"

            # Shadow
            ax.add_patch(patches.Circle(
                (cx_ + 0.045, cy_ - 0.045), r,
                color='#00000033', zorder=5
            ))
            # Token body
            ax.add_patch(patches.Circle(
                (cx_, cy_), r,
                color=fill, zorder=6
            ))
            # Highlight rim
            ax.add_patch(patches.Circle(
                (cx_, cy_), r,
                facecolor='none', edgecolor=edge,
                linewidth=1.1, zorder=7
            ))
            # Inner shine
            ax.add_patch(patches.Circle(
                (cx_ - 0.09, cy_ + 0.09), r * 0.38,
                color=hi, alpha=0.38, zorder=8
            ))
            # New token gold ring
            if is_new:
                ax.add_patch(patches.Circle(
                    (cx_, cy_), r + 0.06,
                    facecolor='none', edgecolor=HIGHLIGHT,
                    linewidth=1.6, alpha=0.9, zorder=9
                ))

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


# ── SESSION STATE ──────────────────────────────────────────────────
engine = SixteenSquaredEngine()

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
        disabled=(not game_active or sc <= 1)
    )

    preview_cells = []

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
    fig = draw_board(
        st.session_state.board,
        preview_cells=preview_cells if game_active else [],
        new_cells=st.session_state.new_cells if st.session_state.new_cells else None,
        game_over=not game_active
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

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
