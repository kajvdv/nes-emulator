import pytest

from cartridge import Cartridge
from nes import NES
from screen import Screen

@pytest.fixture(name="cartridge")
def cartridge_fixture():
    cartridge = Cartridge(b'NES\x1A\x01\x01' + bytes(1024*100))
    return cartridge

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


@pytest.fixture(name='screen', scope='function')
def screen_fixture():
    screen = Screen()
    yield screen
