from pathlib import Path

from PIL import Image
from cartridge import Cartridge
from render import PatternTile, NameTable, Palette, PPU2c02
from nes import NES

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def save_frame_as_image(frame: list[list[tuple[int, int, int]]], filename: str):
    pixels = [pixel for row in frame for pixel in row]
    height = len(frame)
    width = len(frame[0]) if height > 0 else 0
    img = Image.new('RGB', (width, height))
    img.putdata(pixels)
    img.save(DATA_DIR / filename)



def test_render_pattern_table():
    pass


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

def test_render_nametable(nes: NES, ppu: PPU2c02):
    ppu.write_tile(n_x=0, n_y=0, pattern_index=3)
    ppu.write_tile(n_x=10, n_y=10, pattern_index=7)
    ppu.write_tile(n_x=31, n_y=29, pattern_index=7)
    frame = nes.resolve_frame()
    save_frame_as_image(frame, "test_render_nametable.png")
    # TODO: put assertions


def test_write_to_vram(nes: NES, ppu: PPU2c02):
    for i in range(255*240):
        ppu.write_addr(0x20)
        ppu.write_addr(i)
        ppu.write_data(0)
    frame = nes.resolve_frame()
    save_frame_as_image(frame, "test_write_to_vram.png")
    # TODO: put assertions


def test_ppu_generates_pixels(ppu: PPU2c02):
    ppu.write_tile(n_x=0, n_y=0, pattern_index=0)

    frame = []
    for scanline in range(262):
        row = []
        for cycle in range(341):
            pixel = ppu.tick()
            if pixel is not None:
                color = pixel
            elif scanline < 240:
                color = (50, 50, 50)
            elif scanline == 240:
                color = (100, 50, 50)
            elif scanline <= 260:
                color = (50, 100, 50)
            else:
                color = (50, 50, 100)
            row.append(color)
        frame.append(row)

    save_frame_as_image(frame, "test_ppu_generates_pixels.png")


