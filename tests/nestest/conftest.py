import pytest

from cartridge import Cartridge
from nes import NES


@pytest.fixture(name="cartridge", scope="module") # Overriding cartridge fixture in conftest
def cartridge_fixture():
    with open('roms/nestest.nes', 'rb') as rom:
        data = list(rom.read())
        data[0x07BD+16+1] = 0xC4 # Fix nes test pointing to wrong jump
        cartridge = Cartridge(bytes(data))
    return cartridge
