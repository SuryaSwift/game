import numpy as np 
import cv2 
import pygame
import matplotlib.pyplot as plt
class SpriteSheet:
    """Class used to grab images out of a sprite sheet."""
    def __init__(self, filename):
        """Load the sheet."""
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error as e:
            print(f"Unable to load spritesheet image: {filename}")
            raise SystemExit(e)

    def grid_split(self, nrows, ncols, colorkey=(0,128,255)):
        """
        Split the sheet into a grid of nrows x ncols tiles.
        Returns a list of lists of surfaces, one for each row.
        """
        imgheight = self.sheet.get_height()
        imgwidth = self.sheet.get_width()
        y1 = 0
        M = imgheight//nrows
        N = imgwidth//ncols
        tiles=[]
        for y in range(0,imgheight,M):
            rowtiles = []
            for x in range(0, imgwidth, N):
                y1 = y + M
                x1 = x + N
                img = self.image_at((x,y,x1-x,y1-y), colorkey)
                # v = pygame.surfarray.array3d(img).swapaxes(0,1)
                # plt.imshow(v)
                # plt.show()
                # img = pygame.transform.scale(img, (50, 100))
                img.set_colorkey(colorkey, pygame.RLEACCEL)
                rowtiles.append(img)
            tiles.append(rowtiles)
        return tiles
    
    def image_at(self, rectangle, colorkey = None):
        """Load a specific image from a specific rectangle."""
        # Loads image from x, y, x+offset, y+offset.
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image


def clamp(n, a, b): 
    """Clamp a number between a and b (inclusive)
        n: number to clamp
        a: lower bound
        b: upper bound
        Examples: 
            clamp(5, 0, 10) -> 5
            clamp(-1, 0, 10) -> 0
    """
    return max(min(b, n), a)

def load_door_sprites(path="tiled/door_anims.png"): 
    ss = SpriteSheet(path)
    rows = ss.grid_split(7, 4)

    door = rows[4]
    # for col in door: 
    #     numpy_surf = pygame.surfarray.array3d(col)
    #     numpy_surf = numpy_surf.swapaxes(0,1)
    #     plt.imshow(numpy_surf)
    #     plt.show()
    return door

def load_player_sprites(path="tiled/man.png"): 
    """Load the player sprites from a spritesheet
    Returns a dictionary of lists of surfaces, one for each direction.
    path: path to the spritesheet
    tilesize: size of each tile in pixels
    """
    ss = SpriteSheet(path)
    rows = ss.grid_split(3,4)
    return {
        'DOWN': rows[0],
        'RIGHT': rows[1],
        'UP': rows[2],
        'LEFT': [pygame.transform.flip(surf, True, False) for surf in rows[1]],
    }

def read_spritesheet(path, nrows, ncols, tilesize=50): 
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
    rows = split_image(img, nrows, ncols)
    surfaces = []
    for i, row in enumerate(rows): 
        surfs = []
        for j, tilearray in enumerate(row): 
            tilearray = (255*tilearray/tilearray.max()).astype(np.uint8)
            # use custom function to make surface with per-pixel alpha
            surf = make_surface_rgba(tilearray)
            pygame.transform.scale(surf, (tilesize*2, tilesize))
            surfs.append(surf)
        surfaces.append(surfs)
    return surfaces 

import numpy
import pygame.pixelcopy

def make_surface_rgba(array):
    """Returns a surface made from a [w, h, 4] numpy array with per-pixel alpha
    """
    shape = array.shape
    if len(shape) != 3 and shape[2] != 4:
        raise ValueError("Array not RGBA")

    # Create a surface the same width and height as array and with
    # per-pixel alpha.
    surface = pygame.Surface(shape[0:2], pygame.SRCALPHA, 32)

    # Copy the rgb part of array to the new surface.
    pygame.pixelcopy.array_to_surface(surface, array[:,:,0:3])

    # Copy the alpha part of array to the surface using a pixels-alpha
    # view of the surface.
    surface_alpha = numpy.array(surface.get_view('A'), copy=False)
    surface_alpha[:,:] = array[:,:,3]

    return surface

if __name__ == "__main__":
    pygame.init()
    gameScreen = pygame.display.set_mode((500, 500), flags=pygame.SCALED, vsync=1)
    sprites = load_player_sprites()
    door_sprites = load_door_sprites()