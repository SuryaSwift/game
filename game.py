import pygame
from pygame.locals import *
from pygame.math import Vector2
import pytmx
import utils 

class World: 
    def __init__(self, tiled_map):
        """
        Represents the game world. 
        """
        self.tiled_map = tiled_map
        self.tilesize = tiled_map.tilewidth
        self.width = self.tiled_map.width
        self.height = self.tiled_map.height
        self.ground = self.tiled_map.get_layer_by_name('Ground')
        self.objects = self.tiled_map.get_layer_by_name('Objects')

    def update(self):
        pass
        
    def will_collide(self, x,y): 
        """
        Returns true if the player will collide with the world at the given position. 
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        if self.objects.data[y][x] != 0:
            return True
        return False
    
    def draw_ground(self, surface):
        for x, y, gid, in self.ground:
            tile = self.tiled_map.get_tile_image_by_gid(gid)
            if tile: 
                tile.set_colorkey((0, 0, 0))
                surface.blit(tile, (x * self.tilesize, y * self.tilesize))
        return surface 
    
    def draw_objects(self, surface: pygame.Surface):
        for x, y, gid, in self.objects:
            tile = self.tiled_map.get_tile_image_by_gid(gid)
            if tile: 
                tile.set_colorkey((0, 0, 0))
                surface.blit(tile, (x * self.tilesize, y*self.tilesize))
                # create a red rectangle around the object
                rect = pygame.Rect(x * self.tilesize, y * self.tilesize, self.tilesize, self.tilesize)
                # draw the outline of the rect in red on the surface 
                pygame.draw.rect(surface, (255, 0, 0), rect, 1)
        return surface

class Player(pygame.sprite.Sprite): 
    def __init__(self, x, y, world: World):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.world = world
        self.color = (255, 0, 0)
        self.state = 'IDLE'
        self.direction = 'DOWN'
        self.anim_frame = 0
        self.speed = 1 # 1 tile per move 
        self.image = player_sprites[self.direction][self.anim_frame]
        self.rect = self.image.get_rect()
        
        self.tick = 0
        
    
    def movemap(self, direction):
        mmap = {
                'UP': (0, -self.speed),
                'DOWN': (0, self.speed),
                'LEFT': (-self.speed, 0),
                'RIGHT': (self.speed, 0),
            }
        return mmap[direction]

    def update(self, actions): 
        if actions['direction']:
            print(f"Player state: {self.state}, input: {actions}")
            print(f"Player position: ({self.x},{self.y}) facing {self.direction}")
            print(f"Player rect: {self.rect}")
            print(f"Player tick: {self.tick}")
            print()
            print()

        # check key press, then move player position on next line
        self.tick += 1

        if self.state == 'IDLE': 
            if actions['direction'] == self.direction:
                dx,dy = self.movemap(actions['direction'])
                if self.world.will_collide(self.x+dx, self.y+dy):
                    # if we're already facing the direction of the keypress
                    # and we're about to collide with something, we don't
                    # want to change the state to WALK
                    print("Collision detected, not moving")
                    return
                # enter the walk state
                self.state = 'WALK'
            elif actions['direction']:
                # face the direction of the keypress
                self.direction = actions['direction']
        elif self.state == 'WALK':
            if self.tick % 2 != 0:
                return
            dx,dy = self.movemap(self.direction)
            # play the walking animation by 1 tick 
            self.anim_frame = (self.anim_frame + 1) % len(player_sprites[self.direction])
            if self.anim_frame % 2 == 0: # next frame is standing still, meaning we've entered new tile 
                self.x += dx
                self.y += dy
                # then we reset the counter and go back to idle
                self.state = 'IDLE'
            
            self.rect.x += dx * self.world.tilesize / 2
            self.rect.y += dy * self.world.tilesize / 2
                    
        
        self.image = player_sprites[self.direction][self.anim_frame] 
    
    def view(self):
        # print(f"Player view: {self.direction}, {self.anim_frame}")
        return player_sprites[self.direction][self.anim_frame]
        

class Camera: 
    def __init__(self, viewport_size, world: World, player: Player, scale=3):
        """
            Creates a camera that follows the player around the world. 
            viewport_size: the size of the viewport in tiles (W, H)
            world: the world object
            player: the player object
        """
        self.scale = scale
        self.world = world
        self.player = player
        self.vw, self.vh = viewport_size[0] * world.tilesize, viewport_size[1] * world.tilesize
        # these are pixel coordinates, whereas every other class's coordinates are tile coordinates
        self.x = 0
        self.y = 0
    
    def contains(self, x,y): 
        return (x >= self.x and x <= (self.x + self.viewportWidth) and
                y >= self.y and y <= (self.y + self.viewportHeight))

    def update(self): 
        # target position should be (px, py) - (viewportWidth/2, viewportHeight/2)
        self.x = self.player.rect.x - self.vw * 0.5
        self.y = self.player.rect.y - self.vh * 0.5 
        self.x = utils.clamp(self.x, 0, self.world.width * self.world.tilesize - self.vw)
        self.y = utils.clamp(self.y, 0, self.world.height * self.world.tilesize - self.vh)
        

    def draw(self, surface): 
        worldbuffer = pygame.Surface((self.world.width * self.world.tilesize, self.world.height * self.world.tilesize))
        worldbuffer.fill((80,150,255))
        self.world.draw_ground(worldbuffer)
        self.world.draw_objects(worldbuffer)

        cambuffer = pygame.Surface((self.vw, self.vh))
        cambuffer.blit(worldbuffer, (0,0), (self.x, self.y, self.vw, self.vh))
        # we subtract the tilesize from the player's y coordinate because the player's y coordinate is the top of the sprite
        # but we want to draw the player's sprite at the bottom of the tile
        cambuffer.blit(self.player.view(), (self.player.rect.x - self.x, self.player.rect.y - self.y - self.world.tilesize))
        
        scene = pygame.transform.scale(cambuffer, (self.vw * self.scale, self.vh * self.scale))
        surface.blit(scene, (0,0))
        
        
# draw a red box 


    
class Game: 
    def __init__(self, screen, screen_dims):
        self.setup_window()
        self.screen = screen
        self.screen_dims = screen.get_size()
        print(f"Starting new game with resolution: {self.screen_dims}")
        self.states = ['MENU', 'PLAY', 'EXIT']
        self.game_map = pytmx.load_pygame('tiled/boolground.tmx')
        self.world: World = World(self.game_map)
        self.player: Player = Player(0, 0, self.world)
        camera_dims = screen_dims[0] / (self.world.tilesize * 2), screen_dims[1] / (self.world.tilesize * 2)

        print(f"Camera dims: {camera_dims}")
        self.camera: Camera = Camera(camera_dims, self.world, self.player)
        self.state = 'PLAY'
        self.clock = pygame.time.Clock()
        self.direction_keys = {
            'UP': [pygame.K_UP, pygame.K_w],
            'DOWN': [pygame.K_DOWN, pygame.K_s],
            'LEFT': [pygame.K_LEFT, pygame.K_a],
            'RIGHT': [pygame.K_RIGHT, pygame.K_d],
        }
        self.action_keys = {
            'EXIT': [pygame.K_ESCAPE, pygame.K_q],
            'SPACE': [pygame.K_SPACE],
        }
        self.actions = {
            'direction': None,
            'action': None,
        }
        
    
    def setup_window(self):
        pygame.display.set_caption('Bool')
        # pygame.display.set_icon(pygame.image.load('sprites/boolground.png'))
        pygame.display.flip()
        
    def mainloop(self): 
        """
        Main game loop.
        """
        while self.state != 'EXIT':
            self.clock.tick(30)
            self.screen.fill((88,88,88))
            self.handle_events()
            if self.state == 'PLAY': 
                self.play()
            elif self.state == 'MENU': 
                self.menu()
            
            pygame.display.flip()
        pygame.display.quit()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = 'EXIT'
            elif event.type == pygame.KEYDOWN:
                for direction in self.direction_keys:
                    if event.key in self.direction_keys[direction]:
                        self.actions['direction'] = direction
            elif event.type == pygame.KEYUP: 
                self.actions = {
                'direction': None,
                'action': None,
                }
            
    def menu(self):
        pass
    
    def play(self):
        self.player.update(self.actions)
        self.world.update()
        self.camera.update()
        self.camera.draw(self.screen)



player_sprites = None
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 300
dims = (SCREEN_WIDTH, SCREEN_HEIGHT)
def main():
    global player_sprites
    pygame.init()
    screen = pygame.display.set_mode(dims,flags=pygame.SCALED, vsync=0)
    game_map = pytmx.load_pygame('tiled/boolground.tmx')
    player_sprites = utils.load_player_sprites()
    game = Game(screen, dims)
    game.mainloop()
    
if __name__ == '__main__':
    main()