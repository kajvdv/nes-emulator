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
        self.write(addr, value)
        self.r.S = (self.r.S - 1) & 0xFF

    def pull(self) -> int:
        self.r.S = (self.r.S + 1) & 0xFF
        return self.read(self.r.S | 0x0100)

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
                raise NotImplementedError()
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
            case "ADC": ...
            case "AND": ...
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
                self.r.P = value & self.r.A
                print("Status register is now", self.r.P)
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
            case "CLV": ...
            case "CMP": ...
            case "CPX": ...
            case "CPY": ...
            case "DEC": ...
            case "DEX": ...
            case "DEY": ...
            case "EOR": ...
            case "INC": ...
            case "INX": ...
            case "INY": ...
            case "JMP": 
                self.r.PC = addr
                return 0
            case "JSR": ...
            case "LDA": 
                self.r.A = value
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
                return 2
            case "LDX":
                self.r.X = value
                self.set_flag("Z", value == 0)
                self.set_flag("N", bool(value & 0x80))
                return 2
            case "LDY": ...
            case "LSR": ...
            case "NOP": 
                return 2
            case "ORA": ...
            case "PHA": ...
            case "PHP": ...
            case "PLA": ...
            case "PLP": ...
            case "ROL": ...
            case "ROR": ...
            case "RTI": ...
            case "RTS": ...
            case "SBC": ...
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
                self.nes.write(addr, self.r.A)
                return 4
            case "STX": 
                self.nes.write(addr, self.r.X)
                return 4
            case "STY": ...
            case "TAX": ...
            case "TAY": ...
            case "TXS":
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