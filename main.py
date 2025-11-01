from pathlib import Path
from time import sleep

from screen import Screen
from nes import NES
from cartridge import Cartridge


def main():
    screen = Screen()
    with open(Path('roms/nestest.nes'), 'rb') as rom:
        cartridge = Cartridge(rom.read())
    nes = NES(cartridge)
    nes.ppu.status = 0x80
    nes.reset()
    table = nes.cartridge.get_pattern_table(0)
    rect = screen.render_pattern_table(table, (10, 10))
    screen.update()
    # for _ in range(19740):
    while True:
        screen.loop()
        for _ in range(200):
            nes.cpu.execute()
        frame = nes.resolve_frame()
        screen.draw_frame(frame)
        screen.update()

if __name__ == "__main__":
    main()