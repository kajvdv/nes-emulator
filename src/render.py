

class PatternTile:
    def __init__(self, data: bytes):
        # print(data)
        assert len(data) == 16, f"Length was {len(data)}"
        self.data = data

    def get_color_indexes(self) -> list[list[int]]:
        lsb_plane = self.data[:8]
        msb_plane = self.data[8:]
        indexes: list[list[int]] = []
        for l_byte, m_byte in zip(lsb_plane, msb_plane):
            row: list[int] = []
            for l_bit, m_bit in zip(f"{l_byte:08b}", f"{m_byte:08b}"):
                index = (int(m_bit) << 1) | int(l_bit)
                row.append(index)
            indexes.append(row)
        return indexes
        

class PatternTable:
    def __init__(self, data: bytes):
        assert len(data) == 16*16*16 # 16 rows of 16 tiles that are 16 bytes each
        self.tiles: list[PatternTile] = []
        tile_bytes = data[:16]
        for i, byte in enumerate(data, start=16):
            if i % 16 == 0:
                tile = PatternTile(tile_bytes)
                self.tiles.append(tile)
                tile_bytes = b""
            tile_bytes += bytes([byte])
        tile = PatternTile(tile_bytes)
        self.tiles.append(tile)


class Palette:
    def __init__(self):
        pass

    def get_color(self, index: int):
        return (255, 255, 255) if index == 3 else (0, 0, 0)
        

class NameTable:
    def __init__(self):
        self.data = [
            [PatternTile(b"\x00"*16) for _ in range(32)] 
            for _ in range(30)
        ] # Each name table contains 32 rows of 30 tiles

    def resolve_frame(self, palette: Palette):
        frame = [
            [(0, 0, 0) for _ in range(256)]
            for _ in range(240)
        ]
        for y, row in enumerate(self.data):
            for x, tile in enumerate(row):
                color_indexes = tile.get_color_indexes()
                for t_y, color_index_row in enumerate(color_indexes):
                    for t_x, index in enumerate(color_index_row):
                        frame[y*8+t_y][x*8+t_x] = palette.get_color(index)
        return frame

    def write_tile(self, tile: PatternTile, col: int, row: int):
        self.data[row][col] = tile
                

class Frame:
    ...
        

class PPU2c02:
    def __init__(self, patterntables: tuple[PatternTable, PatternTable]):
        self.nametables = [NameTable(), NameTable()]
        self.palette = Palette()
        self.patterntables = patterntables
        self.r_W = False
        self.vram_addr = 0
        self.status = 0
        self.control = 0
        self.mask = 0

    def get_status(self):
        self.r_W = False
        return self.status

    def set_control(self, value: int):
        self.control = value
    
    def set_mask(self, value: int):
        self.mask = value

    def resolve_frame(self):
        return self.nametables[0].resolve_frame(self.palette)

    def write_tile(self, n_x: int, n_y: int, pattern_index: int):
        tile = self.patterntables[0].tiles[pattern_index]
        self.nametables[0].write_tile(tile, n_x, n_y)

    def write_addr(self, value: int):
        if self.r_W == False:
            self.vram_addr = value << 8
        else:
            self.vram_addr |= value
            print(f"VRAM addr set to {self.vram_addr:04X}")
        self.r_W = True

    def write_data(self, value: int):
        print(f"Writing 0x{value:02X} to 0x{self.vram_addr=:04X}")
        if 0x2000 <= self.vram_addr < 0x23C0:    
            index = self.vram_addr & 0x1FFF
            col = index % 32
            row = index // 32
            print(f"{index=:04X} {col=} {row=}")
            tile = self.patterntables[0].tiles[value]
            self.nametables[0].write_tile(tile, col, row)
        self.vram_addr = (self.vram_addr + 1) & 0x3FFF

    def read_vram(self, addr: int):
        ...
