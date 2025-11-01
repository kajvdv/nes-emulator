# A set of unit tests to make the nestest rom work.


import pytest

from nes import NES
from processor import CPU6502
from cartridge import Cartridge
from render import PPU2c02


@pytest.fixture(name="cartridge") # Overriding cartridge fixture in conftest
def cartridge_fixture():
    with open('roms/nestest.nes', 'rb') as rom:
        cartridge = Cartridge(rom.read())
    return cartridge
    

def test_set_vram_address(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    '''
    0020   A2 20                LDX #$20
    0022   8E 06 20             STX $2006
    0025   A2 00                LDX #$00
    0027   8E 06 20             STX $2006'''
    nes.reset()
    cpu.r_PC += 0x20
    for _ in range(4):
        cpu.execute()
    assert ppu.vram_addr == 0x2000


def test_fill_vram_with_data(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    '''
    002A   A2 00                LDX #$00
    002C   A0 0F                LDY #$0F
    002E   A9 00                LDA #$00
    0030   8D 07 20   L0030     STA $2007
    0033   CA                   DEX
    0034   D0 FA                BNE L0030
    0036   88                   DEY
    0037   D0 F7                BNE L0030'''
    nes.reset()
    start_PC = cpu.r_PC
    cpu.r_PC += 0x2A
    ppu.vram_addr = 0x2000
    while cpu.r_PC != start_PC + 0x39:
        cpu.execute()

def test_fill_palette_ram_indexes(nes: NES, cpu: CPU6502):
    '''
    0039   A9 3F                LDA #$3F
    003B   8D 06 20             STA $2006
    003E   A9 00                LDA #$00
    0040   8D 06 20             STA $2006
    0043   A2 00                LDX #$00
    0045   BD 78 FF   L0045     LDA $FF78,X
    0048   8D 07 20             STA $2007
    004B   E8                   INX
    004C   E0 20                CPX #$20
    004E   D0 F5                BNE L0045'''
    nes.reset()
    start_PC = cpu.r_PC
    cpu.r_PC += 0x39
    while cpu.r_PC != start_PC + 0x50:
        cpu.execute()

def test_some_instructions(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    '''
    0050   A9 C0                LDA #$C0
    0052   8D 17 40             STA $4017
    0055   A9 00                LDA #$00
    0057   8D 15 40             STA $4015
    005A   A9 78                LDA #$78
    005C   85 D0                STA $D0
    005E   A9 FB                LDA #$FB
    0060   85 D1                STA $D1
    0062   A9 7F                LDA #$7F
    0064   85 D3                STA $D3
    0066   A0 00                LDY #$00
    0068   8C 06 20             STY $2006
    006B   8C 06 20             STY $2006
    006E   A9 00                LDA #$00
    0070   85 D7                STA $D7
    0072   A9 07                LDA #$07
    0074   85 D0                STA $D0
    0076   A9 C3                LDA #$C3
    0078   85 D1                STA $D1'''
    nes.reset()
    start_PC = cpu.r_PC
    cpu.r_PC += 0x50
    while cpu.r_PC != start_PC + 0x7A:
        cpu.execute()
    assert ppu.vram_addr == 0
    assert nes.read(0xD0) == 0x07
    assert nes.read(0xD1) == 0xC3
    assert nes.read(0xD3) == 0x7F

def test_jump_to_somewhere(nes: NES, cpu: CPU6502):
    '''
    007A   20 A7 C2             JSR $C2A7'''
    nes.reset()
    # start_PC = cpu.r_PC
    cpu.r_PC += 0x7A
    source = cpu.r_PC + 2
    # while cpu.r_PC != start_PC + 0x7A:
    cpu.execute()
    assert nes.read(0x01FF) == source >> 8
    assert nes.read(0x01FE) == source & 0x00FF
    assert cpu.r_PC == 0xC2A7

def test_write_more_stuff_to_vram(nes: NES, cpu: CPU6502):
    '''
    02A3   A9 00                LDA #$00
    02A5   8D 00 20             STA $2000
    02A8   8D 01 20             STA $2001
    02AB   20 ED C2             JSR $C2ED
    02AE   A9 20                LDA #$20
    02B0   8D 06 20             STA $2006
    02B3   A0 00                LDY #$00
    02B5   8C 06 20             STY $2006
    02B8   A2 20      L02B8     LDX #$20
    02BA   B1 D0      L02BA     LDA ($D0),Y
    02BC   F0 20                BEQ L02DE
    02BE   C9 FF                CMP #$FF
    02C0   F0 0D                BEQ L02CF
    02C2   8D 07 20             STA $2007
    02C5   C8                   INY
    02C6   D0 02                BNE L02CA
    02C8   E6 D1                INC $D1
    02CA   CA         L02CA     DEX
    02CB   D0 ED                BNE L02BA
    02CD   F0 E9                BEQ L02B8
    02CF   C8         L02CF     INY
    02D0   D0 02                BNE L02D4
    02D2   E6 D1                INC $D1
    02D4   A9 20      L02D4     LDA #$20
    02D6   8D 07 20             STA $2007
    02D9   CA                   DEX
    02DA   D0 F8                BNE L02D4
    02DC   F0 DA                BEQ L02B8
    02DE   A9 80      L02DE     LDA #$80
    02E0   8D 00 20             STA $2000
    02E3   A9 0E                LDA #$0E
    02E5   8D 01 20             STA $2001
    02E8   60                   RTS'''
    nes.reset()
    start_PC = cpu.r_PC
    cpu.r_PC += 0x02A3
    nes.write(0xD0, 0x07)
    nes.write(0xD1, 0xC3)
    nes.write(0xD3, 0x7F)
    while cpu.r_PC != start_PC + 0x02E8:
        cpu.execute()

    print("points to ", nes.read(0xC307))
    assert 0


def test_write_into_vram(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    '''
    0261   A5 D7                LDA $D7
    0263   18                   CLC
    0264   69 04                ADC #$04
    0266   A8                   TAY
    0267   A9 84                LDA #$84
    0269   8D 00 20             STA $2000
    026C   A9 20                LDA #$20
    026E   8D 06 20             STA $2006
    0271   A9 02                LDA #$02
    0273   8D 06 20             STA $2006
    0276   A9 20      L0276     LDA #$20
    0278   88                   DEY
    0279   C8                   INY
    027A   D0 02                BNE L027E
    027C   A9 2A                LDA #$2A
    027E   8D 07 20   L027E     STA $2007
    0281   88                   DEY
    0282   CA                   DEX
    0283   D0 F1                BNE L0276
    0285   A9 80                LDA #$80
    0287   8D 00 20             STA $2000
    028A   4C 94 C2             JMP $C294
    028D   A5 D2                LDA $D2
    028F   C5 D2      L028F     CMP $D2
    0291   F0 FC                BEQ L028F
    0293   60                   RTS'''


def test_run_nestest_instructions(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    nes.reset()
    ppu.status = 0x80 # Set the vblack register to make program continue
    # for _ in range(19740):
    for _ in range(2000):
        cpu.execute()
    assert 0