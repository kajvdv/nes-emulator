import pytest

from processor import CPU6502
from render import PPU2c02
from nes import NES




pytest.fixture(name="cpu")
def cpu_fixture(nes: NES):
    return CPU6502(nes)

def test_load_zero_page(nes: NES, cpu: CPU6502):
    nes.write(0x0A, 1)
    assert cpu.zero_page(0x0A) == 1


def test_load_from_zeropage_to_rA(nes: NES, cpu: CPU6502):
    nes.write(0, 0x0A)
    nes.write(1, 0x0C)
    nes.write(2, 0xA5)
    nes.write(3, 0x01)
    cpu.r.PC = 2
    cpu.execute()
    assert cpu.r.A == 0x0C


def test_store_to_memory(nes: NES, cpu: CPU6502):
    nes.write(0, 0x8D) # STA abs
    nes.write(1, 0x11)
    nes.write(2, 0x10)
    cpu.r.A = 1
    cpu.execute()
    assert nes.read(0x1011) == 1


def test_reset_program_counter(nes: NES, cpu: CPU6502):
    lo_pc = nes.read(0xFFFC)
    hi_pc = nes.read(0xFFFD)
    pc = (hi_pc << 8) | lo_pc
    cpu.reset()
    assert cpu.r.PC == pc
    

def test_set_interrupt_disable(cpu: CPU6502):
    cpu.ops.set_interrupt_diable(True)
    assert cpu.r.P == 0b0000_0100


def test_set_interrupt_disable_with_opcode(nes: NES, cpu: CPU6502):
    nes.write(0, 0x78)
    cpu.execute()
    assert cpu.r.P == 0b0000_0100


def test_cpu_read_ppu_status(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    ppu.status = 10
    nes.write(0, 0xAD)
    nes.write(1, 0x02)
    nes.write(2, 0x20)
    cpu.execute()
    assert cpu.r.A == 10


def test_LDA_set_flags(nes: NES, cpu: CPU6502):
    cpu.ops.LDA(0x80)
    assert cpu.get_status_flag(7) == True


def test_branch_if_plus(nes: NES, cpu: CPU6502):
    nes.write(0, 0x10)
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 4

def test_push_and_pull_stack(nes: NES, cpu: CPU6502):
    value = 0x0A
    cpu.push(value)
    assert nes.read(0x01FF) == value
    assert cpu.r.S == 0xFE
    assert cpu.pull() == value
    assert cpu.r.S == 0xFF


def test_JSR_with_RTS(nes: NES, cpu: CPU6502):
    nes.write(0, 0x20)
    nes.write(1, 0x0A)
    nes.write(2, 0x00)
    cpu.execute()
    assert cpu.r.PC == 0x000A
    nes.write(0x0A, 0xE8)
    nes.write(0x0B, 0x60)
    cpu.execute()
    assert cpu.r.X == 1
    cpu.execute()
    assert cpu.r.PC == 3


def test_indirect_x_addressing_mode(nes: NES, cpu: CPU6502):
    nes.write(0x24, 0x10)
    nes.write(0x25, 0x06)
    nes.write(0x0610, 0x0A)
    cpu.r.X = 0x04
    assert cpu.indirect_x(0x20) == 0x0A


def test_indirect_y_addressing_mode(nes: NES, cpu: CPU6502):
    cpu.r.Y = 0x04
    nes.write(0x20, 0x01)
    nes.write(0x21, 0x06)
    nes.write(0x0605, 0x0A)
    assert cpu.indirect_y(0x20) == 0x0A


# --- NOP ---

def test_nop(nes: NES, cpu: CPU6502):
    nes.write(0, 0xEA)
    cpu.execute()
    assert cpu.r.PC == 1  # Only advances PC by 1


# --- Flag operations ---

def test_clc(nes: NES, cpu: CPU6502):
    cpu.ops.SEC()
    assert cpu.get_carry() == True
    nes.write(0, 0x18)  # CLC
    cpu.execute()
    assert cpu.get_carry() == False


def test_sec(nes: NES, cpu: CPU6502):
    nes.write(0, 0x38)  # SEC
    cpu.execute()
    assert cpu.get_carry() == True


def test_cli(nes: NES, cpu: CPU6502):
    cpu.ops.SEI()
    assert cpu.get_status_flag(2) == True
    nes.write(0, 0x58)  # CLI
    cpu.execute()
    assert cpu.get_status_flag(2) == False


def test_clv(nes: NES, cpu: CPU6502):
    cpu.ops.set_status_flag(6, True)
    assert cpu.get_overflow() == True
    nes.write(0, 0xB8)  # CLV
    cpu.execute()
    assert cpu.get_overflow() == False


# --- Register transfers ---

def test_tax(nes: NES, cpu: CPU6502):
    cpu.r.A = 0x42
    nes.write(0, 0xAA)  # TAX
    cpu.execute()
    assert cpu.r.X == 0x42


def test_tay(nes: NES, cpu: CPU6502):
    cpu.r.A = 0x42
    nes.write(0, 0xA8)  # TAY
    cpu.execute()
    assert cpu.r.Y == 0x42


def test_txa(nes: NES, cpu: CPU6502):
    cpu.r.X = 0x42
    nes.write(0, 0x8A)  # TXA
    cpu.execute()
    assert cpu.r.A == 0x42


def test_tya(nes: NES, cpu: CPU6502):
    cpu.r.Y = 0x42
    nes.write(0, 0x98)  # TYA
    cpu.execute()
    assert cpu.r.A == 0x42


def test_tsx(nes: NES, cpu: CPU6502):
    cpu.r.S = 0xFD
    nes.write(0, 0xBA)  # TSX
    cpu.execute()
    assert cpu.r.X == 0xFD


def test_tax_sets_zero_flag(nes: NES, cpu: CPU6502):
    cpu.r.A = 0
    nes.write(0, 0xAA)  # TAX
    cpu.execute()
    assert cpu.get_zero() == True


def test_tax_sets_negative_flag(nes: NES, cpu: CPU6502):
    cpu.r.A = 0x80
    nes.write(0, 0xAA)  # TAX
    cpu.execute()
    assert cpu.get_negative() == True


# --- Stack operations ---

def test_pha(nes: NES, cpu: CPU6502):
    cpu.r.A = 0x42
    nes.write(0, 0x48)  # PHA
    cpu.execute()
    assert nes.read(0x01FF) == 0x42
    assert cpu.r.S == 0xFE


def test_pla(nes: NES, cpu: CPU6502):
    cpu.push(0x42)
    nes.write(0, 0x68)  # PLA
    cpu.execute()
    assert cpu.r.A == 0x42


def test_pla_sets_flags(nes: NES, cpu: CPU6502):
    cpu.push(0x00)
    nes.write(0, 0x68)  # PLA
    cpu.execute()
    assert cpu.r.A == 0x00
    assert cpu.get_zero() == True


def test_php_plp(nes: NES, cpu: CPU6502):
    cpu.r.P = 0b1100_0011
    nes.write(0, 0x08)  # PHP
    nes.write(1, 0x28)  # PLP
    cpu.execute()
    # PHP pushes P with bits 4 and 5 set
    cpu.r.P = 0
    cpu.execute()
    # PLP restores P but ignores bits 4 and 5
    assert cpu.r.P & 0xCF == 0b1100_0011 & 0xCF


# --- JMP ---

def test_jmp_absolute(nes: NES, cpu: CPU6502):
    nes.write(0, 0x4C)  # JMP abs
    nes.write(1, 0x00)
    nes.write(2, 0x06)
    cpu.execute()
    assert cpu.r.PC == 0x0600


def test_jmp_indirect(nes: NES, cpu: CPU6502):
    nes.write(0, 0x6C)  # JMP indirect
    nes.write(1, 0x10)
    nes.write(2, 0x00)
    nes.write(0x10, 0x00)
    nes.write(0x11, 0x06)
    cpu.execute()
    assert cpu.r.PC == 0x0600


# --- Branch instructions ---

def test_bcc_taken(nes: NES, cpu: CPU6502):
    # Carry is clear by default
    nes.write(0, 0x90)  # BCC
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 4


def test_bcc_not_taken(nes: NES, cpu: CPU6502):
    cpu.ops.SEC()
    nes.write(0, 0x90)  # BCC
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 2  # Just past the operand


def test_bcs_taken(nes: NES, cpu: CPU6502):
    cpu.ops.SEC()
    nes.write(0, 0xB0)  # BCS
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 4


def test_bmi_taken(nes: NES, cpu: CPU6502):
    cpu.ops.set_negative(0x80)  # Set negative flag
    nes.write(0, 0x30)  # BMI
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 4


def test_bvc_taken(nes: NES, cpu: CPU6502):
    # Overflow is clear by default
    nes.write(0, 0x50)  # BVC
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 4


def test_bvs_taken(nes: NES, cpu: CPU6502):
    cpu.ops.set_status_flag(6, True)  # Set overflow
    nes.write(0, 0x70)  # BVS
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r.PC == 4


# --- AND ---

def test_and_immediate(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xFF
    nes.write(0, 0x29)  # AND imm
    nes.write(1, 0x0F)
    cpu.execute()
    assert cpu.r.A == 0x0F


def test_and_zero_page(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xFF
    nes.write(0, 0x25)  # AND zero
    nes.write(1, 0x10)
    nes.write(0x10, 0x0F)
    cpu.execute()
    assert cpu.r.A == 0x0F


def test_and_absolute(nes: NES, cpu: CPU6502):
    cpu.r.A = 0b1010_1010
    nes.write(0, 0x2D)  # AND abs
    nes.write(1, 0x00)
    nes.write(2, 0x06)
    nes.write(0x0600, 0b1111_0000)
    cpu.execute()
    assert cpu.r.A == 0b1010_0000


def test_and_sets_zero_flag(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xF0
    nes.write(0, 0x29)  # AND imm
    nes.write(1, 0x0F)
    cpu.execute()
    assert cpu.r.A == 0x00
    assert cpu.get_zero() == True


# --- ORA ---

def test_ora_immediate(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xF0
    nes.write(0, 0x09)  # ORA imm
    nes.write(1, 0x0F)
    cpu.execute()
    assert cpu.r.A == 0xFF


def test_ora_zero_page(nes: NES, cpu: CPU6502):
    cpu.r.A = 0x00
    nes.write(0, 0x05)  # ORA zero
    nes.write(1, 0x10)
    nes.write(0x10, 0x42)
    cpu.execute()
    assert cpu.r.A == 0x42


# --- EOR ---

def test_eor_immediate(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xFF
    nes.write(0, 0x49)  # EOR imm
    nes.write(1, 0x0F)
    cpu.execute()
    assert cpu.r.A == 0xF0


def test_eor_zero_page(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xFF
    nes.write(0, 0x45)  # EOR zero
    nes.write(1, 0x10)
    nes.write(0x10, 0xFF)
    cpu.execute()
    assert cpu.r.A == 0x00
    assert cpu.get_zero() == True


# --- BIT ---

def test_bit_zero_page(nes: NES, cpu: CPU6502):
    cpu.r.A = 0xFF
    nes.write(0, 0x24)  # BIT zero
    nes.write(1, 0x10)
    nes.write(0x10, 0xC0)
    cpu.execute()
    assert cpu.get_negative() == True  # Bit 7 of memory value
    assert cpu.get_overflow() == True  # Bit 6 of memory value
    assert cpu.get_zero() == False     # A & M != 0


def test_bit_sets_zero(nes: NES, cpu: CPU6502):
    cpu.r.A = 0x0F
    nes.write(0, 0x24)  # BIT zero
    nes.write(1, 0x10)
    nes.write(0x10, 0xF0)
    cpu.execute()
    assert cpu.get_zero() == True      # A & M == 0
    assert cpu.get_negative() == True  # Bit 7 of memory value
    assert cpu.get_overflow() == True  # Bit 6 of memory value