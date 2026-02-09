import pytest


with open("data/opcodes.txt") as file:
    codes = file.readlines()


params = []
for line in codes:
    mnemonics, addr_mode, opcode, size, cycles = line.split("|")
    params.append(pytest.param(
        mnemonics.strip(),
        addr_mode.strip(),
        int(opcode.strip()[1:], 16),
        int(size.strip()),
        int(cycles.strip()[0])
    ))


@pytest.mark.parametrize("mnemonics, addr_mode, opcode, size, cycles", params)
def test_opcode_properties(nes, cpu, mnemonics, addr_mode, opcode, size, cycles):
    nes.write(0, opcode)
    assert cpu.fetch() == opcode
    assert cpu.decode(opcode) == (mnemonics, addr_mode)
    assert cpu.execute(mnemonics, addr_mode) == cycles
    assert cpu.r.PC == size
    
        