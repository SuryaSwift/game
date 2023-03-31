import pygame
from pygame.locals import *
from pygame.math import Vector2
import pytmx
import utils 

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, world):
        super().__init__()
        self.state = 'CLOSED'
        self.anim_frame = 0
        self.world = world
        self.sprites = utils.load_door_sprites()
        self.image = self.sprites[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        print(f"Door created at {x}, {y} with size {self.rect.width}, {self.rect.height}")

    def toggle(self): 
        """Toggles the door state.
            - If the door is closed, it will start opening.
            - If the door is open, it will start closing.
        """
        if self.state == 'CLOSED':
            self.open()
        elif self.state == 'OPEN':
            self.close()
        else:
            print(f"Door cannot be toggled from {self.state} state")

    def open(self):
        """Opens the door.
            - If the door is closed, it will start opening.
        """
        if self.state == 'CLOSED':
            self.state = 'OPENING'
            self.anim_frame = 0
        else:
            print(f"Door cannot be opened from {self.state} state")
    
    def close(self):
        """Closes the door.
            - If the door is open, it will start closing.
        """
        if self.state == 'OPEN':
            self.state = 'CLOSING'
        else: 
            print(f"Door cannot be closed from {self.state} state")

    def is_open(self):
        return self.state == 'OPEN'
    
    def view(self):
        return self.sprites[self.anim_frame]
        
    def update(self):
        if self.state == 'OPENING':
            self.anim_frame += 1
            if self.anim_frame == len(self.sprites) - 1:
                self.state = 'OPEN'
        elif self.state == 'CLOSING':
            self.anim_frame -= 1
            if self.anim_frame == 0:
                self.state = 'CLOSED'

class World: 
    def __init__(self, tiled_map):
        """
        Represents the game world. 
        tiled_map: pytmx.TiledMap, the Tiled map data 
        """
        self.tiled_map = tiled_map
        self.tilesize = tiled_map.tilewidth
        self.width = self.tiled_map.width
        self.height = self.tiled_map.height
        self.ground = self.tiled_map.get_layer_by_name('Ground')
        self.foreground = self.tiled_map.get_layer_by_name('Foreground')
        self.objects = self.tiled_map.get_layer_by_name('Objects')
        self.doors = {(d.x // self.tilesize, d.y // self.tilesize): Door(d.x, d.y, self) for d in self.tiled_map.get_layer_by_name('Doors')}

    def update(self):
        for door in self.doors.values():
            door.update()
        
    def will_collide(self, x,y): 
        """
            Returns true if the player will collide with the world at the given position. 
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        if self.objects.data[y][x] != 0:
            return True
        if (x,y) in self.doors and not self.doors[(x,y)].is_open():
            return True
        return False
    
    def draw_ground(self, surface, debug=False):
        """Blits the ground layer to the surface.
            surface: pygame.Surface, must be (self.width * self.tilesize, self.height * self.tilesize)
        """
        for x, y, gid, in self.ground:
            tile = self.tiled_map.get_tile_image_by_gid(gid)
            if tile: 
                tile.set_colorkey((0, 0, 0))
                surface.blit(tile, (x * self.tilesize, y * self.tilesize))
        return surface 
    
    def draw_objects(self, surface: pygame.Surface, debug=False):
        """Blits the objects layer to the surface.
            surface: pygame.Surface, must be (self.width * self.tilesize, self.height * self.tilesize)
        """
        for x, y, gid, in self.objects:
            tile = self.tiled_map.get_tile_image_by_gid(gid)
            if tile: 
                tile.set_colorkey((0, 0, 0))
                surface.blit(tile, (x * self.tilesize, y*self.tilesize))
                if debug: 
                    # create a red rectangle around the object
                    rect = pygame.Rect(x * self.tilesize, y * self.tilesize, self.tilesize, self.tilesize)
                    # draw the outline of the rect in red on the surface 
                    pygame.draw.rect(surface, (255, 0, 0), rect, 1)
        
        for door in self.doors.values():
            surface.blit(door.view(), door.rect)
        
        return surface
    
    def draw_foreground(self, surface: pygame.Surface, debug=False): 
        """Blits the foreground layer to the surface.
            surface: pygame.Surface, must be (self.width * self.tilesize, self.height * self.tilesize)
        """
        for x, y, gid, in self.foreground:
            tile = self.tiled_map.get_tile_image_by_gid(gid)
            if tile: 
                tile.set_colorkey((0, 0, 0))
                surface.blit(tile, (x * self.tilesize, y*self.tilesize))
                rect = pygame.Rect(x * self.tilesize, y * self.tilesize, self.tilesize, self.tilesize)
        return surface

class Player(pygame.sprite.Sprite): 
    def __init__(self, x, y, world: World, sprites):
        """
            Represents player, the main controllable character. 
            x: the x position of the player in tiles
            y: the y position of the player in tiles
            world: the world object
            sprites: 
                a dictionary of sprites for the player, where the key is a direction and the value is a 
                list containing pygame.Surface instances
                Example: {'DOWN': [pygame.Surface, pygame.Surface, pygame.Surface, pygame.Surface]}
        """
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.world = world
        self.sprites = sprites
        self.state = 'IDLE'
        self.direction = 'DOWN'
        self.anim_frame = 0
        self.speed = 1 # 1 tile per move 
        self.image = self.sprites[self.direction][self.anim_frame]
        self.rect = self.image.get_rect()
        self.tick = 0
        
    def movemap(self, direction):
        """
            Returns the x and y offset for the given direction.
        """
        mmap = {
                'UP': (0, -self.speed),
                'DOWN': (0, self.speed),
                'LEFT': (-self.speed, 0),
                'RIGHT': (self.speed, 0),
            }
        return mmap[direction]

    def update(self, actions): 
        """
            The update function is called every frame. 
            actions: a dictionary of actions that the player has taken.
             Example: {'direction': 'UP'}
        """
        self.tick += 1

        ax,ay = self.movemap(self.direction)
        if (self.x+ax, self.y+ay) in self.world.doors:
            print(self.world.doors[(self.x+ax, self.y+ay)])
            # if key 'SPACE' is pressed, open the door
            # use pygame key constants for this
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                self.world.doors[(self.x+ax, self.y+ay)].toggle()
                return
            

        if self.state == 'IDLE': 
            if actions['direction'] == self.direction:
                dx,dy = self.movemap(actions['direction'])
                if self.world.will_collide(self.x+dx, self.y+dy):
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
            self.anim_frame = (self.anim_frame + 1) % len(self.sprites[self.direction])
            if self.anim_frame % 2 == 0: # next frame is standing still, meaning we've entered new tile 
                self.x += dx
                self.y += dy
                # then we reset the counter and go back to idle
                self.state = 'IDLE'
            
            # shift the sprite's position by half a tile each animation frame 
            self.rect.x += dx * self.world.tilesize / 2
            self.rect.y += dy * self.world.tilesize / 2
                    
        
        self.image = self.sprites[self.direction][self.anim_frame] 
    
    def view(self):
        # print(f"Player view: {self.direction}, {self.anim_frame}")
        return self.sprites[self.direction][self.anim_frame]
        

class Camera: 
    def __init__(self, viewport_size, world: World, player: Player, scale=3, debug=False):
        """
            Creates a camera that follows the player around the world. 
            viewport_size: the size of the viewport in tiles (W, H)
            world: the world object
            player: the player object
            scale: scale factor for tiles, for example 3 means world.tilesize*3 pixels per tile
        """
        self.scale = scale
        self.world = world
        self.player = player
        self.vw, self.vh = viewport_size[0] * world.tilesize, viewport_size[1] * world.tilesize
        # these are pixel coordinates, whereas every other class's coordinates are tile coordinates
        self.x = 0
        self.y = 0
        self.debug = debug

    def set_debug(self, debug):
        self.debug = debug
    
    def contains(self, x,y):
        """
            Returns True if the given pixel coordinates are within the camera's viewport.
        """ 
        return (x >= self.x and x <= (self.x + self.viewportWidth) and
                y >= self.y and y <= (self.y + self.viewportHeight))

    def update(self):
        """
            Updates the camera's position to follow the player.
        """ 
        # target position should be (px, py) - (viewportWidth/2, viewportHeight/2)
        self.x = self.player.rect.x - self.vw * 0.5
        self.y = self.player.rect.y - self.vh * 0.5 
        # self.x = utils.clamp(self.x, 0, self.world.width * self.world.tilesize - self.vw)
        # self.y = utils.clamp(self.y, 0, self.world.height * self.world.tilesize - self.vh)
        

    def draw(self, surface): 
        """
            Draws the contents of the camera's viewport to the given surface.
        """

        # first we draw the entire world to a buffer 
        # TODO: only blit the tiles that are visible in the viewport to reduce draw calls
        worldbuffer = pygame.Surface((self.world.width * self.world.tilesize, self.world.height * self.world.tilesize))
        
        # clear the buffer, then draw the world layer by layer
        worldbuffer.fill((0,0,0))
        self.world.draw_ground(worldbuffer, debug=self.debug)
        self.world.draw_objects(worldbuffer, debug=self.debug)
        worldbuffer.blit(self.player.view(), (self.player.rect.x, self.player.rect.y - self.player.rect.height/2))
        self.world.draw_foreground(worldbuffer, debug=self.debug)

        cambuffer = pygame.Surface((self.vw, self.vh))
        cambuffer.blit(worldbuffer, (0,0), (self.x, self.y, self.vw, self.vh))
        # we subtract the tilesize from the player's y coordinate because the player's y coordinate is the top of the sprite
        # but we want to draw the player's sprite at the bottom of the tile
        # cambuffer.blit(self.player.view(), (self.player.rect.x - self.x, self.player.rect.y - self.y - self.world.tilesize))
        
        if self.debug: 
            # draw text
            pygame.draw.rect(cambuffer, (255,0,255), (self.player.rect.x - self.x, self.player.rect.y - self.y - self.player.rect.height/2, self.player.rect.width, self.player.rect.height), 1)
            pygame.draw.rect(cambuffer, (255,0,0), (self.player.x * self.world.tilesize - self.x, self.player.y * self.world.tilesize - self.y, self.world.tilesize, self.world.tilesize), 1)
        
        # scale the camera buffer by the scale factor
        scene = pygame.transform.scale(cambuffer, (self.vw * self.scale, self.vh * self.scale))
        if self.debug: 
            font = pygame.font.SysFont('Arial', 16)
            text = font.render(f"Player: {self.player.x}, {self.player.y}", True, (255,255,255))
            scene.blit(text, (0,0))

       
        if self.debug: 
            # show which tile the mouse is on
            mx, my = pygame.mouse.get_pos()
            mx = int((mx / self.scale + self.x) / self.world.tilesize)
            my = int((my / self.scale + self.y) / self.world.tilesize)
            text = font.render(f"Mouse: {mx}, {my}", True, (255,255,255))
            scene.blit(text, (0,16))
        
        # blit the final scene to the surface 
        surface.blit(scene, (0,0))
        
class Game: 
    def __init__(self, screen):
        """
            Creates a new game instance.
            screen: the pygame display surface
            
        """
        self.__setup_window()
        self.screen = screen
        self.screen_dims = screen.get_size()
        print(f"Starting new game with resolution: {self.screen_dims}")
        self.states = ['MENU', 'PLAY', 'EXIT']
        self.game_map = pytmx.load_pygame('tiled/boolground.tmx')
        self.world: World = World(self.game_map)
        self.player: Player = Player(0, 0, self.world, sprites=utils.load_player_sprites())
        camera_dims = self.screen_dims[0] / (self.world.tilesize * 2), self.screen_dims[1] / (self.world.tilesize * 2)
        self.debug = False
        self.camera: Camera = Camera(camera_dims, self.world, self.player, scale=2)
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
        
    
    def __setup_window(self):
        # function starts with __ because it's not meant to be called externally
        """ Configures the window settings """
        pygame.display.set_caption('Bool')
        # pygame.display.set_icon(pygame.image.load('sprites/boolground.png'))
        pygame.display.flip()
        
    def mainloop(self): 
        """
        Main game loop.
        """
        while self.state != 'EXIT':
            # print(pygame.mouse.get_pos(), pygame.mouse.get_rel())
            self.clock.tick(30)
            self.screen.fill((88,88,88))
            self.__handle_events()
            if self.state == 'PLAY': 
                self.play()
            elif self.state == 'MENU': 
                self.menu()
            
            pygame.display.flip()
        pygame.display.quit()
        pygame.quit()

    def __handle_events(self):
        """
            Processes events, such as key presses and mouse clicks.
            Updates the game state and stores the actions in the actions dictionary.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = 'EXIT'
            elif event.type == pygame.KEYDOWN:
                # check if 'I' was pressed 
                if event.key == pygame.K_i:
                    self.camera.set_debug(not self.camera.debug)

                for direction in self.direction_keys:
                    if event.key in self.direction_keys[direction]:
                        self.actions['direction'] = direction
            elif event.type == pygame.KEYUP: 
                # this is a hack to make sure the player stops moving when the key is released
                # it prob doesn't work if the player is holding down two keys at once
                self.actions = {
                'direction': None,
                'action': None,
                }
            
    def menu(self):
        """
            Updates the menu state and draws to the screen. Should be called every frame.
        """
        pass
    
    def play(self):
        """
            Updates the game state and draws the game to the screen. Should be called every frame.
        """
        self.player.update(self.actions)
        self.world.update()
        self.camera.update()
        self.camera.draw(self.screen)

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 300
dims = (SCREEN_WIDTH, SCREEN_HEIGHT)


    
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode(dims,flags=pygame.SCALED, vsync=0)
    game = Game(screen)
    game.mainloop()