import numpy as np
import random
import pickle
import multiprocessing as mp
import os

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
                grid[r, c] = val
                rows[r].add(val)
                cols[c].add(val)
                boxes[box_index(r, c)].add(val)

                if fill_cell(next_r, next_c):
                    return True

                grid[r, c] = 0
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

    def box_index(r, c):
        return (r // 3) * 3 + (c // 3)

    for r in range(9):
        for c in range(9):
            val = grid[r, c]
            if val != 0:
                rows[r].add(val)
                cols[c].add(val)
                boxes[box_index(r, c)].add(val)

    def backtrack(r=0, c=0):
        nonlocal count
        if r == 9:
            count += 1
            return
        if count >= limit:
            return

        next_r, next_c = (r, c + 1) if c < 8 else (r + 1, 0)

        if grid[r, c] != 0:
            backtrack(next_r, next_c)
        else:
            for val in range(1, 10):
                if val not in rows[r] and val not in cols[c] and val not in boxes[box_index(r, c)]:
                    grid[r, c] = val
                    rows[r].add(val)
                    cols[c].add(val)
                    boxes[box_index(r, c)].add(val)

                    backtrack(next_r, next_c)

                    grid[r, c] = 0
                    rows[r].remove(val)
                    cols[c].remove(val)
                    boxes[box_index(r, c)].remove(val)

    backtrack()
    return count


def make_puzzle_from_solution(solution, difficulty="medium"):
    puzzle = solution.copy()
    levels = {"easy": 36, "medium": 32, "hard": 28, "expert": 24}
    min_clues = levels.get(difficulty, 32)

    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)

    for r, c in positions:
        temp = puzzle[r, c]
        puzzle[r, c] = 0

        if solve_and_count(puzzle.copy(), limit=2) != 1:
            puzzle[r, c] = temp

        if np.count_nonzero(puzzle) <= min_clues:
            break

    return puzzle


# -----------------------------
# Worker function (ONE puzzle)
# -----------------------------

def generate_single_puzzle(difficulty):
    solution = generate_full_solution()
    puzzle = make_puzzle_from_solution(solution, difficulty)
    return puzzle, solution


# -----------------------------
# Multiprocessing driver
# -----------------------------

def precompute_puzzles(per_diff=100, filename="sudoku_puzzles.pkl"):
    difficulties = ["easy", "medium", "hard", "expert"]
    all_puzzles = {d: [] for d in difficulties}

    cpu_count = mp.cpu_count()
    print(f"Using {cpu_count} CPU cores")

    with mp.Pool(processes=cpu_count) as pool:
        for diff in difficulties:
            print(f"\nGenerating {per_diff} puzzles for {diff}...")

            jobs = [diff] * per_diff
            results = pool.map(generate_single_puzzle, jobs)

            all_puzzles[diff].extend(results)

    with open(filename, "wb") as f:
        pickle.dump(all_puzzles, f)

    print(f"\nSaved puzzles to {filename}")


# -----------------------------
# Entry point
# -----------------------------

if __name__ == "__main__":
    mp.freeze_support()  # Windows safety

    def run():
        number_making = input("Number of games to make per level: ")
        try:
            number_making = int(number_making)
        except ValueError:
            print("Please enter a valid integer.")
            return run()

        precompute_puzzles(per_diff=number_making)

    run()
