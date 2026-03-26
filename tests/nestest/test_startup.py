import pytest


def test_load_ppu_status(nes, cpu):
    cpu.r.PC = 0xC009
    cpu.step()
    cpu.step()
    assert cpu.r.PC == 0xC009, f"{cpu.r.PC:04X}"


def test_nmi_handler(nes, cpu):
    nes.ppu.status = 0x80
    nes.reset()