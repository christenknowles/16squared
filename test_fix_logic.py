# -*- coding: utf-8 -*-
"""
Standalone test script for proposed AI fix logic in 16 Squared.
No Streamlit, no matplotlib required.
Tests Parts A through E as specified.
"""

import sys
import random
import numpy as np

# ---- Minimal engine stub (replicates only what is needed for the tests) ------

class SixteenSquaredEngine:
    def __init__(self):
        self.vectors = {
            'N':  (0, 1),  'S':  (0, -1), 'E':  (1, 0),  'W':  (-1, 0),
            'NE': (1, 1),  'NW': (-1, 1), 'SE': (1, -1), 'SW': (-1, -1),
        }

    def is_border(self, x, y):
        return x == 0 or x == 15 or y == 0 or y == 15

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


engine = SixteenSquaredEngine()

# ---- Helpers -----------------------------------------------------------------

def classify_lines(lines_for_player):
    """Returns (total_count, diag_count) for a list of scoring lines."""
    diag_count = 0
    for line in lines_for_player:
        dx = line[1][0] - line[0][0]
        dy = line[1][1] - line[0][1]
        is_diagonal = (dx != 0 and dy != 0)
        if is_diagonal:
            diag_count += 1
    return len(lines_for_player), diag_count


def empty_board():
    return np.zeros((16, 16), dtype=int)


PASS_STR = "PASS"
FAIL_STR = "FAIL"
results = []

def record(name, passed, detail=""):
    status = PASS_STR if passed else FAIL_STR
    results.append((name, status, detail))
    mark = "[PASS]" if passed else "[FAIL]"
    print("  %s %s" % (mark, name))
    if detail:
        print("         %s" % detail)


# ==============================================================================
# PART A -- Player line counting
# ==============================================================================
print("")
print("=== PART A: Player line counting ===")

# A1: Empty board returns 0 player lines
board = empty_board()
lines = engine.get_scoring_lines(board)
player_lines = lines[1]
total, diag = classify_lines(player_lines)
record("A1 empty board -> 0 player lines", total == 0, "total=%d" % total)

# A2: One complete horizontal player line (row y=0, x=0..15)
board = empty_board()
board[0, :] = 1   # fill the top border row entirely
lines = engine.get_scoring_lines(board)
player_lines = lines[1]
total, diag = classify_lines(player_lines)
record("A2 horizontal line -> 1 line detected",
       total == 1,
       "total=%d, diag=%d" % (total, diag))
record("A2 horizontal line -> not diagonal",
       diag == 0,
       "diag=%d (expected 0)" % diag)

# A3: One complete diagonal (0,0) to (15,15)
# board[y,x]=1 for y==x
board = empty_board()
for i in range(16):
    board[i, i] = 1
lines = engine.get_scoring_lines(board)
player_lines = lines[1]
total, diag = classify_lines(player_lines)
record("A3 NE diagonal (0,0)-(15,15) -> 1 line",
       total == 1,
       "total=%d" % total)
record("A3 NE diagonal detected as diagonal",
       diag == 1,
       "diag=%d (expected 1)" % diag)

if player_lines:
    line = player_lines[0]
    dx = line[1][0] - line[0][0]
    dy = line[1][1] - line[0][1]
    record("A3 dx!=0 and dy!=0 for NE diag",
           dx != 0 and dy != 0,
           "dx=%d, dy=%d" % (dx, dy))
else:
    record("A3 dx!=0 and dy!=0 for NE diag", False, "no line found to inspect")

# A4: One complete diagonal NW/SE axis -- (0,15) to (15,0)
# tokens at (x, 15-x) for x in 0..15
board = empty_board()
for i in range(16):
    board[15 - i, i] = 1   # board[y,x]: y=15-i, x=i
lines = engine.get_scoring_lines(board)
player_lines = lines[1]
total, diag = classify_lines(player_lines)
record("A4 NW/SE anti-diagonal -> 1 line",
       total == 1,
       "total=%d" % total)
record("A4 anti-diagonal detected as diagonal",
       diag == 1,
       "diag=%d (expected 1)" % diag)
if player_lines:
    line = player_lines[0]
    dx = line[1][0] - line[0][0]
    dy = line[1][1] - line[0][1]
    record("A4 dx!=0 and dy!=0 for NW/SE diag",
           dx != 0 and dy != 0,
           "dx=%d, dy=%d" % (dx, dy))
else:
    record("A4 dx!=0 and dy!=0 for NW/SE diag", False, "no line found")

# A5: Board with 3 complete player diagonal lines -> player_diag_count = 3
# Diag 1: (0,0)-(15,15)  main diagonal
# Diag 2: (0,15)-(15,0)  anti-diagonal
# Diag 3: (0,1) going NE -> ends at (14,15), 15 tokens; both endpoints are borders
board = empty_board()
for i in range(16):
    board[i, i] = 1          # Diag 1
for i in range(16):
    board[15 - i, i] = 1     # Diag 2
for k in range(15):
    board[1 + k, 0 + k] = 1  # Diag 3: (x=k, y=1+k) for k=0..14

lines = engine.get_scoring_lines(board)
player_lines = lines[1]
total, diag = classify_lines(player_lines)
record("A5 3 diagonal lines -> player_diag_count=3",
       diag == 3,
       "total=%d, diag=%d (expected diag=3)" % (total, diag))
if diag != 3:
    print("  [INFO] A5 detected lines:")
    for i, ln in enumerate(player_lines):
        dx2 = ln[1][0] - ln[0][0]
        dy2 = ln[1][1] - ln[0][1]
        print("         Line %d: start=%s end=%s dx=%d dy=%d is_diag=%s" % (
            i, ln[0], ln[-1], dx2, dy2, dx2 != 0 and dy2 != 0))

# A6: 2 diagonal + 1 horizontal -> player_diag_count=2, player_line_count=3
board = empty_board()
for i in range(16):
    board[i, i] = 1        # Diag 1: (0,0)-(15,15)
for i in range(16):
    board[15 - i, i] = 1   # Diag 2: (0,15)-(15,0)
board[0, :] = 1            # Horizontal: bottom border row (y=0, all x)

lines = engine.get_scoring_lines(board)
player_lines = lines[1]
total, diag = classify_lines(player_lines)
record("A6 2 diag + 1 horizontal -> total=3",
       total == 3,
       "total=%d (expected 3)" % total)
record("A6 2 diag + 1 horizontal -> diag=2",
       diag == 2,
       "diag=%d (expected 2)" % diag)

print("")
print("  [INFO] A6 line-by-line classification:")
for i, ln in enumerate(player_lines):
    dx2 = ln[1][0] - ln[0][0]
    dy2 = ln[1][1] - ln[0][1]
    is_diag = dx2 != 0 and dy2 != 0
    print("         Line %d: start=%s, end=%s, dx=%d, dy=%d, is_diag=%s" % (
        i, ln[0], ln[-1], dx2, dy2, is_diag))

# ==============================================================================
# PART B -- Heatmap multiplier tiers
# ==============================================================================
print("")
print("=== PART B: Heatmap multiplier tiers ===")

def get_heatmap_mult(player_diag_count, player_line_count):
    if player_diag_count >= 3:
        return 5.5
    elif player_diag_count >= 2:
        return 4.0
    elif player_line_count >= 2:
        return 3.0
    else:
        return 1.8

# B1: Tier table verification
tier_cases = [
    # (diag_count, line_count, expected_mult, label)
    (0, 0, 1.8, "diag=0, lines=0 -> 1.8"),
    (0, 1, 1.8, "diag=0, lines=1 -> 1.8"),
    (0, 2, 3.0, "diag=0, lines=2 -> 3.0"),
    (1, 0, 1.8, "diag=1, lines=0 -> 1.8"),
    (1, 1, 1.8, "diag=1, lines=1 -> 1.8"),
    (1, 2, 3.0, "diag=1, lines=2 -> 3.0"),
    (2, 0, 4.0, "diag=2, lines=0 -> 4.0"),
    (2, 2, 4.0, "diag=2, lines=2 -> 4.0 (diag takes priority)"),
    (3, 0, 5.5, "diag=3, lines=0 -> 5.5"),
    (3, 5, 5.5, "diag=3, lines=5 -> 5.5 (diag takes priority)"),
    (4, 2, 5.5, "diag=4, lines=2 -> 5.5"),
]

for diag, lines_count, expected, label in tier_cases:
    mult = get_heatmap_mult(diag, lines_count)
    record("B tier: %s" % label, mult == expected, "got %s" % mult)

# B2: Weight calculation at each multiplier
print("")
print("  [INFO] Weight calculations (5 cells x threat_map=12 each):")
n_cells = 5
threat_val = 12
for mult, expected in [(1.8, 108.0), (3.0, 180.0), (4.0, 240.0), (5.5, 330.0)]:
    result_val = n_cells * threat_val * mult
    ok = abs(result_val - expected) < 1e-9
    record("B weight %d x %d x %s = %s" % (n_cells, threat_val, mult, expected),
           ok,
           "computed=%s" % result_val)

# ==============================================================================
# PART C -- Diagonal direction bias sampling
# ==============================================================================
print("")
print("=== PART C: Diagonal direction bias ===")

DIAGONALS_LIST = ['NE', 'NW', 'SE', 'SW']
ALL_DIRECTIONS = ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']

def sample_direction(player_diag_count):
    if player_diag_count >= 2:
        if random.random() < 0.7:
            return random.choice(DIAGONALS_LIST)
        else:
            return random.choice(ALL_DIRECTIONS)
    else:
        return random.choice(ALL_DIRECTIONS)

random.seed(42)
N_SAMPLES = 10000

# C1: player_diag_count=2 -> ~85% diagonal expected
diag_count_c1 = sum(
    1 for _ in range(N_SAMPLES)
    if sample_direction(2) in DIAGONALS_LIST
)
diag_pct_c1 = diag_count_c1 / N_SAMPLES
# Expected: 70% * 100% diagonal + 30% * 50% diagonal = 70% + 15% = 85%
expected_diag_pct = 0.85
# Accept 73-97% tolerance for 10000 samples (as stated in the prompt's loose bound)
c1_ok = 0.73 <= diag_pct_c1 <= 0.97
record("C1 player_diag=2 -> diagonal 73-97% of samples (prompt bound)",
       c1_ok,
       "diagonal%%=%.4f (expected ~%.2f)" % (diag_pct_c1, expected_diag_pct))

# Tighter window: should be 82-88% given expected=85%
c1_tight = 0.82 <= diag_pct_c1 <= 0.88
record("C1 player_diag=2 -> diagonal 82-88%% (2-sigma around 85%%)",
       c1_tight,
       "diagonal%%=%.4f" % diag_pct_c1)

# C2: player_diag_count=0 -> uniform distribution (~12.5% per direction)
dir_counts = {d: 0 for d in ALL_DIRECTIONS}
for _ in range(N_SAMPLES):
    d = sample_direction(0)
    dir_counts[d] += 1

print("")
print("  [INFO] player_diag=0 direction distribution (expected ~12.5%% each):")
for d, cnt in dir_counts.items():
    pct = cnt / N_SAMPLES
    print("         %-3s: %.4f (%d)" % (d, pct, cnt))

max_pct = max(v / N_SAMPLES for v in dir_counts.values())
min_pct = min(v / N_SAMPLES for v in dir_counts.values())
diag_total_pct = sum(dir_counts[d] / N_SAMPLES for d in DIAGONALS_LIST)
card_total_pct = sum(dir_counts[d] / N_SAMPLES for d in ['N', 'S', 'E', 'W'])

record("C2 player_diag=0 -> all directions 10-16%% each",
       0.10 <= min_pct and max_pct <= 0.16,
       "min=%.4f, max=%.4f" % (min_pct, max_pct))
record("C2 player_diag=0 -> diagonals ~50%% total (4/8 directions)",
       0.45 <= diag_total_pct <= 0.55,
       "diag_total=%.4f" % diag_total_pct)
record("C2 player_diag=0 -> cardinals ~50%% total",
       0.45 <= card_total_pct <= 0.55,
       "card_total=%.4f" % card_total_pct)

# C3: Verify formula derivation
# P(diagonal | diag_count>=2) = 0.7*1.0 + 0.3*(4/8) = 0.7 + 0.15 = 0.85
expected_formula = 0.7 * 1.0 + 0.3 * (4.0 / 8.0)
record("C3 formula 0.7*1.0 + 0.3*0.5 = 0.85",
       abs(expected_formula - 0.85) < 1e-9,
       "formula=%.4f" % expected_formula)

# C4: Confirm sample is closer to 85% than to 73-77%
print("")
print("  [INFO] C4 NOTE: prompt says 73-77%%, formula predicts 85%%.")
print("         Measured: %.4f" % diag_pct_c1)
in_73_77 = 0.73 <= diag_pct_c1 <= 0.77
print("         73-77%% range: %s (expected NO -- 85%% is correct)" % ("YES" if in_73_77 else "NO"))
record("C4 sample is closer to 85%% than to 75%% (73-77%% midpoint)",
       abs(diag_pct_c1 - 0.85) < abs(diag_pct_c1 - 0.75),
       "dist_to_85=%.4f, dist_to_75=%.4f" % (
           abs(diag_pct_c1 - 0.85), abs(diag_pct_c1 - 0.75)))

# ==============================================================================
# PART D -- 3-gap urgency raised from 30 to 40
# ==============================================================================
print("")
print("=== PART D: 3-gap urgency raised from 30 to 40 ===")

# Proposed new urgency map
urgency_new = {1: 140, 2: 75, 3: 40, 4: 15}
# Original urgency map (from app.py)
urgency_old = {1: 140, 2: 75, 3: 30, 4: 15}

# D1: 12-token line with 3 gaps
total_len_d1 = 12
new_val_d1 = total_len_d1 * urgency_new[3]
old_val_d1 = total_len_d1 * urgency_old[3]
record("D1 12-token 3-gap: new=480, old=360",
       new_val_d1 == 480 and old_val_d1 == 360,
       "new=%d (expected 480), old=%d (expected 360)" % (new_val_d1, old_val_d1))

# D2: 10-token line with 3 gaps
total_len_d2 = 10
new_val_d2 = total_len_d2 * urgency_new[3]
old_val_d2 = total_len_d2 * urgency_old[3]
record("D2 10-token 3-gap: new=400, old=300",
       new_val_d2 == 400 and old_val_d2 == 300,
       "new=%d (expected 400), old=%d (expected 300)" % (new_val_d2, old_val_d2))

# D3: Other urgency levels unchanged
for gaps, expected in [(1, 140), (2, 75), (4, 15)]:
    same = urgency_new[gaps] == expected
    record("D3 urgency[%d] unchanged at %d" % (gaps, expected),
           same,
           "got %d" % urgency_new[gaps])

# D4: Confirm that gap=3 is the ONLY change
only_3_changed = all(
    urgency_new[g] == urgency_old[g] for g in [1, 2, 4]
) and urgency_new[3] != urgency_old[3]
record("D4 only gap=3 changed (1,2,4 are unchanged)",
       only_3_changed,
       "new[3]=%d, old[3]=%d" % (urgency_new[3], urgency_old[3]))

# ==============================================================================
# PART E -- Integration check on realistic board state
# ==============================================================================
print("")
print("=== PART E: Integration check ===")

board = empty_board()

# Place complete NE diagonal from (0,0) to (15,15): board[y,x]=1 for y==x
for i in range(16):
    board[i, i] = 1

# Place 8 tokens from (0,15) going toward (7,8):
# In board[y,x]: start at x=0,y=15, step dx=1,dy=-1 -> (x,y): (0,15),(1,14),...,(7,8)
for k in range(8):
    board[15 - k, 0 + k] = 1

# Scatter a few AI tokens in the interior (not on any player line)
board[5, 10] = 2
board[6, 11] = 2
board[9, 3]  = 2

lines_result = engine.get_scoring_lines(board)
player_lines_e = lines_result[1]
total_e, diag_e = classify_lines(player_lines_e)

print("")
print("  [INFO] E board state:")
print("         NE full diagonal (0,0)-(15,15): 16 tokens")
print("         SW partial: (0,15)-(7,8): 8 tokens -- does NOT reach far border (x=15,y=0)")
print("         AI tokens scattered at interior positions (no effect on scoring)")

record("E1 full NE diagonal detected as 1 line",
       total_e == 1,
       "total=%d (expected 1)" % total_e)
record("E2 full NE diagonal classified as diagonal",
       diag_e == 1,
       "diag=%d (expected 1)" % diag_e)
record("E3 partial 8-token SW line NOT counted (border-to-border required)",
       total_e == 1,
       "total=%d: confirms partial line excluded" % total_e)

if player_lines_e:
    ln = player_lines_e[0]
    dx2 = ln[1][0] - ln[0][0]
    dy2 = ln[1][1] - ln[0][1]
    is_diag = dx2 != 0 and dy2 != 0
    print("  [INFO] E detected line: start=%s, end=%s, len=%d, dx=%d, dy=%d, is_diag=%s" % (
        ln[0], ln[-1], len(ln), dx2, dy2, is_diag))
    record("E4 detected line is the full diagonal (16 tokens)",
           len(ln) == 16,
           "len=%d" % len(ln))

# E5: Now extend the partial line to make it border-to-border: (0,15)-(15,0)
board2 = board.copy()
for k in range(16):
    board2[15 - k, k] = 1   # fills (0,15) to (15,0) fully

lines2 = engine.get_scoring_lines(board2)
player_lines_e2 = lines2[1]
total_e2, diag_e2 = classify_lines(player_lines_e2)
record("E5 after completing anti-diagonal: 2 scoring lines found",
       total_e2 == 2,
       "total=%d (expected 2)" % total_e2)
record("E5 both scoring lines classified as diagonal",
       diag_e2 == 2,
       "diag=%d (expected 2)" % diag_e2)

# ==============================================================================
# SUMMARY
# ==============================================================================
print("")
print("=" * 60)
print("FINAL SUMMARY")
print("=" * 60)

total_tests = len(results)
passed_count = sum(1 for _, s, _ in results if s == PASS_STR)
failed_count = sum(1 for _, s, _ in results if s == FAIL_STR)

print("  Total tests : %d" % total_tests)
print("  Passed      : %d" % passed_count)
print("  Failed      : %d" % failed_count)
print("")

if failed_count > 0:
    print("FAILED TESTS:")
    for name, status, detail in results:
        if status == FAIL_STR:
            print("  [FAIL] %s" % name)
            if detail:
                print("         %s" % detail)
    print("")

print("ALL RESULTS:")
for name, status, detail in results:
    mark = "[PASS]" if status == PASS_STR else "[FAIL]"
    detail_str = " -- %s" % detail if detail else ""
    print("  %s %s%s" % (mark, name, detail_str))

sys.exit(0 if failed_count == 0 else 1)
