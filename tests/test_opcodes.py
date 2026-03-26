from pathlib import Path
import json

import pytest


def get_opcode_params():
    with open("data/opcodes.txt") as file:
        codes = file.readlines()
    for line in codes:
        mnemonic, addr_mode, opcode, size, cycles = line.split("|")
        yield pytest.param(
            mnemonic.strip(),
            addr_mode.strip(),
            int(opcode.strip()[1:], 16),
            int(size.strip()),
            int(cycles.strip()[0]),
            id=f"{mnemonic} - {addr_mode}"
        )

@pytest.mark.parametrize("mnemonic, addr_mode, opcode, size, cycles", get_opcode_params())
def test_opcode_properties(nes, cpu, mnemonic, addr_mode, opcode, size, cycles):
    nes.write(0, opcode)
    assert cpu.fetch() == opcode
    assert cpu.decode(opcode) == (mnemonic, addr_mode)
    assert cpu.execute(mnemonic, addr_mode) == cycles
    assert cpu.r.PC == size
