import pygame, sys, pickle, random
from settings import *
from buttonClass import *

class App:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        window = self.window
        global window

        self.running = True
        self.grid = testBoard1
        self.selected = None
        self.mousePos = None
        self.state = "menu"  # start with menu
        self.finished = False
        self.cellChanged = False
        self.playingButtons = []
        self.menuButtons = []
        self.font = pygame.font.SysFont('arial', cellSize//2)
        self.endButtons = []
        self.lockedCells = []
        self.incorrectCells = []

        self.timer_start = None  # Timer start
        self.elapsed_time = 0

        self.load()
        self.load_puzzles()
        self.load_menu_buttons()

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
            clock.tick(60)  # limit to 60 FPS
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
                        # Load random puzzle of selected difficulty
                        difficulty = btn.text.lower()
                        puzzle, solution = self.get_random_puzzle(difficulty)
                        self.grid = puzzle
                        self.solution = solution
                        self.lockedCells = [(x,y) for y in range(9) for x in range(9) if puzzle[y][x] != 0]
                        self.state = "playing"
                        self.timer_start = pygame.time.get_ticks()  # start timer

    def menu_draw(self):
        self.window.fill(WHITE)
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

            # User clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                selected = self.mouseOnGrid()
                if selected in lockedCells:
                    self.selected = False
                    self.mousePos = None
                else:
                    self.selected = selected

            # User types
            if event.type == pygame.KEYDOWN:
                if self.selected not in lockedCells and self.isInt(event.unicode):
                    self.grid[self.selected[1]][self.selected[0]] = int(event.unicode)
                    self.cellChanged = True

    def playing_update(self):
        self.mousePos = pygame.mouse.get_pos()
        for button in self.playingButtons:
            button.update(self.mousePos)

        # Update timer
        if self.timer_start:
            self.elapsed_time = (pygame.time.get_ticks() - self.timer_start) // 1000  # seconds

        if self.cellChanged:
            self.incorrectCells = []
            if self.allCellsDone():
                self.checkAllCells()
                if len(self.incorrectCells) == 0:
                    print("Congratulations!")

    def playing_draw(self):
        self.window.fill(WHITE)
        for button in self.playingButtons:
            button.draw(self.window)
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
    # Timer draw
    # -----------------------------
    def draw_timer(self, window):
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60
        time_str = f"{minutes:02}:{seconds:02}"
        font = pygame.font.SysFont("arial", 30)
        text_surf = font.render(time_str, True, BLACK)
        window.blit(text_surf, (WIDTH-150, 20))

    # -----------------------------
    # Board checks (same as before)
    # -----------------------------
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
                possibles = list(range(1,10))
                for i in range(3):
                    for j in range(3):
                        xidx = x*3+i
                        yidx = y*3+j
                        if self.grid[xidx][yidx] in possibles:
                            possibles.remove(self.grid[xidx][yidx])
                        elif (xidx, yidx) not in self.lockedCells and (xidx, yidx) not in self.incorrectCells:
                            self.incorrectCells.append((xidx, yidx))

    def checkRows(self):
        for yidx, row in enumerate(self.grid):
            possibles = list(range(1,10))
            for xidx in range(9):
                if self.grid[yidx][xidx] in possibles:
                    possibles.remove(self.grid[yidx][xidx])
                elif (xidx, yidx) not in self.lockedCells and (xidx, yidx) not in self.incorrectCells:
                    self.incorrectCells.append((xidx, yidx))

    def checkColumns(self):
        for xidx in range(9):
            possibles = list(range(1,10))
            for yidx in range(9):
                if self.grid[yidx][xidx] in possibles:
                    possibles.remove(self.grid[yidx][xidx])
                elif (xidx, yidx) not in self.lockedCells and (xidx, yidx) not in self.incorrectCells:
                    self.incorrectCells.append((xidx, yidx))

    # -----------------------------
    # Helper functions (same as before)
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
                    self.textToScreen(window, str(num), pos)

    def drawSelection(self, window, pos):
        pygame.draw.rect(window, LIGHTBLUE, (pos[0]*cellSize+gridPos[0], pos[1]*cellSize+gridPos[1], cellSize, cellSize))

    def drawGrid(self, window):
        pygame.draw.rect(window, BLACK, (gridPos[0], gridPos[1], WIDTH-150, HEIGHT-150), 2)
        for x in range(9):
            pygame.draw.line(window, BLACK, (gridPos[0]+x*cellSize, gridPos[1]), (gridPos[0]+x*cellSize, gridPos[1]+450), 2 if x%3==0 else 1)
            pygame.draw.line(window, BLACK, (gridPos[0], gridPos[1]+x*cellSize), (gridPos[0]+450, gridPos[1]+x*cellSize), 2 if x%3==0 else 1)

    def mouseOnGrid(self):
        if self.mousePos[0] < gridPos[0] or self.mousePos[1] < gridPos[1]: return False
        if self.mousePos[0] > gridPos[0]+gridSize or self.mousePos[1] > gridPos[1]+gridSize: return False
        cell = ((self.mousePos[0]-gridPos[0])//cellSize, (self.mousePos[1]-gridPos[1])//cellSize)
        return cell if cell not in self.lockedCells else False

    def loadButtons(self):
        self.playingButtons.append(Button(20, 40, 100, 40))

    def textToScreen(self, window, text, pos):
        font_surf = self.font.render(text, False, BLACK)
        fontWidth, fontHeight = font_surf.get_width(), font_surf.get_height()
        pos[0] += (cellSize-fontWidth)//2
        pos[1] += (cellSize-fontHeight)//2
        window.blit(font_surf, pos)

    def isInt(self, string):
        try:
            int(string)
            return True
        except:
            return False

    # -----------------------------
    # Puzzle loading functions
    # -----------------------------
    def load_puzzles(self, filename="sudoku_puzzles.pkl"):
        with open(filename, "rb") as f:
            self.all_puzzles = pickle.load(f)

    def get_random_puzzle(self, difficulty="medium"):
        return random.choice(self.all_puzzles[difficulty])
