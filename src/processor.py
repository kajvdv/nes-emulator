from typing import Protocol, Literal
from dataclasses import dataclass, field

class Bus(Protocol):
    def read(self, addr: int) -> int:
        ...
    
    def write(self, addr: int, value: int):
        ...


with open("data/opcodes.txt") as file:
    opcode_lines = file.readlines()

opcodes: list[tuple[str, str, int, int, int]] = []
for opcode in opcode_lines:
    mnemonics, addr_mode, opcode, size, cycles = opcode.split("|")
    opcodes.append((
        mnemonics.strip(),
        addr_mode.strip(),
        int(opcode.strip()[1:], 16),
        int(size.strip()),
        int(cycles.strip()[0])
    ))


OPCODES: dict[int, tuple[str, str]] = {
    opcode: (mnemonics, addr_mode)
    for mnemonics, addr_mode, opcode, *_ in opcodes
}

CYCLES: dict[tuple[str, str], int] = {
    (mnemonics, addr_mode): cycles
    for mnemonics, addr_mode, _opcode, _size, cycles in opcodes
}


@dataclass
class Registers:
    A: int = field(default=0)
    X: int = field(default=0)
    Y: int = field(default=0)
    S: int = field(default=0xFF)
    P: int = field(default=0)
    PC: int = field(default=0)


class CPU6502:
    def __init__(self, nes: Bus):
        self.nes = nes
        self.r = Registers()
        self._pending_pc: int | None = None

    def reset(self):
        lo_pc = self.read(0xFFFC)
        hi_pc = self.read(0xFFFD)
        pc = (hi_pc << 8) | lo_pc
        self.r.PC = pc
        self.r.S = 0xFF

    def read(self, addr: int):
        return self.nes.read(addr & 0xFFFF)

    def write(self, addr: int, value: int):
        self.nes.write(addr & 0xFFFF, value)

    def push(self, value: int):
        addr = self.r.S | 0x0100
        self.write(addr, value & 0xFF)
        # print(f"push: self.write(0x{addr:02X}, 0x{value & 0xFF:02X})")
        self.r.S = (self.r.S - 1) & 0xFF

    def pull(self) -> int:
        self.r.S = (self.r.S + 1) & 0xFF
        addr = self.r.S | 0x0100
        value = self.read(addr)
        # print(f"pull: pulled 0x{value:02X} from 0x{addr:04X}")
        return value
    
    def get_flag(self, flag: Literal["N","V","1","B","D","I","Z","C"]):
        enum = {"N": 7,"V": 6,"1": 5,"B": 4,"D": 3,"I": 2,"Z": 1,"C": 0}
        return bool(self.r.P & (1 << enum[flag]))
    
    def set_flag(self, flag: Literal["N","V","1","B","D","I","Z","C"], value: bool):
        enum = {"N": 7,"V": 6,"1": 5,"B": 4,"D": 3,"I": 2,"Z": 1,"C": 0}
        if value:
            self.r.P |= (1 << enum[flag])
        else:
            self.r.P &= ~(1 << enum[flag])

    def set_status_flags(self,
            N=None,
            V=None,
            D=None,
            I=None,
            Z=None,
            C=None,
    ):
        if N != None:
            self.set_flag("N", N)
        if V != None:
            self.set_flag("V", V)
        if D != None:
            self.set_flag("D", D)
        if I != None:
            self.set_flag("I", I)
        if Z != None:
            self.set_flag("Z", Z)
        if C != None:
            self.set_flag("C", C)
        # print(f"   NV1BDIZC")
        # print(f"P: {self.r.P:08b}")
    
    def branch_off(self, condition, offset):
        if offset & 0x80:
            # If the signed bit is set, the the value should be negative.
            offset = offset - 0x100
        if condition:
            self.r.PC += offset

    def nmi(self):
        self.push(self.r.PC >> 8)
        self.push(self.r.PC & 0xFF)
        self.push(self.r.P & 0b1110_1111)
        lo_pc = self.read(0xFFFA)
        hi_pc = self.read(0xFFFB)
        pc = (hi_pc << 8) | lo_pc
        self.r.PC = pc
    
    def fetch(self) -> int:
        opcode = self.read(self.r.PC)
        self.r.PC += 1
        return opcode

    def decode(self, opcode) -> tuple[str, str]:
        try:
            return OPCODES[opcode]
        except KeyError as e:
            # print(f"Used an illigal opcode {opcode:02X}")
            raise KeyError(hex(e.args[0]))
        
    def execute(self, mnemonic: str, addr_mode: str) -> int:
        print(f"Execute {(self.r.PC-1):04X}: ({mnemonic}) with addr mode {addr_mode}")
        value = -1
        addr = -1
        match addr_mode:
            case "accu":
                value = self.r.A
            case "immi":
                value = self.read(self.r.PC)
                self.r.PC += 1
            case "zero":
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
            case "zerx":
                addr = (self.read(self.r.PC) + self.r.X) & 0xFF
                self.r.PC += 1
                value = self.read(addr)
            case "zery":
                addr = (self.read(self.r.PC) + self.r.Y) & 0xFF
                self.r.PC += 1
                value = self.read(addr)
            case "abso":
                lo = self.read(self.r.PC)
                self.r.PC += 1
                hi = self.read(self.r.PC)
                self.r.PC += 1
                addr = (hi << 8) | lo
                value = self.read(addr)
            case "absx":
                lo = self.read(self.r.PC)
                self.r.PC += 1
                hi = self.read(self.r.PC)
                self.r.PC += 1
                addr = ((hi << 8) | lo) + self.r.X
                value = self.read(addr)
            case "absy":
                lo = self.read(self.r.PC)
                self.r.PC += 1
                hi = self.read(self.r.PC)
                self.r.PC += 1
                addr = ((hi << 8) | lo) + self.r.Y
                value = self.read(addr)
            case "indx":
                addr = self.read(self.r.PC)
                self.r.PC += 1
                lo = self.read((addr + self.r.X) & 0xFF)
                hi = self.read((addr + self.r.X + 1) & 0xFF)
                addr = (hi << 8) | lo
                value = self.read(addr)
            case "indy":
                addr = self.read(self.r.PC)
                self.r.PC += 1
                lo = self.read(addr)
                hi = self.read((addr + 1) & 0xFF)
                addr = ((hi << 8) | lo) + self.r.Y
                value = self.read(addr)
            case "rela":
                value = self.read(self.r.PC)
                self.r.PC += 1
            case "indi":
                lo = self.read(self.r.PC)
                self.r.PC += 1
                hi = self.read(self.r.PC)
                self.r.PC += 1
                indi_addr = (hi << 8) | lo
                if lo == 0xFF:
                    addr = (self.read(indi_addr & 0xFF00) << 8) | self.read(indi_addr)
                else:
                    addr = (self.read(indi_addr + 1) << 8) | self.read(indi_addr)

        match mnemonic:
            case "ADC":
                result = self.r.A + value + (self.r.P & 1)
                self.set_status_flags(
                    C=result > 0xFF,
                    Z=(result & 0xFF) == 0,
                    V=bool((result ^ self.r.A) & (result ^ value) & 0x80),
                    N=bool(result & 0x80),
                )
                self.r.A = result & 0xFF
            case "AND":
                self.r.A = self.r.A & value
                self.set_status_flags(Z=self.r.A == 0, N=bool(self.r.A & 0x80))
            case "ASL":
                result = (value << 1) & 0xFF
                self.set_status_flags(C=bool(value & 0x80), Z=result == 0, N=bool(result & 0x80))
                value = result
            case "BCC":
                self.branch_off(not self.get_flag("C"), value)
            case "BCS":
                self.branch_off(self.get_flag("C"), value)
            case "BEQ":
                self.branch_off(self.get_flag("Z"), value)
            case "BIT":
                self.set_status_flags(
                    Z=(value & self.r.A) == 0,
                    N=bool(value & 0b10000000),
                    V=bool(value & 0b01000000),
                )
            case "BMI":
                self.branch_off(self.get_flag("N"), value)
            case "BNE":
                self.branch_off(not self.get_flag("Z"), value)
            case "BPL":
                self.branch_off(not self.get_flag("N"), value)
            case "BRK":
                pass
            case "BVC":
                self.branch_off(not self.get_flag("V"), value)
            case "BVS":
                self.branch_off(self.get_flag("V"), value)
            case "CLC":
                self.set_flag("C", False)
            case "CLD":
                self.set_flag("D", False)
            case "CLI":
                self.set_flag("I", False)
            case "CLV":
                self.set_flag("V", False)
            case "CMP":
                result = (self.r.A - value) & 0x80
                self.set_status_flags(C=self.r.A >= value, Z=self.r.A == value, N=bool(result))
            case "CPX":
                result = (self.r.X - value) & 0x80
                self.set_status_flags(C=self.r.X >= value, Z=self.r.X == value, N=bool(result))
            case "CPY":
                result = (self.r.Y - value) & 0x80
                self.set_status_flags(C=self.r.Y >= value, Z=self.r.Y == value, N=bool(result))
            case "DEC":
                value = value - 1
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
            case "DEX":
                self.r.X = (self.r.X - 1) & 0xFF
                self.set_status_flags(Z=self.r.X == 0, N=bool(self.r.X & 0x80))
            case "DEY":
                self.r.Y = (self.r.Y - 1) & 0xFF
                self.set_status_flags(Z=self.r.Y == 0, N=bool(self.r.Y & 0x80))
            case "EOR":
                self.r.A = self.r.A ^ value
                self.set_status_flags(Z=self.r.A == 0, N=bool(self.r.A & 0x80))
            case "INC":
                value = (value + 1) & 0xFF
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
            case "INX":
                self.r.X = (self.r.X + 1) & 0xFF
                self.set_status_flags(Z=self.r.X == 0, N=bool(self.r.X & 0x80))
            case "INY":
                self.r.Y = (self.r.Y + 1) & 0xFF
                self.set_status_flags(Z=self.r.Y == 0, N=bool(self.r.Y & 0x80))
            case "JMP":
                self._pending_pc = addr
            case "JSR":
                return_addr = self.r.PC - 1
                self.push(return_addr >> 8)
                self.push(return_addr)
                self._pending_pc = addr
            case "LDA":
                self.r.A = value
                self.set_status_flags(Z=value == 0, N=bool(value & 0x80))
            case "LDX":
                self.r.X = value
                self.set_status_flags(Z=value == 0, N=bool(value & 0x80))
            case "LDY":
                self.r.Y = value
                self.set_status_flags(Z=value == 0, N=bool(value & 0x80))
            case "LSR":
                result = value >> 1
                self.set_status_flags(C=bool(value & 0x01), Z=result == 0, N=False)
                value = result
            case "NOP":
                pass
            case "ORA":
                self.r.A |= value
                self.set_status_flags(Z=self.r.A == 0, N=bool(self.r.A & 0x80))
            case "PHA":
                self.push(self.r.A)
            case "PHP":
                self.push(self.r.P | 0b00100000)
            case "PLA":
                self.r.A = self.pull()
                self.set_status_flags(Z=self.r.A == 0, N=bool(self.r.A & 0x80))
            case "PLP":
                self.r.P = self.pull()
            case "ROL":
                result = (value << 1) | (0x01 if self.get_flag("C") else 0x00)
                self.set_status_flags(C=bool(value & 0x80), Z=result == 0, N=bool(result & 0x80))
                value = result
            case "ROR":
                result = (value >> 1) | (0x80 if self.get_flag("C") else 0x00)
                self.set_status_flags(C=bool(value & 0x01), Z=result == 0, N=bool(result & 0x80))
                value = result
            case "RTI":
                self.r.P = self.pull()
                lo = self.pull()
                hi = self.pull()
                self._pending_pc = (hi << 8) | lo
            case "RTS":
                lo = self.pull()
                hi = self.pull()
                self.r.PC = ((hi << 8) | lo) + 1
            case "SBC":
                result = self.r.A + ~value + self.get_flag("C")
                self.set_status_flags(
                    C=not(result < 0),
                    Z=result == 0,
                    V=bool((result ^ self.r.A) & (result ^ ~value) & 0x80),
                    N=bool(result & 0x80),
                )
                self.r.A = result & 0xFF
            case "SEC":
                self.set_status_flags(C=True)
            case "SED":
                self.set_status_flags(D=True)
            case "SEI":
                self.set_status_flags(I=True)
            case "STA":
                self.nes.write(addr, self.r.A)
            case "STX":
                self.nes.write(addr, self.r.X)
            case "STY":
                self.nes.write(addr, self.r.Y)
            case "TAX":
                self.r.X = self.r.A
                self.set_status_flags(Z=self.r.X == 0, N=bool(self.r.X & 0x80))
            case "TAY":
                self.r.Y = self.r.A
                self.set_status_flags(Z=self.r.Y == 0, N=bool(self.r.Y & 0x80))
            case "TSX":
                self.r.X = self.r.S
                self.set_status_flags(Z=self.r.X == 0, N=bool(self.r.X & 0x80))
            case "TXA":
                self.r.A = self.r.X
                self.set_status_flags(Z=self.r.A == 0, N=bool(self.r.A & 0x80))
            case "TXS":
                self.r.S = self.r.X
            case "TYA":
                self.r.A = self.r.Y
                self.set_status_flags(Z=self.r.A == 0, N=bool(self.r.A & 0x80))

        # Write-back for read-modify-write instructions
        match (mnemonic, addr_mode):
            case ("ASL" | "LSR" | "ROR" | "ROL", "accu"):
                self.r.A = value & 0xFF
            case (
                ("ASL" | "LSR" | "ROR" | "ROL" | "INC" | "DEC",
                 "zero" | "zerx" | "abso" | "absx")
            ):
                self.write(addr, value & 0xFF)

        return CYCLES[(mnemonic, addr_mode)]


    def step(self):
        self._pending_pc = None
        opcode = self.fetch()
        mnemonic, addr_mode = self.decode(opcode)
        cycles = self.execute(mnemonic, addr_mode)
        if self._pending_pc is not None:
            self.r.PC = self._pending_pc
            self._pending_pc = None
        return cycles
