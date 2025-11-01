from time import sleep

from cartridge import Cartridge
from screen import Screen
from render import PatternTile, NameTable, Palette, PPU2c02
from nes import NES



def test_render_pattern_table(screen: Screen, cartridge: Cartridge):
    table = cartridge.get_pattern_table(index=0)
    screen.render_pattern_table(table, (0, 0))
    screen.update()


def test_combine_pattern_table_planes():
    # Grabbed from https://www.nesdev.org/wiki/PPU_pattern_tables
    first_plane  = b"\x41\xC2\x44\x48\x10\x20\x40\x80"
    second_plane = b"\x01\x02\x04\x08\x16\x21\x42\x87"
    tile = PatternTile(first_plane + second_plane)
    indexes = tile.get_color_indexes()
    assert indexes == [
        [0, 1, 0, 0, 0, 0, 0, 3],
        [1, 1, 0, 0, 0, 0, 3, 0],
        [0, 1, 0, 0, 0, 3, 0, 0],
        [0, 1, 0, 0, 3, 0, 0, 0],
        [0, 0, 0, 3, 0, 2, 2, 0],
        [0, 0, 3, 0, 0, 0, 0, 2],
        [0, 3, 0, 0, 0, 0, 2, 0],
        [3, 0, 0, 0, 0, 2, 2, 2],
    ]


def test_resolve_colors_frame():
    class TestPalette(Palette):
        def get_color(self, index: int):
            return (255, 255, 255) if index == 3 else (0, 0, 0)

    name_table = NameTable()
    palette = TestPalette()
    assert name_table.resolve_frame(palette) == [
        [(0, 0, 0) for _ in range(256)]
        for _ in range(240)
    ]

def test_write_to_nametable():
    nametable = NameTable()
    tile = PatternTile(b"\x80\x80\x00\x00\x00\x00\x00\x00\x80\x80\x00\x00\x00\x00\x00\x00")
    nametable.write_tile(tile, 0, 0)
    frame = nametable.resolve_frame(Palette())
    assert frame[0][0] == (255, 255, 255)
    assert frame[1][0] == (255, 255, 255)

def test_draw_pixel_on_screen(screen: Screen):
    screen.draw_pixel((255, 255, 255), 0, 0)
    screen.update()
    sleep(1)


def test_render_nametable(screen: Screen, nes: NES, ppu: PPU2c02):
    ppu.write_tile(n_x=0, n_y=0, pattern_index=3)
    ppu.write_tile(n_x=10, n_y=10, pattern_index=7)
    ppu.write_tile(n_x=31, n_y=29, pattern_index=7)
    frame = nes.resolve_frame()
    screen.draw_frame(frame)
    screen.update()
    screen.update()
    sleep(2)


def test_write_to_vram(screen: Screen, nes: NES, ppu: PPU2c02):
    ppu.write_addr(0x10)
    ppu.write_addr(0x01)
    ppu.write_data(5)
    frame = nes.resolve_frame()
    screen.draw_frame(frame)
    screen.update()
    sleep(1)