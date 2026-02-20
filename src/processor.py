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
        if self.r.S == 0xFF:
            print("pull: Stack underflowed")
            assert 0
        self.r.S = (self.r.S + 1) & 0xFF
        addr = self.r.S | 0x0100
        value = self.read(addr)
        print(f"pull: pulled 0x{value:02X} from 0x{addr:04X}")
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
        print(f"   NV1BDIZC")
        print(f"P: {self.r.P:08b}")
    
    def branch_off(self, condition, offset):
        if offset & 0x80:
            # If the signed bit is set, the the value should be negative.
            offset = offset - 0x100
        if condition:
            self.r.PC += offset
    
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
                addr = ((hi << 8) | lo)  + self.r.Y
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
                print(f"indi: indi_addr = (0x{hi:02X} << 8) | 0x{lo:02X}")
                if lo == 0xFF:
                    addr = (self.read(indi_addr & 0xFF00) << 8) | self.read(indi_addr + 0)
                else:
                    addr = (self.read(indi_addr + 1) << 8) | self.read(indi_addr + 0)

                print(f"indi: addr = (0x{hi:02X} << 8) | 0x{lo:02X}")


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
                print(f"ADC: result was: {result:08b}, loaded in A: {self.r.A:08b}")
                return 0
            case "AND": 
                self.r.A = self.r.A & value
                print(f"AND: result in A {self.r.A:08b}")
                self.set_status_flags(
                    Z=self.r.A == 0,
                    N=bool(self.r.A & 0x80),
                )
                return 0
            case "ASL": 
                result = (value << 1) & 0xFF
                print(f"0x{result:02X} = (0x{value:02X} << 1) & 0xFF")
                self.set_status_flags(
                    C=bool(value & 0x80),
                    Z=result == 0,
                    N=bool(result & 0x80),
                )
                value = result
            case "BCC": 
                self.branch_off(not self.get_flag("C"), value)
                return 2
            case "BCS":
                self.branch_off(self.get_flag("C"), value)
                return 2
            case "BEQ": 
                self.branch_off(self.get_flag("Z"), value)
                return 2
            case "BIT": 
                self.set_status_flags(
                    Z=(value & self.r.A) == 0,
                    N=bool(value & 0b10000000),
                    V=bool(value & 0b01000000),
                )
                return 0
            case "BMI":
                self.branch_off(self.get_flag("N"), value)
                return 2
            case "BNE": 
                self.branch_off(not self.get_flag("Z"), value)
                return 2
            case "BPL": 
                self.branch_off(not self.get_flag("N"), value)
                return 2
            case "BRK": ...
            case "BVC": 
                self.branch_off(not self.get_flag("V"), value)
                return 2
            case "BVS": 
                self.branch_off(self.get_flag("V"), value)
                return 2
            case "CLC": 
                self.set_flag("C", False)
                return 2
            case "CLD": 
                self.set_flag("D", False)
                return 2
            case "CLI": ...
            case "CLV": 
                self.set_flag("V", False)
                return 2
            case "CMP":
                result = (self.r.A - value) & 0x80
                print(f"CMP: 0x{result:02X} = (0x{self.r.A:02X} - 0x{value:02X}) & 0x80")
                self.set_status_flags(
                    C=self.r.A >= value,
                    Z=self.r.A == value,
                    N=bool(result),
                )
                return 0
            case "CPX": 
                result = (self.r.X - value) & 0x80
                print(f"CMX: comparing X 0x{self.r.X:02X} with 0x{value:02X}, resulting in 0x{result:02X}")
                self.set_status_flags(
                    C=self.r.X >= value,
                    Z=self.r.X == value,
                    N=bool(result),
                )
                return 0
            case "CPY": 
                result = (self.r.Y - value) & 0x80
                print(f"CMY: comparing Y {self.r.Y:08b} with {value:08b}, resulting in {result:08b}")
                self.set_status_flags(
                    C=self.r.Y >= value,
                    Z=self.r.Y == value,
                    N=bool(result),
                )
                return 0
            case "DEC": 
                value = value - 1
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
            case "DEX": 
                result = self.r.X - 1
                self.set_status_flags(
                    Z=result == 0,
                    N=bool(result & 0x80),
                )
                self.r.X = result & 0xFF
                print(f"DEX: new X 0x{self.r.X:02X}")
                return 0
            case "DEY": 
                result = self.r.Y - 1
                self.set_status_flags(
                    Z=result == 0,
                    N=bool(result & 0x80),
                )
                self.r.Y = result & 0xFF
                print(f"DEY: new Y 0x{self.r.Y:02X}")
                return 0
            case "EOR": 
                self.r.A = self.r.A ^ value
                self.set_status_flags(
                    Z=self.r.A == 0,
                    N=bool(self.r.A & 0x80),
                )
                return 0
            case "INC":
                value = (value + 1) & 0xFF
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
            case "INX":
                result = self.r.X + 1
                print(f"INX: result 0x{result:02X}")
                self.r.X = result & 0xFF
                self.set_status_flags(
                    Z=self.r.X == 0,
                    N=bool(self.r.X & 0x80),
                )
                return 0
            case "INY":
                result = self.r.Y + 1
                print(f"INY: result 0x{result:02X}")
                self.r.Y = result & 0xFF
                self.set_status_flags(
                    Z=self.r.Y == 0,
                    N=bool(self.r.Y & 0x80),
                )
                return 0
            case "JMP": 
                self.r.PC = addr
                print(f"JMP: self.r.PC = 0x{addr:02X}")
                return 0
            case "JSR":
                # print(f"JSR: read on addr {self.read(addr):04X}")
                return_addr = self.r.PC - 1
                print(f"JSR: 0x{return_addr:02X} = 0x{self.r.PC:04X} - 1")
                self.push(return_addr >> 8)
                self.push(return_addr)
                self.r.PC = addr
                print(f"JSR: self.r.PC = 0x{addr:02X}")
                return 0
            case "LDA": 
                self.r.A = value
                self.set_status_flags(
                    Z=value == 0,
                    N=bool(value & 0x80),
                )
                return 2
            case "LDX":
                self.r.X = value
                self.set_status_flags(
                    Z=value == 0,
                    N=bool(value & 0x80),
                )
                return 2
            case "LDY": 
                self.r.Y = value
                self.set_status_flags(
                    Z=value == 0,
                    N=bool(value & 0x80),
                )
                return 2
            case "LSR":
                result = value >> 1
                print(f"LSR: {result} = {value} >> 1")
                self.set_status_flags(
                    C=bool(value & 0x01),
                    Z=result == 0,
                    N=False,
                )
                value = result
            case "NOP": 
                return 2
            case "ORA":
                self.r.A |= value
                self.set_status_flags(
                    Z=self.r.A == 0,
                    N=bool(self.r.A & 0x80),
                )
                return 0
            case "PHA": 
                print(f"PHA: pushing A 0b{self.r.A:08b}/0x{self.r.A:02X}")
                self.push(self.r.A)
                return 3
            case "PHP": 
                print(f"PHP: pushing status {self.r.P:08b}")
                self.push(self.r.P | 0b00100000)
                return 3
            case "PLA": 
                self.r.A = self.pull()
                print(f"PLA: pulled {self.r.A:08b}")
                self.set_status_flags(
                    Z=self.r.A == 0,
                    N=bool(self.r.A & 0x80),
                )
                return 4
            case "PLP": 
                self.r.P = self.pull()
                return 4
            case "ROL": 
                result = (value << 1) | (0x01 if self.get_flag("C") else 0x00)
                print(f"ROL: 0x{result:02X} = (0x{value:02X} << 1) | (0x01 if {self.get_flag("C")} else 0x00)")
                self.set_status_flags(
                    C=bool(value & 0x80),
                    Z=result == 0,
                    N=bool(result & 0x80),
                )
                value = result
            case "ROR":
                result = (value >> 1) | (0x80 if self.get_flag("C") else 0x00)
                print(f"ROR: 0x{result:02X} = (0x{value:02X} >> 1) | (0x80 if {self.get_flag("C")} else 0x00)")
                self.set_status_flags(
                    C=bool(value & 0x01),
                    Z=result == 0,
                    N=bool(result & 0x80),
                )
                value = result
            case "RTI": 
                self.r.P = self.pull()
                lo = self.pull()
                hi = self.pull()
                addr = (hi << 8) | lo
                self.r.PC = addr
                return 0
            case "RTS":
                lo = self.pull()
                hi = self.pull()
                addr = (hi << 8) | lo
                self.r.PC = addr + 1
                print(f"RTS: returning to {self.r.PC:04X}")
                return 0
            case "SBC": 
                result = self.r.A + ~value + self.get_flag("C")
                self.set_status_flags(
                    C=not(result < 0),
                    Z=result == 0,
                    V=bool((result ^ self.r.A) & (result ^ ~value) & 0x80),
                    N=bool(result & 0x80),
                )
                self.r.A = result & 0xFF
                return 0
            case "SEC": 
                self.set_status_flags(C=True)
                return 2
            case "SED": 
                self.set_status_flags(D=True)
                return 2
            case "SEI": 
                self.set_status_flags(I=True)
                return 2
            case "STA": 
                self.nes.write(addr, self.r.A)
                print(f"self.nes.write(0x{addr:04X}, 0x{self.r.A:02X})")
                return 4
            case "STX": 
                print(f"STX: Wrting {self.r.X:02X} to {addr:04X}")
                self.nes.write(addr, self.r.X)
                return 4
            case "STY":
                self.nes.write(addr, self.r.Y)
                print(f"STY: self.nes.write(0x{addr:02X}, 0x{self.r.Y:02X})")
                return 4
            case "TAX":
                print(f"TAX: A 0x{self.r.A:02X} -> X")
                self.r.X = self.r.A
                self.set_status_flags(
                    Z=self.r.X == 0,
                    N=bool(self.r.X & 0x80),
                )
                return 2
            case "TAY":
                print(f"TAY: A 0x{self.r.A:02X} -> Y")
                self.r.Y = self.r.A
                self.set_status_flags(
                    Z=self.r.Y == 0,
                    N=bool(self.r.Y & 0x80),
                )
                return 2
            case "TSX":
                print(f"TSX: SP 0x{self.r.S:02X} -> X")
                self.r.X = self.r.S
                self.set_status_flags(
                    Z=self.r.X == 0,
                    N=bool(self.r.X & 0x80),
                )
                return 2
            case "TXA":
                print(f"TXA: X 0x{self.r.X:02X} -> A")
                self.r.A = self.r.X
                self.set_status_flags(
                    Z=self.r.A == 0,
                    N=bool(self.r.A & 0x80),
                )
                return 2
            case "TXS":
                print(f"TXS: X 0x{self.r.X:02X} -> SP")
                self.r.S = self.r.X
                return 2
            case "TYA":
                print(f"TYA: Y 0x{self.r.Y:02X} -> A")
                self.r.A = self.r.Y
                self.set_status_flags(
                    Z=self.r.Y == 0,
                    N=bool(self.r.Y & 0x80),
                )
                return 2

        # Writing back to memory
        match (mnemonic, addr_mode):
            case (
                ("ASL", "accu")
                | ("LSR", "accu")
                | ("ROR", "accu")
                | ("ROL", "accu")
            ):
                self.r.A = value & 0xFF
                print(f"accu: self.r.A = 0x{value:02X} & 0xFF")
                return 0
            case (
                ("LSR", "zero")
                | ("ASL", "zero")
                | ("ROR", "zero")
                | ("ROL", "zero")
                | ("INC", "zero")
                | ("DEC", "zero")
                | ("LSR", "zerx")
                | ("ASL", "zerx")
                | ("ROR", "zerx")
                | ("ROL", "zerx")
                | ("INC", "zerx")
                | ("DEC", "zerx")
            ):
                self.write(addr, value & 0xFF)
                return 0
            case (
                ("LSR", "abso")
                | ("ASL", "abso")
                | ("ROR", "abso")
                | ("ROL", "abso")
                | ("INC", "abso")
                | ("DEC", "abso")
                | ("LSR", "absx")
                | ("ASL", "absx")
                | ("ROR", "absx")
                | ("ROL", "absx")
                | ("INC", "absx")
                | ("DEC", "absx")
            ):
                self.write(addr, value & 0xFF)
                return 0
        raise Exception(f"{mnemonic} with addr_mode: {addr_mode} not implemented")


    def step(self):
        opcode = self.fetch()
        mnomonic, addr_mode = self.decode(opcode)
        return self.execute(mnomonic, addr_mode)
