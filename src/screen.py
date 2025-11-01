import sys

import pygame

from render import PatternTable#, Frame

TILESIZE = 2
SCALE = 3

class Screen:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 800))

    def render_pattern_table(self, table: PatternTable, pos: tuple[int, int]):
        tiles = table.tiles
        for t_i, tile in enumerate(tiles):
            indexes = tile.get_color_indexes()
            t_x = t_i % 16
            t_y = t_i // 16
            for p_y, row in enumerate(indexes):
                for p_x, pixel in enumerate(row):
                    color = (0, 0, 0,)
                    if pixel == 0:
                        color = (0, 0, 0,)
                    elif pixel == 3:
                        color = (255, 255, 255)
                    else:
                        raise Exception(f"No implementation for pixel value {pixel}")
                    self.screen.fill(color, (
                        TILESIZE * p_x + t_x * TILESIZE * 8 + pos[0],
                        TILESIZE * p_y + t_y * TILESIZE * 8 + pos[1],
                        TILESIZE,
                        TILESIZE,
                    ))
        return (*pos, 8 * 16 * TILESIZE, 8 * 16 * TILESIZE)
                    

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def update(self):
        pygame.display.update()

    def draw_pixel(self, rgb_value: tuple[int, int, int], x: int, y: int):
        self.screen.fill(rgb_value, (x*SCALE, y*SCALE, SCALE, SCALE))

    def draw_frame(self, frame: list[list[tuple[int, int, int]]]):
        for y, row in enumerate(frame):
            for x, pixel in enumerate(row):
                self.draw_pixel(pixel, x, y)