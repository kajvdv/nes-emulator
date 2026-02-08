import pytest


with open("data/opcodes.txt") as file:
    codes = file.readlines()


params = []
for line in codes:
    line = line.replace("\t\t", "\t")
    line = line.replace("\t\t\t", "\t")
    addr_mode, opcode, size, cycles = line.split("\t")
    params.append(pytest.param(
        addr_mode.strip(),
        int(opcode.strip()[1:], 16),
        int(size),
        int(cycles[0])
    ))


@pytest.mark.parametrize("addr_mode, opcode, size, cycles", params)
def test_opcode_properties(nes, cpu, addr_mode, opcode, size, cycles):
    nes.write(0, opcode)
    assert cpu.execute() == cycles
    assert cpu.r.PC == size
    
        