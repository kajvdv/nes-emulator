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

class Operations:
    def __init__(self, r: Registers) -> None:
        self.r = r

    def set_status_flag(self, flag: int, bool: bool):
        if bool:
            self.r.P |= (1 << flag)
        else:
            self.r.P &= ~(1 << flag)

    def set_carry(self, value: int):
        value &= 0xFF
        self.set_status_flag(0, bool(value & 0xFF00))

    def set_zero(self, value: int):
        value &= 0xFF
        self.set_status_flag(1, value == 0)

    def set_negative(self, value: int):
        value &= 0xFF
        self.set_status_flag(7, bool(value & 0x80))

    def set_interrupt_diable(self, bool: bool):
        self.set_status_flag(2, bool)
    
    def LDA(self, value: int):
        self.r.A = value
        self.set_zero(value)
        self.set_negative(value)

    def LDX(self, value: int):
        self.r.X = value
        self.set_zero(value)
        self.set_negative(value)

    def LDY(self, value: int):
        self.r.Y = value
        self.set_zero(value)
        self.set_negative(value)

    def CMP(self, value: int):
        result = self.r.A - value
        self.set_zero(result)
        self.set_negative(result)

    def CPX(self, value: int):
        self.set_zero(value)
        self.set_negative(value)

    def DEX(self):
        self.r.X = (self.r.X - 1) & 0xFF
        self.set_negative(self.r.X)
        self.set_zero(self.r.X)

    def INC(self, value: int):
        value += 1
        self.set_zero(value)
        self.set_negative(value)
        return value & 0xFF

    def INX(self):
        self.r.X = (self.r.X + 1) & 0xFF
        self.set_negative(self.r.X)
        self.set_zero(self.r.X)

    def DEY(self):
        self.r.Y = (self.r.Y - 1) & 0xFF
        self.set_negative(self.r.Y)
        self.set_zero(self.r.Y)

    def INY(self):
        self.r.Y = (self.r.Y + 1) & 0xFF
        self.set_negative(self.r.Y)
        self.set_zero(self.r.Y)

    def CLD(self):
        self.set_status_flag(3, False)

    def SEI(self):
        self.set_interrupt_diable(True)

    def LSR(self, value):
        value = (value >> 1) & 0xFF
        self.set_negative(value)
        self.set_zero(value)
        self.set_carry(value)
        return value

    def ROL(self, value):
        value = (value << 1) & 0xFF
        self.set_negative(value)
        self.set_zero(value)
        self.set_carry(value)
        return value 
    
    def EOR(self, value):
        self.r.A = (self.r.A ^ value)
        self.set_negative(self.r.A)
        self.set_zero(self.r.A)

    def AND(self, value):
        self.r.A = (self.r.A ^ value)
        self.set_negative(self.r.A)
        self.set_zero(self.r.A)



class CPU6502:
    def __init__(self, nes: Bus):
        self.nes = nes
        self.r = Registers()
        self.ops = Operations(self.r)
        # self.r_A: int = 0
        # self.r_X: int = 0
        # self.r_Y: int = 0
        # self.r_S: int = 0xFF
        # self.r_P: int = 0
        # self.r_PC: int = 0

    def reset(self):
        lo_pc = self.read(0xFFFC)
        hi_pc = self.read(0xFFFD)
        pc = (hi_pc << 8) | lo_pc
        self.r.PC = pc
        self.r.S = 0xFF

    def read(self, addr: int):
        return self.nes.read(addr)

    def write(self, addr: int, value: int):
        self.nes.write(addr, value)

    def push(self, value: int):
        addr = self.r.S | 0x0100
        print(f"push: pushing 0x{value:02X} to 0x{addr:04X}")
        self.write(addr, value & 0xFF)
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

    def zero_page(self, addr: int):
        return self.nes.read(addr & 0xFF)

    def get_zero_addr(self):
        addr = self.read(self.r.PC)
        self.r.PC += 1
        return addr
    
    def get_absolute_addr(self):
        lo_byte = self.read(self.r.PC)
        self.r.PC += 1
        hi_byte = self.read(self.r.PC)
        self.r.PC += 1
        abs_addr = (hi_byte << 8) | lo_byte
        return abs_addr
    
    def indirect_x(self, operand: int):
        addr = operand + self.r.X
        lo_byte = self.read(addr)
        hi_byte = self.read(addr + 1)
        abs_addr = (hi_byte << 8) | lo_byte
        return self.read(abs_addr)
    
    def indirect_y(self, operand: int):
        lo_byte = self.read(operand)
        hi_byte = self.read(operand + 1)
        abs_addr = (hi_byte << 8) | lo_byte
        return self.read(abs_addr + self.r.Y)

    def get_status_flag(self, flag: int):
        return bool(self.r.P & (1 << flag))
    
    def get_flag(self, flag: Literal["N","V","1","B","D","I","Z","C"]):
        enum = {"N": 7,"V": 6,"1": 5,"B": 4,"D": 3,"I": 2,"Z": 1,"C": 0}
        return bool(self.r.P & (1 << enum[flag]))
    
    def set_flag(self, flag: Literal["N","V","1","B","D","I","Z","C"], value: bool):
        enum = {"N": 7,"V": 6,"1": 5,"B": 4,"D": 3,"I": 2,"Z": 1,"C": 0}
        if value:
            self.r.P |= (1 << enum[flag])
        else:
            self.r.P &= ~(1 << enum[flag])
        print(f"P: {self.r.P:08b} after {flag} -> {int(value)}")


    def get_zero(self):
        return self.get_status_flag(1)

    def get_negative(self):
        return self.get_status_flag(7)
    
    def get_branch_offset(self):
        offset = self.read(self.r.PC)
        self.r.PC += 1
        if offset & 0x80:
            # If the signed bit is set, the the value should be negative.
            offset = offset - 256
        return offset
    
    def PLA(self):
        self.r.A = self.pull()
        self.set_flag("Z", self.r.A == 0)
        return 4
    
    def fetch(self) -> int:
        opcode = self.read(self.r.PC)
        self.r.PC += 1
        return opcode

    def decode(self, opcode) -> tuple[str, str]:
        try:
            return OPCODES[opcode]
        except KeyError as e:
            raise KeyError(hex(e.args[0]))
        
    def execute(self, mnomonic: str, addr_mode: str) -> int:
        value = -1
        addr = -1
        match addr_mode:
            case "immi":
                value = self.read(self.r.PC)
                self.r.PC += 1
            case "zero":
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
            case "zerx":
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr + self.r.X)
            case "abso":
                lo = self.read(self.r.PC)
                self.r.PC += 1
                hi = self.read(self.r.PC)
                self.r.PC += 1
                addr = (hi << 8) | lo
                value = self.read(addr)
            case "absx":
                raise NotImplementedError()
            case "absy":
                raise NotImplementedError()
            case "indx":
                raise NotImplementedError()
            case "indy":
                raise NotImplementedError()
            case "rela":
                value = self.read(self.r.PC)
                self.r.PC += 1

        match mnomonic:
            case "ADC":
                result = self.r.A + value + (self.r.P & 1)
                self.set_flag("C", result > 0xFF)
                self.set_flag("Z", (result & 0xFF) == 0)
                self.set_flag("V", bool((result ^ self.r.A) & (result ^ value) & 0x80))
                self.set_flag("N", bool(result & 0x80))
                self.r.A = result & 0xFF
                print(f"ADC: result was: {result:08b}, loaded in A: {self.r.A:08b}")
                return 0
            case "AND": 
                self.r.A = self.r.A & value
                print(f"AND: result in A {self.r.A:08b}")
                self.set_flag("Z", self.r.A == 0)
                self.set_flag("N", bool(self.r.A & 0x80))
                return 0
            case "ASL": ...
            case "BCC": 
                if not self.get_flag("C"):
                    self.r.PC += value
                return 2
            case "BCS":
                if self.get_flag("C"):
                    self.r.PC += value
                return 2
            case "BEQ": 
                if self.get_flag("Z"):
                    self.r.PC += value
                return 2
            case "BIT": 
                self.set_flag("Z", (value & self.r.A) == 0)
                self.set_flag("N", bool(value & 0b00100000))
                self.set_flag("V", bool(value & 0b01000000))
                return 0
            case "BMI":
                if self.get_flag("N"):
                    self.r.PC += value
                return 2
            case "BNE": 
                if not self.get_flag("Z"):
                    self.r.PC += value
                return 2
            case "BPL": 
                if not self.get_flag("N"):
                    self.r.PC += value
                return 2
            case "BRK": ...
            case "BVC": 
                if not self.get_flag("V"):
                    self.r.PC += value
                return 2
            case "BVS": 
                if self.get_flag("V"):
                    self.r.PC += value
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
                print(f"CMP: comparing A {self.r.A:08b}/0x{self.r.A:02X} with {value:08b}/0x{value:02X}, resulting in {result:08b}")
                self.set_flag("C", self.r.A >= value)
                self.set_flag("Z", self.r.A == value)
                self.set_flag("N", bool(result))
                return 0
            case "CPX": 
                result = (self.r.X - value) & 0x80
                print(f"CMX: comparing X 0x{self.r.X:02X} with 0x{value:02X}, resulting in 0x{result:02X}")
                self.set_flag("C", self.r.X >= value)
                self.set_flag("Z", self.r.X == value)
                self.set_flag("N", bool(result))
                return 0
            case "CPY": 
                result = (self.r.Y - value) & 0x80
                print(f"CMY: comparing Y {self.r.Y:08b} with {value:08b}, resulting in {result:08b}")
                self.set_flag("C", self.r.Y >= value)
                self.set_flag("Z", self.r.Y == value)
                self.set_flag("N", bool(result))
                return 0
            case "DEC": ...
            case "DEX": 
                result = self.r.X - 1
                self.set_flag("Z", result == 0)
                self.set_flag("N", bool(result & 0x80))
                self.r.X = result & 0xFF
                print(f"DEX: new X 0x{self.r.X:02X}")
                return 0
            case "DEY": 
                result = self.r.Y - 1
                self.set_flag("Z", result == 0)
                self.set_flag("N", bool(result & 0x80))
                self.r.Y = result & 0xFF
                print(f"DEY: new Y 0x{self.r.Y:02X}")
                return 0
            case "EOR": 
                self.r.A = self.r.A ^ value
                self.set_flag("Z", self.r.A == 0)
                self.set_flag("N", bool(self.r.A & 0x80))
                return 0
            case "INC": ...
            case "INX":
                result = self.r.X + 1
                print(f"INX: result 0x{result:02X}")
                self.r.X = result & 0xFF
                self.set_flag("Z", self.r.X == 0)
                self.set_flag("N", bool(self.r.X & 0x80))
                return 0
            case "INY":
                result = self.r.Y + 1
                print(f"INY: result 0x{result:02X}")
                self.r.Y = result & 0xFF
                self.set_flag("Z", self.r.Y == 0)
                self.set_flag("N", bool(self.r.Y & 0x80))
                return 0
            case "JMP": 
                self.r.PC = addr
                return 0
            case "JSR":
                print(f"JSR: Jumping to {addr:04X}")
                # print(f"JSR: read on addr {self.read(addr):04X}")
                return_addr = self.r.PC - 1
                self.push(return_addr >> 8)
                self.push(return_addr)
                self.r.PC = addr
                return 0
            case "LDA": 
                self.r.A = value
                print(f"LDA: {value:08b} loaded in A")
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
                return 2
            case "LDX":
                print(f"LDX: setting X to 0x{value:02X}")
                self.r.X = value
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
                return 2
            case "LDY": 
                self.r.Y = value
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
                return 2
            case "LSR": ...
            case "NOP": 
                return 2
            case "ORA":
                self.r.A |= value
                self.set_flag("Z", self.r.A == 0)
                self.set_flag("N", bool(self.r.A & 0x80))
                return 0
            case "PHA": 
                print(f"PHA: pushing A 0b{self.r.A:08b}/0x{self.r.A:02X}")
                self.push(self.r.A)
                return 3
            case "PHP": 
                print(f"PHP: pushing status {self.r.P:08b}")
                self.push(self.r.P | 0b00110000)
                return 3
            case "PLA": 
                self.r.A = self.pull()
                print(f"PLA: pulled {self.r.A:08b}")
                self.set_flag("Z", self.r.A == 0)
                self.set_flag("N", bool(self.r.A & 0x80))
                return 4
            case "PLP": 
                self.r.P = self.pull()
                return 4
            case "ROL": ...
            case "ROR": ...
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
                self.set_flag("C", not(result < 0))
                self.set_flag("Z", result == 0)
                self.set_flag("V", bool((result ^ self.r.A) & (result ^ ~value) & 0x80))
                self.set_flag("N", bool(result & 0x80))
                self.r.A = result & 0xFF
                return 0
            case "SEC": 
                self.set_flag("C", True)
                return 2
            case "SED": 
                self.set_flag("D", True)
                return 2
            case "SEI": 
                self.set_flag("I", True)
                return 2
            case "STA": 
                print(f"Writing A {self.r.A:08b} to {addr:08b}")
                self.nes.write(addr, self.r.A)
                return 4
            case "STX": 
                print(f"STX: Wrting {self.r.X:02X} to {addr:04X}")
                self.nes.write(addr, self.r.X)
                return 4
            case "STY":
                print(f"STy: Wrting {self.r.Y:02X} to {addr:04X}")
                self.nes.write(addr, self.r.Y)
                return 4
            case "TAX": ...
            case "TAY":
                print(f"TAY: A 0x{self.r.A:02X} -> Y")
                self.r.Y = self.r.A
                return 2
            case "TSX":
                print(f"TSX: SP 0x{self.r.S:02X} -> X")
                self.r.X = self.r.S
                return 2
            case "TXS":
                print(f"TXS: X 0x{self.r.X:02X} -> SP")
                self.r.S = self.r.X
                return 2
            case "TYA": ...
        raise Exception(f"{mnomonic} with addr_mode: {addr_mode} not implemented")

    def step(self):
        opcode = self.fetch()
        mnomonic, addr_mode = self.decode(opcode)
        return self.execute(mnomonic, addr_mode)

    # def execute(self) -> int:
    #     match opcode:
    #         case 0xE0: # CPX imm
    #             value = self.r.X - self.read(self.r.PC)
    #             self.r.PC += 1
    #             self.ops.CPX(value)
    #             return 2
    #         case 0xC9: # CMP imm
    #             value = self.read(self.r.PC)
    #             self.r.PC += 1
    #             self.ops.CMP(value)
    #             return 2
    #         case 0xC5: # CMP zero
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.read(addr)
    #             self.ops.CMP(value)
    #             return 3
    #         case 0xA5: # LDA zero page
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.zero_page(addr)
    #             self.ops.LDA(value)
    #             return 3
    #         case 0xA9: # LDA imm
    #             value = self.read(self.r.PC)
    #             self.r.PC += 1
    #             self.ops.LDA(value)
    #             return 2
    #         case 0xAD: # LDA abs
    #             abs_addr = self.get_absolute_addr()
    #             value = self.read(abs_addr)
    #             self.ops.LDA(value)
    #             return 4
    #         case 0xBD: # LDA abs x
    #             abs_addr = self.get_absolute_addr()
    #             value = self.read(abs_addr + self.r.X)
    #             self.ops.LDA(value)
    #             return 4
    #         case 0xB1: # LDA ind y
    #             operand = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.indirect_y(operand)
    #             self.ops.LDA(value)
    #             return 5
    #         case 0x8D: # STA abs
    #             abs_addr = self.get_absolute_addr()
    #             self.nes.write(abs_addr, self.r.A)
    #             return 4
    #         case 0x85: # STA zero
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             self.write(addr, self.r.A)
    #             return 3
    #         case 0x8E: # STX abs
    #             abs_addr = self.get_absolute_addr()
    #             self.nes.write(abs_addr, self.r.X)
    #             return 4
    #         case 0x86: # STX zero
    #             self.nes.write(self.get_zero_addr(), self.r.X)
    #             return 4
    #         case 0x8C: # STY abs
    #             abs_addr = self.get_absolute_addr()
    #             self.nes.write(abs_addr, self.r.Y)
    #             return 4
    #         case 0xA2: # LDX imm
    #             value = self.read(self.r.PC)
    #             self.r.PC += 1
    #             self.ops.LDX(value)
    #             return 2
    #         case 0xA0: # LDY imm
    #             value = self.read(self.r.PC)
    #             self.r.PC += 1
    #             self.ops.LDY(value)
    #             return 2
    #         case 0xE6: # INC zero
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.zero_page(addr)
    #             self.write(addr, self.ops.INC(value))
    #             return 5
    #         case 0xCA: # DEX
    #             self.ops.DEX()
    #             return 2
    #         case 0xE8: # INX
    #             self.ops.INX()
    #             return 2
    #         case 0x88: # DEY
    #             self.ops.DEY()
    #             return 2
    #         case 0xC8: # INY
    #             self.ops.INY()
    #             return 2
    #         case 0x10: # Branch if plus
    #             offset = self.get_branch_offset()
    #             if not self.get_negative():
    #                 self.r.PC += offset
    #                 return 3
    #             return 2
    #         case 0xF0: # Branch if equal
    #             offset = self.get_branch_offset()
    #             if self.get_zero():
    #                 self.r.PC += offset
    #                 return 3
    #             return 2
    #         case 0xD0: # Branch if not equal
    #             offset = self.get_branch_offset()
    #             if not self.get_zero():
    #                 self.r.PC += offset
    #                 return 3
    #             return 2
    #         case 0x4A: # LSR
    #             self.ops.LSR(self.r.A)
    #             return 2
    #         case 0x26: # ROL
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.zero_page(addr)
    #             self.write(addr, self.ops.ROL(value))
    #             return 5
    #         case 0x45:
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.zero_page(addr)
    #             self.ops.EOR(value)
    #             return 3
    #         case 0x25:
    #             addr = self.read(self.r.PC)
    #             self.r.PC += 1
    #             value = self.zero_page(addr)
    #             self.ops.AND(value)
    #             return 3
    #         case 0x48: # PHA
    #             self.push(self.r.A)
    #             return 3
    #         case 0x68: # PLA
    #             self.r.A = self.pull()
    #             return 4
    #         case 0x78: # SEI
    #             self.ops.SEI()
    #             return 2
    #         case 0xD8: # CLD
    #             self.ops.CLD()
    #             return 2
    #         case 0x9A: # TXS
    #             self.r.S = self.r.X
    #             return 2
    #         case 0x8A: # TXA
    #             self.r.A = self.r.X
    #             return 2
    #         case 0xAA: # TAX
    #             self.r.X = self.r.A
    #             return 2
    #         case 0x20: # JSR
    #             abs_addr = self.get_absolute_addr()
    #             return_addr = self.r.PC - 1
    #             self.push((return_addr >> 8) & 0xFF)
    #             self.push(return_addr & 0x00FF)
    #             self.r.PC = abs_addr
    #             return 6
    #         case 0x60: # RTS
    #             lo_byte = self.pull()
    #             hi_byte = self.pull()
    #             addr = (hi_byte << 8) | lo_byte
    #             self.r.PC = addr + 1
    #             return 6
    #         case _:
    #             raise Exception(f"Opcode 0x{opcode:02X} is not implemented")