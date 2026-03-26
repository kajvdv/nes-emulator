# A set of unit tests to make the nestest rom work.
# Upload the rom in a disassambler and remove the header
# This will get the right mapping between location and address

import pytest

from nes import NES, FrameListener
from processor import CPU6502
from cartridge import Cartridge
from render import PPU2c02

from utils import save_frame_as_image
from mocks import MockScreen


@pytest.fixture(autouse=True)
def menu_frame(nes: NES, screen: MockScreen):
    nes.ppu.status = 0x80
    nes.reset()
    # while screen.render_count < 4:
    #     nes.execute()
    nes.get_next_frame()
    nes.get_next_frame()
    nes.get_next_frame()
    return nes.get_next_frame()


def test_displaying_menu(menu_frame):
    save_frame_as_image(menu_frame, 256, 240, "test_displaying_menu.png")
    

def test_receive_user_input(nes: NES, screen: MockScreen):
    # lo_pc = nes.read(0xFFFA)
    # hi_pc = nes.read(0xFFFB)
    # pc = (hi_pc << 8) | lo_pc
    # print(f"pc is {(pc):04X}")
    # nes.cpu.r.PC = pc
    # nes.write(0xD4, 0x04)
    nes.cpu.nmi()
    frame = nes.get_next_frame()
    for _ in range(10):
        nes.cpu.nmi()
        frame = nes.get_next_frame()
    save_frame_as_image(frame, 256, 240, "test_receive_user_input.png")


# def test_set_vram_address(nes: NES, cpu: CPU6502, ppu: PPU2c02):
#     '''
#     0024   A2 20                LDX #$20
#     0026   8E 06 20             STX $2006
#     0029   A2 00                LDX #$00
#     002B   8E 06 20             STX $2006
#     '''
#     nes.reset()
#     cpu.r.PC = 0x8024
#     for _ in range(4):
#         cpu.execute()
#     assert ppu.vram_addr == 0x2000


# def test_fill_vram_with_data(nes: NES, cpu: CPU6502, ppu: PPU2c02):
#     '''
#     002E   A2 00                LDX #$00
#     0030   A0 0F                LDY #$0F
#     0032   A9 00                LDA #$00
#     0034   8D 07 20   L0034     STA $2007
#     0037   CA                   DEX
#     0038   D0 FA                BNE L0034
#     003A   88                   DEY
#     003B   D0 F7                BNE L0034
#     '''
#     nes.reset()
#     cpu.r.PC = 0x802E
#     ppu.vram_addr = 0x2000
#     while cpu.r.PC != 0x803B + 2:
#         cpu.execute()

# def test_fill_palette_ram_indexes(nes: NES, cpu: CPU6502):
#     '''
#     003D   A9 3F                LDA #$3F
#     003F   8D 06 20             STA $2006
#     0042   A9 00                LDA #$00
#     0044   8D 06 20             STA $2006
#     0047   A2 00                LDX #$00
#     0049   BD 78 FF   L0049     LDA $FF78,X
#     004C   8D 07 20             STA $2007
#     004F   E8                   INX
#     0050   E0 20                CPX #$20
#     0052   D0 F5                BNE L0049
#     '''
#     nes.reset()
#     start_PC = cpu.r.PC
#     cpu.r.PC += 0x39
#     while cpu.r.PC != start_PC + 0x50:
#         cpu.execute()

# def test_some_instructions(nes: NES, cpu: CPU6502, ppu: PPU2c02):
#     '''
#     0054   A9 C0                LDA #$C0
#     0056   8D 17 40             STA $4017
#     0059   A9 00                LDA #$00
#     005B   8D 15 40             STA $4015
#     005E   A9 78                LDA #$78
#     0060   85 D0                STA L00D0
#     0062   A9 FB                LDA #$FB
#     0064   85 D1                STA $D1
#     0066   A9 7F                LDA #$7F
#     0068   85 D3                STA $D3
#     006A   A0 00                LDY #$00
#     006C   8C 06 20             STY $2006
#     006F   8C 06 20             STY $2006
#     0072   A9 00                LDA #$00
#     0074   85 D7                STA $D7
#     0076   A9 07                LDA #$07
#     0078   85 D0                STA L00D0
#     007A   A9 C3                LDA #$C3
#     007C   85 D1                STA $D1
#     '''
#     nes.reset()
#     cpu.r.PC = 0x8054
#     while cpu.r.PC != 0x807C + 2:
#         cpu.execute()
#     assert ppu.vram_addr == 0
#     assert nes.read(0xD0) == 0x07
#     assert nes.read(0xD1) == 0xC3
#     assert nes.read(0xD3) == 0x7F

# def test_jump_to_somewhere(nes: NES, cpu: CPU6502):
#     '''
#     007E   20 A7 C2             JSR $C2A7
#     '''
#     nes.reset()
#     # start_PC = cpu.r.PC
#     cpu.r.PC += 0x7A
#     source = cpu.r.PC + 2
#     # while cpu.r.PC != start_PC + 0x7A:
#     cpu.execute()
#     assert nes.read(0x01FF) == source >> 8
#     assert nes.read(0x01FE) == source & 0x00FF
#     assert cpu.r.PC == 0xC2A7

# def test_write_more_stuff_to_vram(nes: NES, cpu: CPU6502):
#     '''
#     02A7   A9 00                LDA #$00
#     02A9   8D 00 20             STA $2000
#     02AC   8D 01 20             STA $2001
#     02AF   20 ED C2             JSR $C2ED
#     02B2   A9 20                LDA #$20
#     02B4   8D 06 20             STA $2006
#     02B7   A0 00                LDY #$00
#     02B9   8C 06 20             STY $2006
#     02BC   A2 20      L02BC     LDX #$20
#     02BE   B1 D0      L02BE     LDA (L00D0),Y
#     02C0   F0 20                BEQ L02E2
#     02C2   C9 FF                CMP #$FF
#     02C4   F0 0D                BEQ L02D3
#     02C6   8D 07 20             STA $2007
#     02C9   C8                   INY
#     02CA   D0 02                BNE L02CE
#     02CC   E6 D1                INC $D1
#     02CE   CA         L02CE     DEX
#     02CF   D0 ED                BNE L02BE
#     02D1   F0 E9                BEQ L02BC
#     02D3   C8         L02D3     INY
#     02D4   D0 02                BNE L02D8
#     02D6   E6 D1                INC $D1
#     02D8   A9 20      L02D8     LDA #$20
#     02DA   8D 07 20             STA $2007
#     02DD   CA                   DEX
#     02DE   D0 F8                BNE L02D8
#     02E0   F0 DA                BEQ L02BC
#     02E2   A9 80      L02E2     LDA #$80
#     02E4   8D 00 20             STA $2000
#     02E7   A9 0E                LDA #$0E
#     02E9   8D 01 20             STA $2001
#     02EC   60                   RTS
#     '''
#     nes.reset()
#     cpu.r.PC = 0x82A7
#     nes.write(0xD0, 0x07)
#     nes.write(0xD1, 0xC3)
#     nes.write(0xD3, 0x7F)
#     while cpu.r.PC != 0x82E9 + 3:
#         cpu.execute()

#     print("points to ", nes.read(0xC307))


# def test_write_into_vram(nes: NES, cpu: CPU6502, ppu: PPU2c02):
#     '''
#     0261   A5 D7                LDA $D7
#     0263   18                   CLC
#     0264   69 04                ADC #$04
#     0266   A8                   TAY
#     0267   A9 84                LDA #$84
#     0269   8D 00 20             STA $2000
#     026C   A9 20                LDA #$20
#     026E   8D 06 20             STA $2006
#     0271   A9 02                LDA #$02
#     0273   8D 06 20             STA $2006
#     0276   A9 20      L0276     LDA #$20
#     0278   88                   DEY
#     0279   C8                   INY
#     027A   D0 02                BNE L027E
#     027C   A9 2A                LDA #$2A
#     027E   8D 07 20   L027E     STA $2007
#     0281   88                   DEY
#     0282   CA                   DEX
#     0283   D0 F1                BNE L0276
#     0285   A9 80                LDA #$80
#     0287   8D 00 20             STA $2000
#     028A   4C 94 C2             JMP $C294
#     028D   A5 D2                LDA $D2
#     028F   C5 D2      L028F     CMP $D2
#     0291   F0 FC                BEQ L028F
#     0293   60                   RTS
#     '''


# def test_run_nestest_instructions(nes: NES, cpu: CPU6502, ppu: PPU2c02):
#     nes.reset()
#     ppu.status = 0x80 # Set the vblack register to make program continue
#     # for _ in range(19740):
#     for _ in range(2000):
#         cpu.execute()
#     # assert 0