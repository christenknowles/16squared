"""
Synergy bonus isolation tests.
Tests all thresholds, bonus amounts, and the territory_denial diagonal fix
without importing app.py (which is tightly coupled to Streamlit runtime).

Copies only the engine methods needed: is_border, is_legal_direction,
simulate_path, _evaluate_scoring, _evaluate_territory_denial, _build_blocking_map.

Run with: python test_synergy.py
"""

import numpy as np

# ── Inline minimal engine (exact code from app.py) ────────────────────────────

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
            return False, [], "Not on border."
        if board[sy, sx] != 0:
            return False, [], "Border square occupied."
        if count == 1:
            return True, [(sx, sy)], None
        dx, dy = self.vectors[direction]
        if not self.is_legal_direction(sx, sy, dx, dy):
            return False, [], "Illegal direction."
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
                return True, path, f"Blocked. {tokens_placed} placed."
            else:
                return False, [], "Immediately blocked."
        if len(path) > 1 and not has_touched_interior:
            return False, [], "Wall-crawl."
        if not path:
            return False, [], "No valid path."
        return True, path, None

    def _evaluate_scoring(self, board, path):
        temp = board.copy()
        new_squares = [(px, py) for px, py in path if board[py, px] == 0]
        for px, py in path:
            temp[py, px] = 2
        complete_gain = 0
        partial_gain = 0
        seen = set()
        for nx, ny in new_squares:
            for dx, dy in self.vectors.values():
                cx, cy = nx, ny
                while 0 <= cx - dx < 16 and 0 <= cy - dy < 16 and temp[cy - dy, cx - dx] == 2:
                    cx -= dx
                    cy -= dy
                if not self.is_border(cx, cy):
                    continue
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
                    fx, fy = lx, ly
                    viable = False
                    while 0 <= fx < 16 and 0 <= fy < 16:
                        if board[fy, fx] == 1:
                            break
                        if self.is_border(fx, fy):
                            viable = True
                            break
                        fx += dx
                        fy += dy
                    if viable:
                        partial_gain += len(line)
        return complete_gain, partial_gain

    def _evaluate_territory_denial(self, board, path):
        denied = set()
        for px, py in path:
            if board[py, px] != 0:
                continue
            for dx, dy in self.vectors.values():
                bx, by = px - dx, py - dy
                found_start = False
                while 0 <= bx < 16 and 0 <= by < 16:
                    if self.is_border(bx, by):
                        found_start = True
                        break
                    if board[by, bx] == 2:
                        break
                    bx -= dx
                    by -= dy
                if not found_start:
                    continue
                if board[by, bx] == 2:
                    continue
                if not self.is_legal_direction(bx, by, dx, dy):
                    continue
                fx, fy = px + dx, py + dy
                found_end = False
                while 0 <= fx < 16 and 0 <= fy < 16:
                    if self.is_border(fx, fy):
                        found_end = True
                        break
                    if board[fy, fx] == 2:
                        break
                    fx += dx
                    fy += dy
                if not found_end:
                    continue
                if board[fy, fx] == 2:
                    continue
                if bx + dx == fx and by + dy == fy:
                    continue
                ep = tuple(sorted([(bx, by), (fx, fy)]))
                corridor_id = (ep, (abs(dx), abs(dy)))
                denied.add(corridor_id)
        return len(denied)

    def _build_blocking_map(self, board):
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
                            break
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
                        continue
                    urgency = {1: 140, 2: 75, 3: 40, 4: 15}[len(empty_cells)]
                    block_val = total_len * urgency
                    for ex, ey in empty_cells:
                        blocking[ey, ex] = max(blocking[ey, ex], block_val)
        UNIQUE_AXES = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for y in range(1, 15):
            for x in range(1, 15):
                if board[y, x] != 1:
                    continue
                for dx, dy in UNIQUE_AXES:
                    bx, by = x - dx, y - dy
                    if 0 <= bx < 16 and 0 <= by < 16 and board[by, bx] == 1:
                        continue
                    player_fwd = 1
                    empty_fwd  = []
                    reached_fwd = False
                    fx, fy = x + dx, y + dy
                    while 0 <= fx < 16 and 0 <= fy < 16:
                        if board[fy, fx] == 2:
                            break
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
                        continue
                    player_bwd = 0
                    empty_bwd  = []
                    reached_bwd = False
                    rx, ry = x - dx, y - dy
                    while 0 <= rx < 16 and 0 <= ry < 16:
                        if board[ry, rx] == 2:
                            break
                        if board[ry, rx] == 1:
                            player_bwd += 1
                        else:
                            empty_bwd.append((rx, ry))
                        if self.is_border(rx, ry):
                            reached_bwd = True
                            break
                        rx -= dx
                        ry -= dy
                    if not reached_bwd:
                        continue
                    total_player = player_fwd + player_bwd
                    all_empty    = empty_fwd + empty_bwd
                    total_len    = total_player + len(all_empty)
                    if total_len < 3 or not (1 <= len(all_empty) <= 4):
                        continue
                    urgency   = {1: 140, 2: 75, 3: 30, 4: 15}[len(all_empty)]
                    block_val = total_len * urgency
                    for ex, ey in all_empty:
                        blocking[ey, ex] = max(blocking[ey, ex], block_val)
        return blocking


engine = SixteenSquaredEngine()


# ═════════════════════════════════════════════════════════════════════════════
# SYNERGY BONUS FUNCTION (exact proposed logic)
# ═════════════════════════════════════════════════════════════════════════════

def synergy_bonus(complete_gain, blocking_hit, territory_denial, bridge_count):
    """Returns (purposes_served, bonus) using the proposed thresholds."""
    purposes_served = 0
    if complete_gain > 0:       purposes_served += 1
    if blocking_hit > 200:      purposes_served += 1
    if territory_denial >= 3:   purposes_served += 1
    if bridge_count >= 2:       purposes_served += 1
    bonus = 200 * (purposes_served - 1) if purposes_served >= 2 else 0
    return purposes_served, bonus


# ═════════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═════════════════════════════════════════════════════════════════════════════

PASS = 0
FAIL = 0

def check(label, got, expected, note=""):
    global PASS, FAIL
    ok = (got == expected)
    PASS += ok
    FAIL += (not ok)
    mark = "✓" if ok else "✗"
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {mark} {label}")
    if not ok:
        print(f"         got={got!r}  expected={expected!r}")
    if note:
        print(f"         note: {note}")


# ─────────────────────────────────────────────────────────────────────────────
# Tests 1–8: Unit tests on synergy_bonus()
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "═"*60)
print("TESTS 1–8  — Synergy bonus unit tests")
print("═"*60)

print("\nTest 1 — Pure single purpose (complete only)")
ps, b = synergy_bonus(10, 0, 0, 0)
check("purposes_served == 1", ps, 1)
check("bonus == 0",           b,  0)

print("\nTest 2 — Dual purpose: scores AND blocks")
ps, b = synergy_bonus(8, 350, 0, 0)
check("purposes_served == 2", ps, 2)
check("bonus == 200",          b, 200)

print("\nTest 3 — Triple purpose: scores, blocks, denies")
ps, b = synergy_bonus(6, 250, 4, 0)
check("purposes_served == 3", ps, 3)
check("bonus == 400",          b, 400)

print("\nTest 4 — Quadruple purpose: all four")
ps, b = synergy_bonus(5, 300, 5, 3)
check("purposes_served == 4", ps, 4)
check("bonus == 600",          b, 600)

print("\nTest 5 — Boundary: blocking_hit=199 (just below threshold)")
ps, b = synergy_bonus(8, 199, 0, 0)
check("purposes_served == 1 (blocking does not fire)", ps, 1)
check("bonus == 0",                                    b,  0)

print("\nTest 6 — Boundary: territory_denial=2 (just below threshold)")
ps, b = synergy_bonus(8, 0, 2, 0)
check("purposes_served == 1 (denial does not fire)", ps, 1)
check("bonus == 0",                                   b,  0)

print("\nTest 7 — Bridge only, no scoring")
ps, b = synergy_bonus(0, 0, 0, 3)
check("purposes_served == 1", ps, 1)
check("bonus == 0",           b,  0)

print("\nTest 8 — Multi-purpose without scoring (blocks + denies + bridges)")
ps, b = synergy_bonus(0, 300, 4, 3)
check("purposes_served == 3", ps, 3)
check("bonus == 400",          b, 400)


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: territory_denial returns non-zero for diagonal paths
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "═"*60)
print("TEST 9  — territory_denial non-zero for diagonal paths")
print("═"*60)

# 9a: Populated board — player tokens along an interior diagonal
# Player chain along SE: (3,3),(4,4),(5,5),(6,6)
board9a = np.zeros((16, 16), dtype=int)
for x, y in [(3,3),(4,4),(5,5),(6,6)]:
    board9a[y, x] = 1

# AI diagonal path NE from border (2,0) heading into interior
# NE = dx=+1, dy=+1: (2,0),(3,1),(4,2),(5,3),(6,4),(7,5),(8,6),(9,7),(10,8),(11,9)...
path9a = []
px, py, dx, dy = 2, 0, 1, 1
for _ in range(14):
    if 0 <= px < 16 and 0 <= py < 16:
        path9a.append((px, py))
        if engine.is_border(px, py) and (px != 2 or py != 0):
            break
        px += dx
        py += dy

denial9a = engine._evaluate_territory_denial(board9a, path9a)
print(f"\n  Board 9a: player tokens at (3,3),(4,4),(5,5),(6,6)")
print(f"  NE path from (2,0): {path9a}")
print(f"  territory_denial = {denial9a}")
check("denial >= 1 on board with player tokens", denial9a >= 1, True,
      note=f"actual={denial9a}")

# 9b: Completely empty board — denial should still be non-zero
# (player-reachable corridors exist even with no tokens yet)
board9b = np.zeros((16, 16), dtype=int)
denial9b = engine._evaluate_territory_denial(board9b, path9a)
print(f"\n  Board 9b: empty board, same NE path")
print(f"  territory_denial = {denial9b}")
check("denial >= 1 on empty board (open corridors blocked)", denial9b >= 1, True,
      note=f"actual={denial9b}")

# 9c: Cardinal vs diagonal comparison on same empty board
# Build a cardinal E path of similar length
path9c_card = []
px, py, dx, dy = 0, 8, 1, 0
for _ in range(16):
    if 0 <= px < 16 and 0 <= py < 16:
        path9c_card.append((px, py))
        if engine.is_border(px, py) and (px != 0 or py != 8):
            break
        px += dx
        py += dy

denial9c_card = engine._evaluate_territory_denial(board9b, path9c_card)
denial9c_diag = engine._evaluate_territory_denial(board9b, path9a)
print(f"\n  Comparing cardinal E path vs NE diagonal path on empty board:")
print(f"  Cardinal E from (0,8): {path9c_card}")
print(f"  denial_cardinal = {denial9c_card}")
print(f"  denial_diagonal = {denial9c_diag}")
print(f"  (Cardinal lines block more corridors — they run across the full board width")
print(f"   and deny all 8 line directions for each new cell they occupy)")
check("cardinal denial > 0", denial9c_card > 0, True, note=f"actual={denial9c_card}")
check("diagonal denial > 0", denial9c_diag > 0, True, note=f"actual={denial9c_diag}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Calibration check
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "═"*60)
print("TEST 10  — Calibration: dual-purpose vs pure scoring")
print("═"*60)

# Weight formula components (from get_ai_move):
#   path_len + (80 if border) + bridge_count*20 + heatmap + blocking + scoring
# For this test heatmap = 0 and bridge = 0 to isolate the comparison.

# Pure scoring: 12-token diagonal completion
# path_len=12, border bonus=80, complete_gain=12 → 12*140=1680
pure_12 = 12 + 80 + 12 * 140
print(f"\n  Pure 12-token diagonal: {12} + 80 + 12×140 = {pure_12}")

# Dual purpose: 8-token completion + blocking_hit=350
# blocking_hit enters weight directly as sum(blocking_map[py,px])
dual_base  = 8 + 80
dual_score = 8 * 140
dual_block = 350
dual_bonus_val = 200
dual_total = dual_base + dual_score + dual_block + dual_bonus_val
print(f"  Dual-purpose 8-token + block=350 + bonus=200: "
      f"{dual_base} + {dual_score} + {dual_block} + {dual_bonus_val} = {dual_total}")

gap = pure_12 - dual_total
print(f"  Gap (pure12 - dual): {gap}")
check("dual-purpose is within 200 points of pure 12-token scoring",
      abs(gap) <= 200, True, note=f"gap={gap}")
check("dual-purpose does not beat pure-12 by more than 300",
      dual_total - pure_12 < 300, True, note=f"guard against overcorrection")

# Also test dual with blocking_hit=500 (a tier-1 urgency, near-mandatory block)
dual_block_500 = 8 + 80 + 8*140 + 500 + 200
print(f"\n  Dual-purpose 8-token + block=500 + bonus=200: "
      f"= {dual_block_500}")
print(f"  Vs pure 12-token: {pure_12}")
print(f"  With a critical threat (500 block), dual-purpose beats pure scoring: "
      f"{dual_block_500 > pure_12}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Crossover calculation
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "═"*60)
print("TEST 11  — Crossover point: when does dual-purpose beat pure-12?")
print("═"*60)

# dual_total(X) = X + 80 + X*140 + 300 + 200 = 141X + 580
# pure_12      = 12 + 80 + 12*140 = 1772
# dual >= pure: 141X + 580 >= 1772 → X >= (1772-580)/141

pure_12_val = 12 + 80 + 12 * 140
crossover_300 = (pure_12_val - 580) / 141.0
print(f"\n  Pure-12 weight: {pure_12_val}")
print(f"  Dual formula (blocking=300): 141X + 580")
print(f"  Crossover: X = ({pure_12_val} - 580) / 141 = {crossover_300:.2f}")
print(f"  → Dual-purpose beats pure-12 when complete_gain >= {crossover_300:.1f}")
print(f"    (i.e., a ~{int(crossover_300)+1}-token scoring move paired with a real block)")

crossover_500 = (pure_12_val - (80 + 500 + 200)) / 141.0
print(f"\n  With blocking=500 (tier-1 threat):")
print(f"  Crossover: X = ({pure_12_val} - {80+500+200}) / 141 = {crossover_500:.2f}")
print(f"  → Dual-purpose beats pure-12 when complete_gain >= {crossover_500:.1f}")
print(f"    (a ~{max(1,int(crossover_500)+1)}-token completion paired with a critical block)")

check("crossover (block=300) is >= 6.0 (bonus is not too dominant)",
      crossover_300 >= 6.0, True, note=f"actual={crossover_300:.2f}")
check("crossover (block=300) is <= 10.0 (dual-purpose can realistically win)",
      crossover_300 <= 10.0, True, note=f"actual={crossover_300:.2f}")
check("crossover (block=500) is >= 4.0 (critical-threat dual should win earlier)",
      crossover_500 >= 4.0, True, note=f"actual={crossover_500:.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# Q-tests: threshold sensitivity analysis
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "═"*60)
print("Q-TESTS  — Threshold sensitivity analysis")
print("═"*60)

print("\nQ1 — blocking_hit > 200 threshold: which urgency tiers fire it?")
print("  blocking_map value = total_len × urgency")
print("  Urgency tiers: 1-gap=140, 2-gap=75, 3-gap=40, 4-gap=15")
header = f"  {'Gaps':>5}  {'Urgency':>8}  {'len=3':>7}  {'len=6':>7}  {'len=9':>7}  {'len=12':>8}  {'len=16':>8}  {'Fires at len>=':>14}"
print(header)
for gaps, urgency in [(1,140),(2,75),(3,40),(4,15)]:
    vals = {l: l*urgency for l in [3,6,9,12,16]}
    min_fire = None
    for l in range(3, 17):
        if l * urgency > 200:
            min_fire = l
            break
    row = f"  {gaps:>5}  {urgency:>8}  "
    row += "  ".join(f"{vals[l]:>7}" for l in [3,6,9,12,16])
    row += f"  {min_fire if min_fire else 'never':>14}"
    print(row)

print(f"""
  Analysis:
  1-gap (urgency=140): minimum value 3×140=420  — ALWAYS fires (min line is 3 cells)
  2-gap (urgency=75):  minimum value 3×75=225   — fires for all valid lines (3+)
  3-gap (urgency=40):  fires at len>=6 (5×40=200 is AT threshold, 6×40=240 > 200)
  4-gap (urgency=15):  fires at len>=14 (13×15=195 doesn't fire, 14×15=210 fires)

  Conclusion on threshold=200:
  - 1-gap and 2-gap blocking always triggers synergy bonus — this is correct,
    those are genuine near-complete threats that warrant multi-purpose reward.
  - 3-gap fires only for longer chains (>=6 cells), filtering out trivial threats.
  - 4-gap fires only for very long chains (>=14 cells), which are near-impossible.
    Effectively the 4-gap tier contributes no synergy bonus in practice.
  VERDICT: threshold=200 is well-calibrated for 1-gap and 2-gap threats.
  For 3-gap, it acts as a minimum quality filter (short 3-gap chains don't fire).
""")

print("Q2 — Flat 200 vs scaled bonus:")
print("  Current: 200 × (purposes_served - 1)")
print(f"  purposes=2: +200   purposes=3: +400   purposes=4: +600")
print()
# Edge case: marginal dual — complete_gain=3 (minimum completion) + blocking_hit=201
ps_m, b_m = synergy_bonus(3, 201, 0, 0)
w_marginal = (3 + 80 + 3*140) + 201 + b_m
print(f"  Marginal dual (complete=3, block=201, bonus=200): weight = {w_marginal}")
print(f"  Pure-12 weight: {pure_12_val}")
print(f"  Marginal dual loses by {pure_12_val - w_marginal} — bonus not inflating weak moves")
print()
# Strong dual: complete=10, blocking=450
ps_s, b_s = synergy_bonus(10, 450, 0, 0)
w_strong = (10 + 80 + 10*140) + 450 + b_s
print(f"  Strong dual (complete=10, block=450, bonus=200): weight = {w_strong}")
print(f"  Pure-12 weight: {pure_12_val}")
print(f"  Strong dual {'beats' if w_strong > pure_12_val else 'loses to'} pure-12 by "
      f"{abs(w_strong - pure_12_val)}")
print(f"""
  Analysis of flat vs scaled:
  A quality-scaled bonus (e.g., 200 × sqrt(average_signal)) would be more
  theoretically correct but introduces calibration complexity. The flat 200
  avoids 'gaming' where a marginally-better-quality move gets disproportionate
  synergy credit. Given that the thresholds (>200, >=3, >=2) already act as
  quality filters, the flat amount is appropriate.
  VERDICT: flat 200 is suitable. No need to scale with quality.
""")

print("Q3 — complete_gain > 0 vs >= 3 threshold:")
# Find minimum complete_gain from _evaluate_scoring on a real board
board_q3 = np.zeros((16, 16), dtype=int)
# Build a 3-cell scoring line for player 2: border(0,8), interior(1,8)(2,8)...(14,8), border(15,8)
# But we want a COMPLETION: fill most, test the final placement
# Pre-place the full horizontal line except the last cell
for x in range(0, 15):  # (0,8) to (14,8)
    board_q3[8, x] = 2
# path = just the final cell (15,8)
path_q3 = [(15, 8)]
cg_q3, pg_q3 = engine._evaluate_scoring(board_q3, path_q3)
print(f"  Completing a 16-cell horizontal line with 1 new cell:")
print(f"  complete_gain = {cg_q3}  (expected=16, not 1)")
print(f"  Minimum possible complete_gain when firing: entire line length (3+)")

# Minimal scoring line test: 3-cell diagonal (border+1interior+border)
board_q3b = np.zeros((16, 16), dtype=int)
board_q3b[0, 0] = 2   # border (0,0)
board_q3b[1, 1] = 2   # interior (1,1)
# path places the final cell to complete to border (2,2)? — that's not a border
# For a real minimal diagonal: (0,15)→(1,14)→(2,13) but (2,13) is not border
# Shortest actual scoring diagonal: (0,15) SE to (15,0) = 16 cells
# Or a near-border diagonal: corner (0,0) → (1,1) → (2,0)? — (2,0) is border
# (0,0) is border, (1,1) is interior, (2,0) is border: 3 cells, valid
board_q3b = np.zeros((16, 16), dtype=int)
board_q3b[0, 0] = 2   # (0,0) border
board_q3b[1, 1] = 2   # (1,1) interior
path_q3b = [(2, 0)]   # (2,0) is border — completes the SE line
cg_q3b, pg_q3b = engine._evaluate_scoring(board_q3b, path_q3b)
print(f"\n  Minimal 3-cell SE diagonal completion via path [(2,0)]:")
print(f"  complete_gain = {cg_q3b}  (expected=3 or 0 if direction check fails)")
print(f"  partial_gain  = {pg_q3b}")

print(f"""
  Analysis:
  _evaluate_scoring() returns complete_gain = TOTAL LINE LENGTH, not token count.
  The minimum scoring line is 3 cells (2 border + 1 interior minimum).
  Therefore complete_gain > 0 always means complete_gain >= 3 when valid.
  A single-token completion (complete_gain=1) is structurally impossible —
  the line must include at least one interior cell and reach both borders.

  VERDICT: complete_gain > 0 is the correct threshold.
  There is no risk of a single-token (length=1) line triggering the bonus.
  Raising the threshold to >= 3 would have no practical effect but could
  theoretically filter out a 3-cell line completion — which IS a real scoring
  move and should legitimately trigger the synergy bonus.
  Keep threshold as complete_gain > 0.
""")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print("═"*60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("═"*60)
if FAIL == 0:
    print("\nAll tests passed. Synergy bonus logic and thresholds are verified.")
    print("Ready for implementation in app.py.")
else:
    print(f"\n{FAIL} test(s) failed — review output above before implementing.")
