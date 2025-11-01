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
    cpu.r_PC = 2
    cpu.execute()
    assert cpu.r_A == 0x0C


def test_store_to_memory(nes: NES, cpu: CPU6502):
    nes.write(0, 0x8D) # STA abs
    nes.write(1, 0x11)
    nes.write(2, 0x10)
    cpu.r_A = 1
    cpu.execute()
    assert nes.read(0x1011) == 1


def test_reset_program_counter(nes: NES, cpu: CPU6502):
    lo_pc = nes.read(0xFFFC)
    hi_pc = nes.read(0xFFFD)
    pc = (hi_pc << 8) | lo_pc
    cpu.reset()
    assert cpu.r_PC == pc
    

def test_set_interrupt_disable(cpu: CPU6502):
    cpu.set_interrupt_diable(True)
    assert cpu.r_P == 0b0000_0100


def test_set_interrupt_disable_with_opcode(nes: NES, cpu: CPU6502):
    nes.write(0, 0x78)
    cpu.execute()
    assert cpu.r_P == 0b0000_0100


def test_cpu_read_ppu_status(nes: NES, cpu: CPU6502, ppu: PPU2c02):
    ppu.status = 10
    nes.write(0, 0xAD)
    nes.write(1, 0x02)
    nes.write(2, 0x20)
    cpu.execute()
    assert cpu.r_A == 10


def test_LDA_set_flags(nes: NES, cpu: CPU6502):
    cpu.LDA(0x80)
    assert cpu.get_status_flag(7) == True


def test_branch_if_plus(nes: NES, cpu: CPU6502):
    nes.write(0, 0x10)
    nes.write(1, 0x02)
    cpu.execute()
    assert cpu.r_PC == 4

def test_push_and_pull_stack(nes: NES, cpu: CPU6502):
    value = 0x0A
    cpu.push(value)
    assert nes.read(0x01FF) == value
    assert cpu.r_S == 0xFE
    assert cpu.pull() == value
    assert cpu.r_S == 0xFF


def test_JSR_with_RTS(nes: NES, cpu: CPU6502):
    nes.write(0, 0x20)
    nes.write(1, 0x0A)
    nes.write(2, 0x00)
    cpu.execute()
    assert cpu.r_PC == 0x000A
    nes.write(0x0A, 0xE8)
    nes.write(0x0B, 0x60)
    cpu.execute()
    assert cpu.r_X == 1
    cpu.execute()
    assert cpu.r_PC == 3


def test_indirect_x_addressing_mode(nes: NES, cpu: CPU6502):
    nes.write(0x24, 0x10)
    nes.write(0x25, 0x06)
    nes.write(0x0610, 0x0A)
    cpu.r_X = 0x04
    assert cpu.indirect_x(0x20) == 0x0A


def test_indirect_y_addressing_mode(nes: NES, cpu: CPU6502):
    cpu.r_Y = 0x04
    nes.write(0x20, 0x01)
    nes.write(0x21, 0x06)
    nes.write(0x0605, 0x0A)
    assert cpu.indirect_y(0x20) == 0x0A