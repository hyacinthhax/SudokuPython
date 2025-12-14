import numpy as np
import random
import pickle

# -----------------------------
# Sudoku generator functions
# -----------------------------

def generate_full_solution():
    grid = np.zeros((9,9), dtype=int)
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]

    def box_index(r, c):
        return (r // 3) * 3 + (c // 3)

    def fill_cell(r=0, c=0):
        if r == 9:
            return True
        next_r, next_c = (r, c + 1) if c < 8 else (r + 1, 0)
        candidates = list(range(1, 10))
        random.shuffle(candidates)
        for val in candidates:
            if val not in rows[r] and val not in cols[c] and val not in boxes[box_index(r, c)]:
                grid[r,c] = val
                rows[r].add(val)
                cols[c].add(val)
                boxes[box_index(r, c)].add(val)
                if fill_cell(next_r, next_c):
                    return True
                grid[r,c] = 0
                rows[r].remove(val)
                cols[c].remove(val)
                boxes[box_index(r, c)].remove(val)
        return False

    fill_cell()
    return grid

def solve_and_count(grid, limit=2):
    count = 0
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]

    def box_index(r,c):
        return (r // 3) * 3 + (c // 3)

    for r in range(9):
        for c in range(9):
            val = grid[r,c]
            if val != 0:
                rows[r].add(val)
                cols[c].add(val)
                boxes[box_index(r,c)].add(val)

    def backtrack(r=0,c=0):
        nonlocal count
        if r == 9:
            count += 1
            return
        if count >= limit:
            return
        next_r, next_c = (r, c + 1) if c < 8 else (r + 1, 0)
        if grid[r,c] != 0:
            backtrack(next_r, next_c)
        else:
            for val in range(1,10):
                if val not in rows[r] and val not in cols[c] and val not in boxes[box_index(r,c)]:
                    grid[r,c] = val
                    rows[r].add(val)
                    cols[c].add(val)
                    boxes[box_index(r,c)].add(val)
                    backtrack(next_r, next_c)
                    grid[r,c] = 0
                    rows[r].remove(val)
                    cols[c].remove(val)
                    boxes[box_index(r,c)].remove(val)

    backtrack()
    return count

def make_puzzle_from_solution(solution, difficulty="medium"):
    puzzle = solution.copy()  # no deepcopy needed
    levels = {"easy":36,"medium":32,"hard":28,"expert":24}
    min_clues = levels.get(difficulty, 32)

    positions = [(r,c) for r in range(9) for c in range(9)]
    random.shuffle(positions)

    for r,c in positions:
        temp = puzzle[r,c]
        puzzle[r,c] = 0
        if solve_and_count(puzzle.copy(), limit=2) != 1:
            puzzle[r,c] = temp
        if np.count_nonzero(puzzle) <= min_clues:
            break
    return puzzle

# -----------------------------
# Precompute and save puzzles
# -----------------------------
def precompute_puzzles(per_diff=100, filename="sudoku_puzzles.pkl"):
    difficulties = ["easy","medium","hard","expert"]
    all_puzzles = {d:[] for d in difficulties}

    for diff in difficulties:
        print(f"Generating {per_diff} puzzles for {diff}...")
        for _ in range(per_diff):
            solution = generate_full_solution()
            puzzle = make_puzzle_from_solution(solution, diff)
            all_puzzles[diff].append((puzzle, solution))
    # Save to Pickle
    with open(filename, "wb") as f:
        pickle.dump(all_puzzles, f)
    print(f"Saved puzzles to {filename}")

# Run if script executed directly
if __name__ == "__main__":
    precompute_puzzles(per_diff=100)
