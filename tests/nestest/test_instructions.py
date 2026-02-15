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
    

class BaseTest:
    PC_START = 0
    
    @pytest.fixture(autouse=True, scope="class")
    def set_PC_fixture(self, cpu):
        cpu.r.PC = self.PC_START
        # assert cpu.read(cpu.r.PC == 0xEA)
        return

    @pytest.fixture(autouse=True, scope="function")
    def execute_test(self, nes: NES, cpu: CPU6502, PC):
        print(f"Start test with PC: {cpu.r.PC:02X}")
        assert cpu.r.PC == PC, (
            f"Start stared at wrong position."
            f"PC should be {PC:04X}, but was {cpu.r.PC:04X}"
        )
        current_opcode = cpu.fetch()
        while True:
            mnemonic, addr_mode = cpu.decode(current_opcode)
            print(f"Executed {(cpu.r.PC-1):04X}: 0x{current_opcode:02X} ({mnemonic}) with addr mode {addr_mode}")
            cpu.execute(mnemonic, addr_mode)
            current_opcode = cpu.fetch()
            if current_opcode == 0xEA:
                cpu.r.PC -= 1 # Revert fetch
                break
            # Prevent underflowing when pulling addr with RTS
            if current_opcode == 0x60 and cpu.r.S == 0xFF:
                break


class TestBranch(BaseTest):
    PC_START = 0xC72D

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


class TestFlag(BaseTest):
    PC_START = 0xC7DB

    @pytest.mark.parametrize("PC", [
        pytest.param(0xC7DB, id="011h - PHP/flags failure (bits set) "),
        pytest.param(0xC7F3, id="012h - PHP/flags failure (bits clear)"),
        pytest.param(0xC80A, id="013h - PHP/flags failure (misc bit states)"),
        pytest.param(0xC821, id="014h - PLP/flags failure (misc bit states)"),
        pytest.param(0xC835, id="015h - PLP/flags failure (misc bit states)"),
        pytest.param(0xC849, id="016h - PHA/PLA failure (PLA didn't affect Z and N properly)"),
        pytest.param(0xC867, id="017h - PHA/PLA failure (PLA didn't affect Z and N properly)"),
    ])
    def test_nes_(self, nes: NES, PC):
        assert nes.read(0x00) == 0


class TestImmi(BaseTest):
    PC_START = 0xC885

    @pytest.mark.parametrize("PC", [
        pytest.param(0xC885, id="018h - ORA # failure"),
        pytest.param(0xC8A2, id="019h - ORA # failure"),
        pytest.param(0xC8B8, id="01Ah - AND # failure"),
        pytest.param(0xC8CF, id="01Bh - AND # failure"),
        pytest.param(0xC8E7, id="01Ch - EOR # failure"),
        pytest.param(0xC900, id="01Dh - EOR # failure"),
        pytest.param(0xC916, id="01Eh - ADC # failure (overflow/carry problems)"),
        pytest.param(0xC92F, id="01Fh - ADC # failure (decimal mode was turned on)"),
        pytest.param(0xC949, id="020h - ADC # failure"),
        pytest.param(0xC962, id="021h - ADC # failure"),
        pytest.param(0xC97B, id="022h - ADC # failure"),
        pytest.param(0xC991, id="023h - LDA # failure (didn't set N and Z correctly)"),
        pytest.param(0xC9A5, id="024h - LDA # failure (didn't set N and Z correctly)"),
        pytest.param(0xC9BA, id="025h - CMP # failure (messed up flags)"),
        pytest.param(0xC9D0, id="026h - CMP # failure (messed up flags)"),
        pytest.param(0xC9E3, id="027h - CMP # failure (messed up flags)"),
        pytest.param(0xC9F3, id="028h - CMP # failure (messed up flags)"),
        pytest.param(0xCA05, id="029h - CMP # failure (messed up flags)"),
        pytest.param(0xCA15, id="02Ah - CMP # failure (messed up flags)"),
        pytest.param(0xCA25, id="02Bh - CPY # failure (messed up flags)"),
        pytest.param(0xCA35, id="02Ch - CPY # failure (messed up flags)"),
        pytest.param(0xCA4B, id="02Dh - CPY # failure (messed up flags)"),
        pytest.param(0xCA5E, id="02Eh - CPY # failure (messed up flags)"),
        pytest.param(0xCA6E, id="02Fh - CPY # failure (messed up flags)"),
        pytest.param(0xCA80, id="030h - CPY # failure (messed up flags)"),
        pytest.param(0xCA90, id="031h - CPY # failure (messed up flags)"),
        pytest.param(0xCAA0, id="032h - CPX # failure (messed up flags)"),
        pytest.param(0xCAB0, id="033h - CPX # failure (messed up flags)"),
        pytest.param(0xCAC6, id="034h - CPX # failure (messed up flags)"),
        pytest.param(0xCAD9, id="035h - CPX # failure (messed up flags)"),
        pytest.param(0xCAE9, id="036h - CPX # failure (messed up flags)"),
        pytest.param(0xCAFB, id="037h - CPX # failure (messed up flags)"),
        pytest.param(0xCB0B, id="038h - CPX # failure (messed up flags)"),
        pytest.param(0xCB1B, id="039h - LDX # failure (didn't set N and Z correctly)"),
        pytest.param(0xCB2B, id="03Ah - LDX # failure (didn't set N and Z correctly)"),
        pytest.param(0xCB3F, id="03Bh - LDY # failure (didn't set N and Z correctly)"),
        pytest.param(0xCB54, id="03Ch - LDY # failure (didn't set N and Z correctly)"),
        pytest.param(0xCB68, id="03Dh - compare(s) stored the result in a register (whoops!)"),
        pytest.param(0xCB7D, id="071h - SBC # failure"),
        pytest.param(0xCBDE, id="072h - SBC # failure"),
        pytest.param(0xCC14, id="073h - SBC # failure"),
        pytest.param(0xCC62, id="074h - SBC # failure"),
        pytest.param(0xCCB0, id="075h - SBC # failure"),
    ])
    def test_nes_(self, nes: NES, PC):
        assert nes.read(0x00) == 0


class TestImpl(BaseTest):
    PC_START = 0xCBDE
    
    @pytest.mark.parametrize("PC", [
        pytest.param(0xCBDE, id="03Eh - INX/DEX/INY/DEY did something bad"),
        pytest.param(0xCC14, id="03Fh - INY/DEY messed up overflow or carry"),
        pytest.param(0xCC62, id="040h - INX/DEX messed up overflow or carry"),
        pytest.param(0xCCB0, id="041h - TAY did something bad (changed wrong regs, messed up flags)"),
        pytest.param(0xCCEF, id="042h - TAX did something bad (changed wrong regs, messed up flags)"),
        pytest.param(0xCD2E, id="043h - TYA did something bad (changed wrong regs, messed up flags)"),
        pytest.param(0xCD6D, id="044h - TXA did something bad (changed wrong regs, messed up flags)"),
        pytest.param(0xCDAC, id="045h - TXS didn't set flags right, or TSX touched flags and it shouldn't have"),
    ])
    def test_nes_(self, nes: NES, PC):
        assert nes.read(0x00) == 0
        

class TestStack(BaseTest):
    PC_START = 0xCDF8

    @pytest.fixture(autouse=True, scope="class")
    def set_PC_fixture(self, cpu):
        cpu.r.PC = self.PC_START
        cpu.step()
        cpu.step()
        cpu.step()
        cpu.step()
        return

    @pytest.mark.parametrize("PC", [
        pytest.param(0xCE00, id="046h - wrong data popped, or data not in right location on stack"),
        pytest.param(0xCE33, id="047h - JSR didn't work as expected"),
        pytest.param(0xCE5F, id="048h - RTS/JSR shouldn't have affected flags"),
        pytest.param(0xCE9D, id="049h - RTI/RTS didn't work right when return addys/data were manually pushed"),
    ])
    def test_nes_(self, nes: NES, PC):
        test_number = nes.read(0x00)
        assert test_number == 0, f"Test {test_number:02X}h failed"


class TestAccu(BaseTest):
    PC_START = 0xCEEE

    @pytest.fixture(autouse=True, scope="class")
    def set_PC_fixture(self, cpu):
        cpu.r.PC = self.PC_START
        cpu.step()
        cpu.step()
        cpu.step()
        cpu.step()
        return

    @pytest.mark.parametrize("PC", [
        pytest.param(0xCEF6, id="04Ah - LSR A  failed"),
        pytest.param(0xCF20, id="04Bh - ASL A  failed"),
        pytest.param(0xCF4B, id="04Ch - ROR A  failed"),
        pytest.param(0xCF76, id="04Dh - ROL A  failed"),
    ])
    def test_nes_(self, nes: NES, PC):
        test_number = nes.read(0x00)
        assert test_number == 0, f"Test {test_number:02X}h failed"