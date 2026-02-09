import pytest

from cartridge import Cartridge
from nes import NES, FrameListener
from screen import Screen

from mocks import MockScreen

@pytest.fixture(name="cartridge")
def cartridge_fixture():
    header = b'NES\x1A\x01\x01' + bytes(10)
    prg_rom = bytes(16 * 1024)

    test_tile = b"\x80\x80\x00\x00\x00\x00\x00\x00\x80\x80\x00\x00\x00\x00\x00\x00"
    chr_rom = test_tile + bytes(8 * 1024 - len(test_tile))

    cartridge = Cartridge(header + prg_rom + chr_rom)
    return cartridge


@pytest.fixture(name='screen', scope='function')
def screen_fixture():
    screen = MockScreen()
    yield screen

@pytest.fixture(name='nes')
def nes_fixture(cartridge: Cartridge):
    nes = NES(cartridge)
    return nes


@pytest.fixture(name="cpu")
def cpu_fixture(nes: NES):
    return nes.cpu

@pytest.fixture(name="ppu")
def ppu_fixture(nes: NES):
    return nes.ppu
