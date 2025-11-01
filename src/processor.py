from typing import Protocol

class Bus(Protocol):
    def read(self, addr: int) -> int:
        ...
    
    def write(self, addr: int, value: int):
        ...


class CPU6502:
    def __init__(self, nes: Bus):
        self.nes = nes
        self.r_A: int = 0
        self.r_X: int = 0
        self.r_Y: int = 0
        self.r_S: int = 0xFF
        self.r_P: int = 0
        self.r_PC: int = 0

    def reset(self):
        lo_pc = self.read(0xFFFC)
        hi_pc = self.read(0xFFFD)
        pc = (hi_pc << 8) | lo_pc
        self.r_PC = pc
        self.r_S = 0xFF

    def read(self, addr: int):
        return self.nes.read(addr)

    def write(self, addr: int, value: int):
        self.nes.write(addr, value)

    def push(self, value: int):
        addr = self.r_S | 0x0100
        self.write(addr, value)
        self.r_S = (self.r_S - 1) & 0xFF

    def pull(self) -> int:
        self.r_S = (self.r_S + 1) & 0xFF
        return self.read(self.r_S | 0x0100)

    def zero_page(self, addr: int):
        return self.nes.read(addr & 0xFF)
    
    def get_absolute_addr(self):
        lo_byte = self.read(self.r_PC)
        self.r_PC += 1
        hi_byte = self.read(self.r_PC)
        self.r_PC += 1
        abs_addr = (hi_byte << 8) | lo_byte
        return abs_addr
    
    def indirect_x(self, operand: int):
        addr = operand + self.r_X
        lo_byte = self.read(addr)
        hi_byte = self.read(addr + 1)
        abs_addr = (hi_byte << 8) | lo_byte
        return self.read(abs_addr)
    
    def indirect_y(self, operand: int):
        lo_byte = self.read(operand)
        hi_byte = self.read(operand + 1)
        abs_addr = (hi_byte << 8) | lo_byte
        return self.read(abs_addr + self.r_Y)

    def get_status_flag(self, flag: int):
        return bool(self.r_P & (1 << flag))

    def get_zero(self):
        return self.get_status_flag(1)

    def get_negative(self):
        return self.get_status_flag(7)
    
    def set_status_flag(self, flag: int, bool: bool):
        if bool:
            self.r_P |= (1 << flag)
        else:
            self.r_P &= ~(1 << flag)

    def set_zero(self, value: int):
        value &= 0xFF
        self.set_status_flag(1, value == 0)

    def set_interrupt_diable(self, bool: bool):
        self.set_status_flag(2, bool) 

    def set_negative(self, value: int):
        value &= 0xFF
        self.set_status_flag(7, bool(value & 0x80))

    def LDA(self, value: int):
        self.r_A = value
        self.set_zero(value)
        self.set_negative(value)

    def LDX(self, value: int):
        self.r_X = value
        self.set_zero(value)
        self.set_negative(value)

    def LDY(self, value: int):
        self.r_Y = value
        self.set_zero(value)
        self.set_negative(value)

    def CMP(self, value: int):
        result = self.r_A - value
        self.set_zero(result)
        self.set_negative(result)

    def get_branch_offset(self):
        offset = self.read(self.r_PC)
        self.r_PC += 1
        if offset & 0x80:
            # If the signed bit is set, the the value should be negative.
            offset = offset - 256
        print(f"{offset=:02X}")
        return offset

    def execute(self):
        opcode = self.read(self.r_PC)
        print(f"Executing {opcode:02X}")
        self.r_PC += 1
        if opcode == 0xE0: # CPX imm
            value = self.r_X - self.read(self.r_PC)
            self.r_PC += 1
            self.set_zero(value)
            self.set_negative(value)
        elif opcode == 0xC9: # CMP imm
            value = self.read(self.r_PC)
            self.r_PC += 1
            self.CMP(value)
        elif opcode == 0xC5: # CMP zero
            addr = self.read(self.r_PC)
            self.r_PC += 1
            value = self.read(addr)
            self.CMP(value)
        elif opcode == 0xA5: # LDA zero page
            addr = self.read(self.r_PC)
            self.r_PC += 1
            value = self.zero_page(addr)
            print(f"LDA zero, {addr=:02X} {value=:02X}")
            self.LDA(value)
        elif opcode == 0xA9:
            value = self.read(self.r_PC)
            self.r_PC += 1
            self.LDA(value)
        elif opcode == 0xAD: # LDA abs
            abs_addr = self.get_absolute_addr()
            value = self.read(abs_addr)
            self.LDA(value)
        elif opcode == 0xBD: # LDA abs x
            abs_addr = self.get_absolute_addr()
            print(f"{abs_addr=:04X} {self.r_X:02X}")
            value = self.read(abs_addr + self.r_X)
            self.LDA(value)
        elif opcode == 0xB1: # LDA ind y
            operand = self.read(self.r_PC)
            self.r_PC += 1
            value = self.indirect_y(operand)
            print(f"LDA ind y {value=}")
            self.LDA(value)
        elif opcode == 0x8D: # STA abs
            abs_addr = self.get_absolute_addr()
            self.nes.write(abs_addr, self.r_A)
        elif opcode == 0x85: # STA zero
            addr = self.read(self.r_PC)
            self.r_PC += 1
            self.write(addr, self.r_A)
        elif opcode == 0x8E: # STX abs
            abs_addr = self.get_absolute_addr()
            print(f"STX abs. {abs_addr=:04X} {self.r_X=:02X}")
            self.nes.write(abs_addr, self.r_X)
        elif opcode == 0x8C: # STY abs
            abs_addr = self.get_absolute_addr()
            self.nes.write(abs_addr, self.r_Y)
        elif opcode == 0xA2: # LDX imm
            value = self.read(self.r_PC)
            self.r_PC += 1
            self.LDX(value)
        elif opcode == 0xA0: # LDY imm
            value = self.read(self.r_PC)
            self.r_PC += 1
            self.LDY(value)
        elif opcode == 0xE6: # INC zero
            addr = self.read(self.r_PC)
            self.r_PC += 1
            value = self.zero_page(addr)
            value += 1
            self.set_zero(value)
            self.set_negative(value)
            self.write(addr, value & 0xFF)
        elif opcode == 0xCA: # DEX
            self.r_X = (self.r_X - 1) & 0xFF
            print(f"DEX {self.r_X}")
            self.set_negative(self.r_X)
            self.set_zero(self.r_X)
        elif opcode == 0xE8: # INX
            self.r_X = (self.r_X + 1) & 0xFF
            self.set_negative(self.r_X)
            self.set_zero(self.r_X)
        elif opcode == 0x88: # DEY
            self.r_Y = (self.r_Y - 1) & 0xFF
            # if self.r_Y == 0:
            #     exit() 
            self.set_negative(self.r_Y)
            self.set_zero(self.r_Y)
        elif opcode == 0xC8: # INY
            print(f"INY {self.r_Y=:02X}")
            self.r_Y = (self.r_Y + 1) & 0xFF
            self.set_negative(self.r_Y)
            self.set_zero(self.r_Y)
        elif opcode == 0x10: # Branch if plus
            offset = self.get_branch_offset()
            if not self.get_negative():
                print("Branching")
                self.r_PC += offset
        elif opcode == 0xF0: # Branch if equal
            offset = self.get_branch_offset()
            if self.get_zero():
                print("Branching")
                self.r_PC += offset
        elif opcode == 0xD0: # Branch if not equal
            offset = self.get_branch_offset()
            if not self.get_zero():
                print("Branching")
                self.r_PC += offset
        elif opcode == 0x78:
            self.set_interrupt_diable(True)
        elif opcode == 0xD8:
            self.set_status_flag(3, False)
        elif opcode == 0x9A:
            self.r_S = self.r_X
        elif opcode == 0x20: # JSR
            abs_addr = self.get_absolute_addr()
            return_addr = self.r_PC - 1
            self.push((return_addr >> 8) & 0xFF)
            self.push(return_addr & 0x00FF)
            print(f"Jumping to {abs_addr:04X}")
            self.r_PC = abs_addr
        elif opcode == 0x60: # RTS
            print(f"RTS. {self.r_S=:02X}")
            lo_byte = self.pull()
            hi_byte = self.pull()
            addr = (hi_byte << 8) | lo_byte
            print(f"Returning to {addr+1:04X}")
            self.r_PC = addr + 1
        else:
            raise Exception(f"Opcode 0x{opcode:02X} is not implemented")