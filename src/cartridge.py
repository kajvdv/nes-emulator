from io import BytesIO

# from pathlib import Path
from typing import Literal

from render import PatternTable

class Cartridge:
    def __init__(self, data: bytes):
        # Parsing not fully complete, but works for nestest
        with BytesIO(data) as reader:
            header = reader.read(16)
            assert header[:4] == b'NES\x1A'
            self.prg_size = header[4]
            self.chr_size = header[5]
            self.flags_6 = header[6]
            self.flags_7 = header[7]
            self.mapper = header[8]
            # Not all header data is parsed
            self.prg_rom = reader.read(16*1024*self.prg_size)
            self.chr_rom = reader.read(8*1024*self.chr_size)

    def map(self, addr: int):
        if 0x8000 <= addr <= 0xFFFF:
            if self.prg_size == 1:
                mapped_address = addr & 0x3FFF
            else:
                mapped_address = addr & 0x7FFF
            assert mapped_address < len(self.prg_rom), f"Address {mapped_address:04X} from {addr:04X} is too big"
            return mapped_address
        else:
            raise Exception(f"Address {addr:04X} not in cartridge range")

    def read(self, addr: int) -> int:
        return self.prg_rom[self.map(addr)]

    def get_pattern_table(self, index: Literal[0, 1]) -> PatternTable:
        match index:
            case 0: return PatternTable(self.chr_rom[:16**3])
            case 1: return PatternTable(self.chr_rom[16**3:2*16**3])
