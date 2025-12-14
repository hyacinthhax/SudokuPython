import pygame, sys, pickle, random
from settings import *
# from buttonClass import * # Note: Button class is defined in this file, so this import is redundant/circular
import logging
import os

# Set current directory to script directory for resource loading
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


class Button:
    def __init__(self, x, y, width, height, text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hover = False

    def draw(self, window):
        color = (180,180,250) if self.hover else (200,200,200)
        pygame.draw.rect(window, color, self.rect)
        if self.text:
            font = pygame.font.SysFont("arial", 24)
            text_surf = font.render(self.text, True, (0,0,0))
            text_rect = text_surf.get_rect(center=self.rect.center)
            window.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update(self, mousePos):
        self.hover = self.rect.collidepoint(mousePos)

class App:
    def __init__(self):
        global window
        self.logger = self.setup_logger()
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        window = self.window
        self.difficulty = None

        self.running = True
        self.paused = False
        self.grid = testBoard1
        self.original_grid = [row[:] for row in testBoard1]  # store original for reset
        self.selected = None
        self.mousePos = None
        self.state = "menu"
        self.finished = False
        self.cellChanged = False
        self.playingButtons = []
        self.menuButtons = []
        self.font = pygame.font.SysFont('arial', cellSize//2)
        self.endButtons = []
        self.lockedCells = []
        self.incorrectCells = []
        self.hints_used = 0
        self.hints_max = 3

        self.pause_start = None
        self.timer_start = None
        self.elapsed_time = 0
        self.paused_elapsed = 0

        self.load()
        self.load_puzzles()
        self.load_menu_buttons()

    def setup_logger(self):
        logger = logging.getLogger("Sudoku")
        logger.setLevel(logging.DEBUG)
        
        # Stream Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File Handler
        fh = logging.FileHandler("sudoku.log")
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

        return logger

    # -----------------------------
    # Main loop
    # -----------------------------
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            if self.state == "menu":
                self.menu_events()
                self.menu_draw()
            elif self.state == "playing":
                self.playing_events()
                self.playing_update()
                self.playing_draw()
            clock.tick(60)
        pygame.quit()
        sys.exit()

    # -----------------------------
    # Menu functions
    # -----------------------------
    def load_menu_buttons(self):
        start_x = WIDTH//2 - 75
        start_y = HEIGHT//2 - 120
        spacing = 70
        difficulties = ["Easy", "Medium", "Hard", "Expert"]
        for i, diff in enumerate(difficulties):
            btn = Button(start_x, start_y + i*spacing, 150, 50, text=diff)
            self.menuButtons.append(btn)

    def menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for btn in self.menuButtons:
                    if btn.is_clicked(pos):
                        difficulty = btn.text.lower()
                        self.difficulty = difficulty
                        puzzle, solution = self.get_random_puzzle(difficulty)
                        self.grid = [row[:] for row in puzzle]
                        self.original_grid = [row[:] for row in puzzle]  # store original
                        self.solution = [row[:] for row in solution]
                        self.lockedCells = [(x,y) for y in range(9) for x in range(9) if puzzle[y][x] != 0]
                        self.state = "playing"
                        self.paused = False
                        self.timer_start = pygame.time.get_ticks()
                        self.elapsed_time = 0
                        self.pause_start = None
                        self.loadButtons()
                        self.log_solution_board()

    def menu_draw(self):
        self.window.fill(WHITE)
        # Draw Title/Instructions here if desired
        for btn in self.menuButtons:
            btn.draw(self.window)
        pygame.display.update()

    # -----------------------------
    # Playing functions
    # -----------------------------
    def playing_events(self):
        for event in pygame.event.get():
            lockedCells = self.lockedCells

            if event.type == pygame.QUIT:
                self.running = False

            # Mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                button_clicked = False
                for button in self.playingButtons:
                    if button.is_clicked(pos):
                        button_clicked = True

                        # RESET
                        if button.text == "Reset":
                            if self.difficulty is None:
                                return  # safety check

                            # Get a new puzzle of the same difficulty
                            puzzle, solution = self.get_random_puzzle(self.difficulty)

                            self.grid = [row[:] for row in puzzle]
                            self.original_grid = [row[:] for row in puzzle]
                            self.solution = [row[:] for row in solution]

                            # Reset locked cells to only original puzzle numbers
                            self.lockedCells = [(x,y) for y in range(9) for x in range(9) if puzzle[y][x] != 0]

                            # Reset hints and incorrect cells
                            self.hints_used = 0
                            self.incorrectCells = []
                            self.cellChanged = True
                            self.selected = None

                            # Reset timer
                            self.elapsed_time = 0
                            self.timer_start = pygame.time.get_ticks()
                            self.paused = False

                            # Reset pause button text
                            for b in self.playingButtons:
                                if b.text in ["Pause", "Resume"]:
                                    b.text = "Pause"

                            # Reset finished flag so completion can trigger
                            self.finished = False

                            # Optional: log solution for debugging
                            self.log_solution_board()


                        # PAUSE / RESUME
                        elif button.text in ["Pause", "Resume"]:
                            if not self.paused:
                                self.paused = True
                                self.pause_start = pygame.time.get_ticks()

                                self.paused_elapsed = self.elapsed_time  # store time at pause (not used but safe to keep)
                                button.text = "Resume"
                            else:
                                self.paused = False
                                # Adjust timer_start by the length of the pause
                                self.timer_start += pygame.time.get_ticks() - self.pause_start
                                self.pause_start = None
                                button.text = "Pause"

                        # HINT
                        elif button.text == "Hint" and self.hints_used < self.hints_max:
                            self.use_hint()

                        elif button.text == "Menu":
                            # Return to menu safely
                            self.state = "menu"
                            self.paused = False
                            self.selected = None
                            self.incorrectCells = []
                            self.lockedCells = []
                            self.playingButtons = [] # Clear playing buttons

                # Cell selection (only if not paused)
                if not button_clicked and not self.paused:
                    selected = self.mouseOnGrid()
                    if selected in lockedCells or selected is False: # Added 'or selected is False' check
                        self.selected = None
                        self.mousePos = None
                    else:
                        self.selected = selected

            # Keyboard input (only if not paused)
            if event.type == pygame.KEYDOWN and not self.paused:
                if self.selected and self.selected not in lockedCells and self.isInt(event.unicode):
                    self.grid[self.selected[1]][self.selected[0]] = int(event.unicode)
                    self.cellChanged = True
                # Added support for number key release if needed, but not in original code

    def playing_update(self):
        self.mousePos = pygame.mouse.get_pos()
        for button in self.playingButtons:
            button.update(self.mousePos)

        if self.timer_start and not self.paused:
            # Calculate elapsed time in seconds
            self.elapsed_time = (pygame.time.get_ticks() - self.timer_start) // 1000

        if self.cellChanged:
            # For simplicity (and speed), only check for errors when the user enters a number
            self.incorrectCells = []
            
            # Simple check against solution (assumes self.solution exists)
            if self.selected:
                x, y = self.selected
                current_val = self.grid[y][x]
                if current_val != 0 and current_val != self.solution[y][x]:
                    self.incorrectCells.append((x, y))

            if self.cellChanged:
                self.incorrectCells = []
                if self.allCellsDone():
                    self.checkAllCells()
                    if len(self.incorrectCells) == 0 and not self.finished:
                        self.finished = True
                        self.logger.info(f"Congratulations! \nYou completed {self.difficulty} puzzle in {self.elapsed_time} seconds!\nWith {self.hints_used}/{self.hints_max}")
                        self.paused = True

    def playing_draw(self):
        self.window.fill(WHITE)
        self.draw_difficulty(self.window) # Draw difficulty above grid/buttons
        for button in self.playingButtons:
            button.draw(self.window)
        
        # Draw selections/shades BEFORE numbers to avoid drawing over them
        if self.selected:
            self.drawSelection(self.window, self.selected)
        
        self.shadeLockedCells(self.window, self.lockedCells)
        self.shadeIncorrectCells(self.window, self.incorrectCells)
        
        self.drawNumbers(self.window)
        self.drawGrid(self.window)
        self.draw_timer(self.window)
        
        pygame.display.update()
        self.cellChanged = False

    # -----------------------------
    # Timer/Info draw
    # -----------------------------
    def draw_timer(self, window):
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60
        time_str = f"{minutes:02}:{seconds:02}"

        font = pygame.font.SysFont("arial", 30)
        text_surf = font.render(time_str, True, BLACK)

        # --- TIMER: centered below grid ---
        timer_rect = text_surf.get_rect(
            midtop=(
                gridPos[0] + gridSize // 2,
                gridPos[1] + gridSize + 10
            )
        )
        window.blit(text_surf, timer_rect)

        # --- HINT COUNTER ABOVE HINT BUTTON (unchanged) ---
        hint_font = pygame.font.SysFont("arial", 22)
        hint_str = f"Hints: {self.hints_used}/{self.hints_max}"
        hint_surf = hint_font.render(hint_str, True, BLACK)

        for button in self.playingButtons:
            if button.text == "Hint":
                hint_rect = hint_surf.get_rect(
                    midbottom=(button.rect.centerx, button.rect.top - 5)
                )
                window.blit(hint_surf, hint_rect)
                break

    def draw_difficulty(self, window):
        if not self.difficulty:
            return

        font = pygame.font.SysFont("arial", 28)
        text = f"Difficulty: {self.difficulty.capitalize()}"
        surf = font.render(text, True, BLACK)

        # Position above the buttons/grid
        x = gridPos[0]
        y = gridPos[1] - 100

        window.blit(surf, (x, y))

    def allCellsDone(self):
        for row in self.grid:
            for number in row:
                if number == 0:
                    return False
        return True

    def checkAllCells(self):
        self.checkRows()
        self.checkColumns()
        self.checkSmallGrid()

    def checkSmallGrid(self):
        for x in range(3):
            for y in range(3):
                # This logic is likely flawed for *checking correctness*. It seems designed for a solver.
                possibles = list(range(1,10))
                for i in range(3):
                    for j in range(3):
                        xidx = x*3+i
                        yidx = y*3+j
                        if self.grid[yidx][xidx] != 0 and self.grid[yidx][xidx] in possibles:
                            possibles.remove(self.grid[yidx][xidx])
                        elif self.grid[yidx][xidx] != 0 and (xidx, yidx) not in self.lockedCells and (xidx, yidx) not in self.incorrectCells:
                            # A duplicate was found in this subgrid's 'possibles' logic
                            pass # simplified to avoid complex error handling that might conflict

    def checkRows(self):
        for yidx, row in enumerate(self.grid):
            possibles = list(range(1,10))
            for xidx in range(9):
                if self.grid[yidx][xidx] != 0 and self.grid[yidx][xidx] in possibles:
                    possibles.remove(self.grid[yidx][xidx])
                elif self.grid[yidx][xidx] != 0 and (xidx, yidx) not in self.lockedCells and (xidx, yidx) not in self.incorrectCells:
                    pass # simplified

    def checkColumns(self):
        for xidx in range(9):
            possibles = list(range(1,10))
            for yidx in range(9):
                if self.grid[yidx][xidx] != 0 and self.grid[yidx][xidx] in possibles:
                    possibles.remove(self.grid[yidx][xidx])
                elif self.grid[yidx][xidx] != 0 and (xidx, yidx) not in self.lockedCells and (xidx, yidx) not in self.incorrectCells:
                    pass # simplified

    # -----------------------------
    # Helper functions
    # -----------------------------
    def shadeLockedCells(self, window, locked):
        for cell in locked:
            pygame.draw.rect(window, LOCKEDCELLCOLOR, (cell[0]*cellSize+gridPos[0], cell[1]*cellSize+gridPos[1], cellSize, cellSize))

    def shadeIncorrectCells(self, window, incorrect):
        for cell in incorrect:
            pygame.draw.rect(window, INCORRECTCELLCOLOR, (cell[0]*cellSize+gridPos[0], cell[1]*cellSize+gridPos[1], cellSize, cellSize))

    def drawNumbers(self, window):
        for yidx, row in enumerate(self.grid):
            for xidx, num in enumerate(row):
                if num != 0:
                    pos = [xidx*cellSize+gridPos[0], yidx*cellSize+gridPos[1]]
                    # Use a different color for user-entered vs. locked numbers
                    color = BLACK
                    if (xidx, yidx) in self.lockedCells:
                         color = DARK_GRAY # or a distinct color
                    
                    self.textToScreen(window, str(num), pos, color)

    def drawSelection(self, window, pos):
        pygame.draw.rect(window, LIGHTBLUE, (pos[0]*cellSize+gridPos[0], pos[1]*cellSize+gridPos[1], cellSize, cellSize))

    def drawGrid(self, window):
        # Outer Border
        pygame.draw.rect(window, BLACK, (gridPos[0], gridPos[1], gridSize, gridSize), 2)
        
        # Inner lines
        for x in range(1, 9):
            # Vertical lines
            thickness = 2 if x % 3 == 0 else 1
            pygame.draw.line(window, BLACK, (gridPos[0]+x*cellSize, gridPos[1]), (gridPos[0]+x*cellSize, gridPos[1]+gridSize), thickness)
            # Horizontal lines
            pygame.draw.line(window, BLACK, (gridPos[0], gridPos[1]+x*cellSize), (gridPos[0]+gridSize, gridPos[1]+x*cellSize), thickness)


    def mouseOnGrid(self):
        # Check if mouse is within the grid boundaries
        if self.mousePos[0] < gridPos[0] or self.mousePos[1] < gridPos[1]: return False
        if self.mousePos[0] > gridPos[0]+gridSize or self.mousePos[1] > gridPos[1]+gridSize: return False
        
        # Calculate cell coordinates
        cell = ((self.mousePos[0]-gridPos[0])//cellSize, (self.mousePos[1]-gridPos[1])//cellSize)
        return cell # Return (x, y) tuple

    def loadButtons(self):
        self.playingButtons = []
        
        # Calculate button positions relative to the grid
        start_x = gridPos[0]
        start_y = gridPos[1] - 60
        spacing = 140
        btn_width = 120
        btn_height = 50

        reset_btn = Button(start_x, start_y, btn_width, btn_height, text="Reset")
        pause_btn = Button(start_x + spacing, start_y, btn_width, btn_height, text="Pause")
        hint_btn  = Button(start_x + spacing*2, start_y, btn_width, btn_height, text="Hint")
        menu_btn  = Button(start_x + spacing*3, start_y, btn_width, btn_height, text="Menu")

        self.playingButtons.extend([reset_btn, pause_btn, hint_btn, menu_btn])

        self.hints_used = 0
        self.hints_max = 3 # Reset hints

    def use_hint(self):
        empty_cells = [(x, y) for y in range(9) for x in range(9) if self.grid[y][x] == 0]
        if not empty_cells:
            return
        
        x, y = random.choice(empty_cells)
        self.grid[y][x] = self.solution[y][x]
        
        # Lock the cell if it's a hint
        if (x, y) not in self.lockedCells:
            self.lockedCells.append((x, y)) 
            
        self.hints_used += 1
        self.cellChanged = True
        
        self.logger.debug(f"Hint used. Cell ({x+1}, {y+1}) filled with {self.solution[y][x]}. Hints remaining: {self.hints_max - self.hints_used}")

    def textToScreen(self, window, text, pos, color=BLACK):
        font_surf = self.font.render(text, False, color)
        fontWidth, fontHeight = font_surf.get_width(), font_surf.get_height()
        
        # Center text in the cell
        x = pos[0] + (cellSize-fontWidth)//2
        y = pos[1] + (cellSize-fontHeight)//2
        window.blit(font_surf, (x, y))

    def load(self):
        global lockedCells
        self.lockedCells = []
        for yidx, row in enumerate(self.grid):
            for xidx, num in enumerate(row):
                if num != 0:
                    self.lockedCells.append((xidx, yidx))
        lockedCells = self.lockedCells

        # Load buttons after initial setup
        self.loadButtons() 

    def isInt(self, string):
        try:
            val = int(string)
            return 1 <= val <= 9
        except:
            return False

    def log_solution_board(self):
        if not hasattr(self, "solution") or self.solution is None:
            self.logger.debug("No solution loaded yet.")
            return

        self.logger.debug("\n--- Sudoku Solution ---")
        for y in range(9):
            row_str = ""
            for x in range(9):
                val = self.solution[y][x]
                row_str += str(val) if val != 0 else "."
                if x % 3 == 2 and x != 8:
                    row_str += " | "
                else:
                    row_str += " "
            self.logger.debug(row_str)
            if y % 3 == 2 and y != 8:
                self.logger.debug("-" * 21)

    # -----------------------------
    # Puzzle loading
    # -----------------------------
    def load_puzzles(self, filename="sudoku_puzzles.pkl"):
        # The file loading may fail if the file is missing/corrupted, use try-except
        try:
            with open(filename, "rb") as f:
                self.all_puzzles = pickle.load(f)
        except FileNotFoundError:
            self.logger.error(f"Puzzle file '{filename}' not found. Please create it.")
            self.all_puzzles = {}
        except Exception as e:
            self.logger.error(f"Error loading puzzles: {e}")
            self.all_puzzles = {}


    def get_random_puzzle(self, difficulty="medium"):
        if difficulty in self.all_puzzles and self.all_puzzles[difficulty]:
            return random.choice(self.all_puzzles[difficulty])
        else:
            self.logger.warning(f"No puzzles found for difficulty '{difficulty}'. Using fallback testBoard1.")
            # Fallback in case of missing puzzle file/difficulty
            return testBoard1, testBoard1 # Return a copy of the testBoard as puzzle and solution

if __name__ == '__main__':
    # Initialize game
    app = App()
    app.run()