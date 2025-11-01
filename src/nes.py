# from pathlib import Path

from cartridge import Cartridge
from processor import CPU6502
from render import PPU2c02


class NES:
    def __init__(self, cartridge: Cartridge):
        # self.cartridge = Cartridge(rom_file)
        self.cartridge = cartridge
        self.ppu = PPU2c02(patterntables=(self.cartridge.get_pattern_table(0), self.cartridge.get_pattern_table(1)))
        self.cpu = CPU6502(self)
        self.ram = [0 for _ in range(2 * 1024)]

    def reset(self):
        self.cpu.reset()

    def read(self, addr: int) -> int:
        assert 0 <= addr <= 0xFFFF
        if addr <= 0x1FFF:
            return self.ram[addr & 0x07FF]
        # PPU status registers
        elif addr == 0x2002:
            return self.ppu.get_status()
        elif 0x8000 <= addr <= 0xFFFF:
            return self.cartridge.read(addr)
        else:
            raise Exception(f"Unmapped address used: {addr:04X}")

    def write(self, addr: int, value: int):
        assert 0 <= addr <=0xFFFF
        assert 0 <= value <= 0xFF
        if addr <= 0x1FFF:
            self.ram[addr & 0x07FF] = value
        # PPU registers
        elif 0x2000 == addr:
            self.ppu.set_control(value)
        elif 0x2001 == addr:
            self.ppu.set_mask(value)
        elif 0x2005 == addr:
            # Something with scrolling. Not important for drawing things on the screen
            self.ppu.r_W = True
        elif 0x2006 == addr:
            self.ppu.write_addr(value)
        elif 0x2007 == addr:
            self.ppu.write_data(value)
        elif 0x4000 <= addr <= 0x4017:
            ... # IO and APU stuff
        else:
            raise Exception(f"Unmapped address used: {addr:04X}")

    def resolve_frame(self):
        return self.ppu.resolve_frame()
