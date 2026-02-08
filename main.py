from pathlib import Path

from screen import Screen
from nes import NES
from cartridge import Cartridge


def main():
    screen = Screen()
    with open(Path('roms/nestest.nes'), 'rb') as rom:
        cartridge = Cartridge(rom.read())
    nes = NES(cartridge, screen)
    nes.ppu.status = 0x80
    nes.reset()
    while True:
        screen.process_events()
        nes.update()

if __name__ == "__main__":
    main()