import pygame, sys
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
		self.state = "playing"
		self.finished = False
		self.cellChanged = False
		self.playingButtons = []
		self.menuButtons = []
		self.font = pygame.font.SysFont('arial', cellSize/2)
		self.endButtons = []
		self.lockedCells = []
		self.incorrectCells = []
		self.load()

	def run(self):
		while self.running:
			if self.state == "playing":
				self.playing_events()
				self.playing_update()
				self.playing_draw()
		pygame.quit()
		sys.exit()

#### Playing State Functions ####

	def playing_events(self):
		for event in pygame.event.get():
			lockedCells = self.lockedCells

			if event.type == pygame.QUIT:
				self.running = False

			#User Clicks
			if event.type == pygame.MOUSEBUTTONDOWN:
				selected = self.mouseOnGrid()
				if self.selected in lockedCells:
					print("Not Possible")
					self.selected = False
					if self.selected == False:
						self.mousePos = None
				elif self.selected not in lockedCells:
					print(selected)
					self.selected = selected

			#User Types
			if event.type == pygame.KEYDOWN:
				print("checking...")
				if self.selected in lockedCells:
					self.selected = False
					print("Not Possible")
				elif self.selected not in lockedCells:
					if self.isInt(event.unicode):
						# Cell Changed
						self.grid[self.selected[1]][self.selected[0]] = int(event.unicode)
						self.cellChanged = True


	def playing_update(self):
		self.mousePos = pygame.mouse.get_pos()
		for button in self.playingButtons:
			button.update(self.mousePos)

		if self.cellChanged:
			self.incorrectCells = []
			if self.allCellsDone():
				# Check if board is correct
				self.checkAllCells()
				if len(self.incorrectCells) == 0:
					print("Congratulations! ")

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
		pygame.display.update()
		self.cellChanged = False

#### Board Check Functions ####
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
				possibles = [1,2,3,4,5,6,7,8,9]
				print("Resetting Possibles...")
				for i in range(3):
					for j in range(3):
						# print(x*3+i, y*3+j)
						xidx = x*3+i
						yidx = y*3+j
						if self.grid[xidx][yidx] in possibles:
							possibles.remove(self.grid[xidx][yidx])
						elif [xidx, yidx] not in self.lockedCells and [xidx, yidx] not in self.incorrectCells:
							self.incorrectCells.append([xidx, yidx])
							print("Error Found! ")

	def checkRows(self):
		for yidx, row in enumerate(self.grid):
			possibles = [1,2,3,4,5,6,7,8,9]
			for xidx in range(9):
				if self.grid[yidx][xidx] in possibles:
					possibles.remove(self.grid[yidx][xidx])
				else:
					if [xidx, yidx] not in self.lockedCells and [xidx, yidx] not in self.incorrectCells:
						self.incorrectCells.append([xidx, yidx])

	def checkColumns(self):
		for xidx in range(9):
			possibles = [1,2,3,4,5,6,7,8,9]
			for yidx, row in enumerate(self.grid):
				if self.grid[yidx][xidx] in possibles:
					possibles.remove(self.grid[yidx][xidx])
				else:
					if [xidx, yidx] not in self.lockedCells and [xidx, yidx] not in self.incorrectCells:
						self.incorrectCells.append([xidx, yidx])


#### Helper Functions ####

	def shadeLockedCells(self,window,locked):
		for cell in locked:
			pygame.draw.rect(window, LOCKEDCELLCOLOR, (cell[0]*cellSize+gridPos[0], cell[1]*cellSize+gridPos[1], cellSize, cellSize))

	def shadeIncorrectCells(self,window,incorrect):
		for cell in incorrect:
			pygame.draw.rect(window, INCORRECTCELLCOLOR, (cell[0]*cellSize+gridPos[0], cell[1]*cellSize+gridPos[1], cellSize, cellSize))


	def drawNumbers(self, window):
		for yidx, row in enumerate(self.grid):
			for xidx, num in enumerate(row):
				if num != 0:
					pos = [(xidx*cellSize)+gridPos[0],(yidx*cellSize)+gridPos[1]]
					self.textToScreen(window, str(num), pos)

	def drawSelection(self, window, pos):
		pygame.draw.rect(window, LIGHTBLUE, ((pos[0]*cellSize)+gridPos[0], (pos[1]*cellSize)+gridPos[1],cellSize, cellSize))

	def drawGrid(self, window):
		pygame.draw.rect(window, BLACK, (gridPos[0], gridPos[1], WIDTH-150, HEIGHT-150), 2)
		for x in range(9):
			pygame.draw.line(window, BLACK, (gridPos[0]+(x*cellSize), gridPos[1]), (gridPos[0]+(x*cellSize), gridPos[1]+450), 2 if x % 3 == 0 else 1)
			pygame.draw.line(window, BLACK, (gridPos[0], gridPos[1]+(x*cellSize)), (gridPos[0]+450,gridPos[1]+(x*cellSize)), 2 if x % 3 == 0 else 1)

	def mouseOnGrid(self):
		if self.mousePos[0] < gridPos[0] or self.mousePos[1] < gridPos[1]:
			return False
		if self.mousePos[0] > gridPos[0]+gridSize or self.mousePos[1] > gridPos[1]+gridSize:
			return False
		proced = ((self.mousePos[0]-gridPos[0])//cellSize, (self.mousePos[1]-gridPos[1])//cellSize)
		if proced in self.lockedCells:
			self.selected = False
		elif proced not in self.lockedCells:
			return proced

	def loadButtons(self):
		self.playingButtons.append(Button(20, 40, 100, 40))

	def textToScreen(self, window, text, pos):
		font = self.font.render(text, False, BLACK)
		fontWidth = font.get_width()
		fontHeight = font.get_height()
		pos[0] += (cellSize-fontWidth)//2
		pos[1] += (cellSize-fontHeight)//2
		window.blit(font, pos)

	def load(self):
		self.loadButtons()

		#Setting locked cells from original
		for yixd, row in enumerate(self.grid):
			for xidx, num in enumerate(row):
				if num != 0:
					self.lockedCells.append((xidx, yixd))
		print(self.lockedCells)
		lockedCells = self.lockedCells
		global lockedCells

	def isInt(self, string):
		try:
			int(string)
			return True
		except:
			return False
