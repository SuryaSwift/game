import sys
 
import pygame
from pygame.locals import *
 
pygame.init()
 
fps = 60
fpsClock = pygame.time.Clock()

width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Game')

player = pygame.image.load('player.jpeg')
player = pygame.transform.scale(player, (100, 100))

def draw(): 
    screen.blit(player, player.get_rect()) 

def update(): 
  pass

# Game loop.
while True:
  screen.fill((0, 0, 0)) # Fill the screen with black.
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
      sys.exit()
  
  # Update.
  update()
  # Draw.
  draw()

  pygame.display.flip()
  fpsClock.tick(fps)