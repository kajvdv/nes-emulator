import pytest


from nes import NES
from processor import CPU6502
from cartridge import Cartridge


@pytest.fixture(name="cpu", scope="class")
def cpu_fixture(nes: NES):
    return nes.cpu


@pytest.fixture(name='nes', scope="class")
def nes_fixture(cartridge: Cartridge):
    nes = NES(cartridge)
    assert nes.read(0x8000) == 0x4c, "Nestest rom was not inserted"
    return nes


def test_pre_test_instructions(nes: NES, cpu: CPU6502):
    cpu.r.PC = 0xC5F5
    cpu.step()
    cpu.step()
    cpu.step()
    cpu.step()
    

class TestBranch:
    PC_START = 0xC72D
    
    @pytest.fixture(autouse=True, scope="class")
    def set_PC_fixture(self, cpu):
        cpu.r.PC = self.PC_START
        return

    @pytest.fixture(autouse=True, scope="function")
    def execute_test(self, nes: NES, cpu: CPU6502, PC):
        print(f"Start test with PC: {cpu.r.PC:02X}")
        assert cpu.r.PC == PC, "Start stared at wrong position"
        current_opcode = cpu.fetch()
        while True:
            mnemonic, addr_mode = cpu.decode(current_opcode)
            print(f"Executed {(cpu.r.PC-1):04X}: 0x{current_opcode:02X} ({mnemonic}) with addr mode {addr_mode}")
            cpu.execute(mnemonic, addr_mode)
            current_opcode = cpu.fetch()
            if current_opcode == 0xEA or cpu.r.PC == self.PC_START + 1:
                break
        cpu.r.PC -= 1 # Revert fetch


    @pytest.mark.parametrize("PC", [
        pytest.param(0xC72D, id="001h_BCS_failed_to_branch"),
        pytest.param(0xC735, id="002h_BCS_branched_when_it_shouldnt_have"),
        pytest.param(0xC740, id="003h_BCC_branched_when_it_shouldnt_have"),
        pytest.param(0xC74B, id="004h_BCC_failed_to_branch"),
        pytest.param(0xC753, id="005h_BEQ_failed_to_branch"),
        pytest.param(0xC75C, id="006h_BEQ_branched_when_it_shouldnt_have"),
        pytest.param(0xC768, id="007h_BNE_failed_to_branch"),
        pytest.param(0xC771, id="008h_BNE_branched_when_it_shouldnt_have"),
        pytest.param(0xC77D, id="009h_BVS_failed_to_branch"),
        pytest.param(0xC78A, id="00Ah_BVC_branched_when_it_shouldnt_have"),
        pytest.param(0xC796, id="00Bh_BVC_failed_to_branch"),
        pytest.param(0xC7A3, id="00Ch_BVS_branched_when_it_shouldnt_have"),
        pytest.param(0xC7AF, id="00Dh_BPL_failed_to_branch"),
        pytest.param(0xC7B8, id="00Eh_BPL_branched_when_it_shouldnt_have"),
        pytest.param(0xC7C4, id="00Fh_BMI_failed_to_branch"),
        pytest.param(0xC7CD, id="010h_BMI_branched_when_it_shouldnt_have"),
    ])
    def test_nes_(self, nes: NES, PC):
        assert nes.read(0x00) == 0

    
    # def test_001h_BCS_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_002h_BCS_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_003h_BCC_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_004h_BCC_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_005h_BEQ_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_006h_BEQ_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_007h_BNE_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_008h_BNE_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_009h_BVS_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_00Ah_BVC_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_00Bh_BVC_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_00Ch_BVS_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_00Dh_BPL_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_00Eh_BPL_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_00Fh_BMI_failed_to_branch(self, nes: NES):
    #     assert nes.read(0x00) == 0

    # def test_010h_BMI_branched_when_it_shouldnt_have(self, nes: NES):
    #     assert nes.read(0x00) == 0
