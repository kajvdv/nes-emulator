from typing import Protocol
from dataclasses import dataclass, field

class Bus(Protocol):
    def read(self, addr: int) -> int:
        ...
    
    def write(self, addr: int, value: int):
        ...

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

    def CLI(self):
        self.set_interrupt_diable(False)

    def CLC(self):
        self.set_status_flag(0, False)

    def SEC(self):
        self.set_status_flag(0, True)

    def CLV(self):
        self.set_status_flag(6, False)

    def TAX(self):
        self.r.X = self.r.A
        self.set_zero(self.r.X)
        self.set_negative(self.r.X)

    def TAY(self):
        self.r.Y = self.r.A
        self.set_zero(self.r.Y)
        self.set_negative(self.r.Y)

    def TXA(self):
        self.r.A = self.r.X
        self.set_zero(self.r.A)
        self.set_negative(self.r.A)

    def TYA(self):
        self.r.A = self.r.Y
        self.set_zero(self.r.A)
        self.set_negative(self.r.A)

    def TSX(self):
        self.r.X = self.r.S
        self.set_zero(self.r.X)
        self.set_negative(self.r.X)

    def AND(self, value: int):
        self.r.A &= value
        self.set_zero(self.r.A)
        self.set_negative(self.r.A)

    def ORA(self, value: int):
        self.r.A |= value
        self.set_zero(self.r.A)
        self.set_negative(self.r.A)

    def EOR(self, value: int):
        self.r.A ^= value
        self.set_zero(self.r.A)
        self.set_negative(self.r.A)

    def BIT(self, value: int):
        self.set_zero(self.r.A & value)
        self.set_negative(value)
        self.set_status_flag(6, bool(value & 0x40))



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

    def get_carry(self):
        return self.get_status_flag(0)

    def get_zero(self):
        return self.get_status_flag(1)

    def get_negative(self):
        return self.get_status_flag(7)

    def get_overflow(self):
        return self.get_status_flag(6)
    
    def get_branch_offset(self):
        offset = self.read(self.r.PC)
        self.r.PC += 1
        if offset & 0x80:
            # If the signed bit is set, the the value should be negative.
            offset = offset - 256
        return offset

    def execute(self):
        opcode = self.read(self.r.PC)
        self.r.PC += 1
        match opcode:
            case 0xE0: # CPX imm
                value = self.r.X - self.read(self.r.PC)
                self.r.PC += 1
                self.ops.CPX(value)
            case 0xC9: # CMP imm
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.CMP(value)
            case 0xC5: # CMP zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
                self.ops.CMP(value)
            case 0xA5: # LDA zero page
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.zero_page(addr)
                self.ops.LDA(value)
            case 0xA9:
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.LDA(value)
            case 0xAD: # LDA abs
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr)
                self.ops.LDA(value)
            case 0xBD: # LDA abs x
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.X)
                self.ops.LDA(value)
            case 0xB1: # LDA ind y
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_y(operand)
                self.ops.LDA(value)
            case 0x8D: # STA abs
                abs_addr = self.get_absolute_addr()
                self.nes.write(abs_addr, self.r.A)
            case 0x85: # STA zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                self.write(addr, self.r.A)
            case 0x8E: # STX abs
                abs_addr = self.get_absolute_addr()
                self.nes.write(abs_addr, self.r.X)
            case 0x8C: # STY abs
                abs_addr = self.get_absolute_addr()
                self.nes.write(abs_addr, self.r.Y)
            case 0xA2: # LDX imm
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.LDX(value)
            case 0xA0: # LDY imm
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.LDY(value)
            case 0xE6: # INC zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.zero_page(addr)
                self.write(addr, self.ops.INC(value))
            case 0xCA: # DEX
                self.ops.DEX()
            case 0xE8: # INX
                self.ops.INX()
            case 0x88: # DEY
                self.ops.DEY()
            case 0xC8: # INY
                self.ops.INY()
            case 0x10: # Branch if plus
                offset = self.get_branch_offset()
                if not self.get_negative():
                    self.r.PC += offset
            case 0xF0: # Branch if equal
                offset = self.get_branch_offset()
                if self.get_zero():
                    self.r.PC += offset
            case 0xD0: # Branch if not equal
                offset = self.get_branch_offset()
                if not self.get_zero():
                    self.r.PC += offset
            case 0x78:
                self.ops.SEI()
            case 0xD8:
                self.ops.CLD()
            case 0x9A:
                self.r.S = self.r.X
            case 0x20: # JSR
                abs_addr = self.get_absolute_addr()
                return_addr = self.r.PC - 1
                self.push((return_addr >> 8) & 0xFF)
                self.push(return_addr & 0x00FF)
                self.r.PC = abs_addr
            case 0x60: # RTS
                lo_byte = self.pull()
                hi_byte = self.pull()
                addr = (hi_byte << 8) | lo_byte
                self.r.PC = addr + 1
            # --- NOP ---
            case 0xEA: # NOP
                pass
            # --- Flag operations ---
            case 0x18: # CLC
                self.ops.CLC()
            case 0x38: # SEC
                self.ops.SEC()
            case 0x58: # CLI
                self.ops.CLI()
            case 0xB8: # CLV
                self.ops.CLV()
            # --- Register transfers ---
            case 0xAA: # TAX
                self.ops.TAX()
            case 0xA8: # TAY
                self.ops.TAY()
            case 0x8A: # TXA
                self.ops.TXA()
            case 0x98: # TYA
                self.ops.TYA()
            case 0xBA: # TSX
                self.ops.TSX()
            # --- Stack operations ---
            case 0x48: # PHA
                self.push(self.r.A)
            case 0x68: # PLA
                self.r.A = self.pull()
                self.ops.set_zero(self.r.A)
                self.ops.set_negative(self.r.A)
            case 0x08: # PHP
                self.push(self.r.P | 0x30)
            case 0x28: # PLP
                self.r.P = (self.pull() & 0xCF) | (self.r.P & 0x30)
            # --- JMP ---
            case 0x4C: # JMP abs
                abs_addr = self.get_absolute_addr()
                self.r.PC = abs_addr
            case 0x6C: # JMP indirect
                abs_addr = self.get_absolute_addr()
                lo_byte = self.read(abs_addr)
                # 6502 bug: wraps within page on page boundary
                hi_addr = (abs_addr & 0xFF00) | ((abs_addr + 1) & 0x00FF)
                hi_byte = self.read(hi_addr)
                self.r.PC = (hi_byte << 8) | lo_byte
            # --- Branch instructions ---
            case 0x90: # BCC - Branch if carry clear
                offset = self.get_branch_offset()
                if not self.get_carry():
                    self.r.PC += offset
            case 0xB0: # BCS - Branch if carry set
                offset = self.get_branch_offset()
                if self.get_carry():
                    self.r.PC += offset
            case 0x30: # BMI - Branch if minus
                offset = self.get_branch_offset()
                if self.get_negative():
                    self.r.PC += offset
            case 0x50: # BVC - Branch if overflow clear
                offset = self.get_branch_offset()
                if not self.get_overflow():
                    self.r.PC += offset
            case 0x70: # BVS - Branch if overflow set
                offset = self.get_branch_offset()
                if self.get_overflow():
                    self.r.PC += offset
            # --- AND ---
            case 0x29: # AND imm
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.AND(value)
            case 0x25: # AND zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
                self.ops.AND(value)
            case 0x35: # AND zero,X
                addr = (self.read(self.r.PC) + self.r.X) & 0xFF
                self.r.PC += 1
                value = self.read(addr)
                self.ops.AND(value)
            case 0x2D: # AND abs
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr)
                self.ops.AND(value)
            case 0x3D: # AND abs,X
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.X)
                self.ops.AND(value)
            case 0x39: # AND abs,Y
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.Y)
                self.ops.AND(value)
            case 0x21: # AND (ind,X)
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_x(operand)
                self.ops.AND(value)
            case 0x31: # AND (ind),Y
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_y(operand)
                self.ops.AND(value)
            # --- ORA ---
            case 0x09: # ORA imm
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.ORA(value)
            case 0x05: # ORA zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
                self.ops.ORA(value)
            case 0x15: # ORA zero,X
                addr = (self.read(self.r.PC) + self.r.X) & 0xFF
                self.r.PC += 1
                value = self.read(addr)
                self.ops.ORA(value)
            case 0x0D: # ORA abs
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr)
                self.ops.ORA(value)
            case 0x1D: # ORA abs,X
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.X)
                self.ops.ORA(value)
            case 0x19: # ORA abs,Y
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.Y)
                self.ops.ORA(value)
            case 0x01: # ORA (ind,X)
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_x(operand)
                self.ops.ORA(value)
            case 0x11: # ORA (ind),Y
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_y(operand)
                self.ops.ORA(value)
            # --- EOR ---
            case 0x49: # EOR imm
                value = self.read(self.r.PC)
                self.r.PC += 1
                self.ops.EOR(value)
            case 0x45: # EOR zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
                self.ops.EOR(value)
            case 0x55: # EOR zero,X
                addr = (self.read(self.r.PC) + self.r.X) & 0xFF
                self.r.PC += 1
                value = self.read(addr)
                self.ops.EOR(value)
            case 0x4D: # EOR abs
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr)
                self.ops.EOR(value)
            case 0x5D: # EOR abs,X
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.X)
                self.ops.EOR(value)
            case 0x59: # EOR abs,Y
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr + self.r.Y)
                self.ops.EOR(value)
            case 0x41: # EOR (ind,X)
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_x(operand)
                self.ops.EOR(value)
            case 0x51: # EOR (ind),Y
                operand = self.read(self.r.PC)
                self.r.PC += 1
                value = self.indirect_y(operand)
                self.ops.EOR(value)
            # --- BIT ---
            case 0x24: # BIT zero
                addr = self.read(self.r.PC)
                self.r.PC += 1
                value = self.read(addr)
                self.ops.BIT(value)
            case 0x2C: # BIT abs
                abs_addr = self.get_absolute_addr()
                value = self.read(abs_addr)
                self.ops.BIT(value)
            case _:
                raise Exception(f"Opcode 0x{opcode:02X} is not implemented")