import pygame

class Button:
	def __init__(self, x, y, width, height, text=None, color=(73,73,73), highlightedColor=(189,189,189), function=None, params=None):
		self.image = pygame.Surface((width, height))
		self.rect = self.image.get_rect()
		self.pos = (x, y)
		self.rect.topleft = self.pos
		self.text = text
		self.function = function
		self.params = params
		self.color = color
		self.highlightedColor = highlightedColor
		self.highlighted = False

	def update(self,mouse):
		if self.rect.collidepoint(mouse):
			self.highlighted = True
		else:
			self.highlighted = False

	def draw(self, window):
		if self.highlighted:
			self.image.fill(self.highlightedColor)
		else:
			self.image.fill(self.color)
		window.blit(self.image, self.pos)
		
#pygame.draw.rect(window, self.highlightedColor if self.highlighted else self.color, self.rect)
#self.image.fill(self.highlightedColor if self.highlighted else self.color)
		#window.blit(self.image, self.pos)