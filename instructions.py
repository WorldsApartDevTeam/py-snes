
class Instruction:
    opcodes=[]

    def __init__(self, opcode):
        self.opcode = opcode

    def __repr__(self):
        return "UNK"

    def fetch(self, cpu):
        return 0 # return parameter byte count (or -1 for jump instructions)

    def execute(self, cpu):
        return 2 # return cycle count

def nextAddr(addr, off=1):
    bank = addr & 0xFF0000
    addrlo = addr & 0xFFFF
    return bank | (addrlo + off) & 0xFFFF

def read16(addr, cpu):
    return cpu.mem.read(addr) | (cpu.mem.read(nextAddr(addr)) << 8)

def read24(addr, cpu):
    data = cpu.mem.read(addr); addr = nextAddr(addr)
    data |= cpu.mem.read(addr) << 8; addr = nextAddr(addr)
    data |= cpu.mem.read(addr) << 16
    return data

def getAddr(offset, mode, cpu, is_pb):
    if is_pb:
        bankreg = cpu.PB
    else:
        bankreg = cpu.DB

    x = cpu.X
    y = cpu.Y
#    if cpu.get_flag("X"):
#        if x & 0x80:
#            x |= 0xFF00
#        if y & 0x80:
#            y |= 0xFF00

    if mode == "imm":
        return 0 # means nothing to getAddr
    elif mode == "abs": # absolute
        return (bankreg << 16) | (offset & 0xFFFF)
    elif mode == "absl": # absolute long
        return offset & 0xFFFFFF
    elif mode == "absx": # absolute indexed X
        return (bankreg << 16) | ((offset + x) & 0xFFFF)
    elif mode == "absy": # absolute indexed Y
        return (bankreg << 16) | ((offset + y) & 0xFFFF)
    elif mode == "abslx": # absolute long indexed X
        return nextAddr(offset, x)
    elif mode == "absly": # absolute long indexed Y (possibly unavailable)
        return nextAddr(offset, y)
    elif mode == "rel": # relative (short)
        return (bankreg << 16) | ((offset + cpu.PC) & 0xFFFF)
    elif mode == "rell": # relative (long)
        return nextAddr(offset, cpu.PC)
    elif mode == "dp": # direct page
        return (cpu.DP + offset) & 0xFFFF
    elif mode == "dpx": # direct page indexed X
        return (cpu.DP + offset + x) & 0xFFFF
    elif mode == "dpy": # direct page indexed Y
        return (cpu.DP + offset + y) & 0xFFFF
    elif mode == "absi": # absolute indirect
        ind_addr = getAddr(offset, "abs", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ind_data
    elif mode == "absil": # absolute indirect long
        ind_addr = getAddr(offset, "abs", cpu, is_pb)
        ind_data = read24(ind_addr, cpu)
        return ind_data
    elif mode == "absxi": # absolute (indexed X) indirect
        ind_addr = getAddr(offset, "absx", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ind_data
    elif mode == "absyi": # absolute (indexed Y) indirect
        ind_addr = getAddr(offset, "absy", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ind_data
    elif mode == "dpi": # direct page indirect
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ind_data
    elif mode == "dpxi": # direct-page (indexed X) indirect
        ind_addr = getAddr(offset, "dpx", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ind_data
    elif mode == "dpyi": # direct-page (indexed Y) indirect
        ind_addr = getAddr(offset, "dpy", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ind_data
    elif mode == "dpix": # direct-page indirect, indexed X
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ((ind_data + x) & 0xFFFF)
    elif mode == "dpiy": # direct-page indirect, indexed Y
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ((ind_data + y) & 0xFFFF)
    elif mode == "dpil": # direct-page indirect long
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = read24(ind_addr, cpu)
        return ind_data
    elif mode == "dpixl": # direct-page indirect, indexed X, long
        return nextAddr(getAddr(offset, "dpil", cpu, is_pb), x)
    elif mode == "dpiyl": # direct-page indirect, indexed Y, long
        return nextAddr(getAddr(offset, "dpil", cpu, is_pb), y)
    elif mode == "sr": # stack relative
        return (offset + cpu.S) & 0xFFFF
    elif mode == "srix": # stack relative indirect, indexed X
        ind_addr = getAddr(offset, "sr", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ((ind_data + x) & 0xFFFF)
    elif mode == "sriy": # stack relative indirect, indexed Y
        ind_addr = getAddr(offset, "sr", cpu, is_pb)
        ind_data = read16(ind_addr, cpu)
        return (bankreg << 16) | ((ind_data + x) & 0xFFFF)

def getAddrFormat(mode):
    if mode == 'imm':
        return '#$%02x'
    elif mode in ['rel', 'dp']:
        return '$%02x'
    elif mode in ['rell', 'abs']:
        return '$%04x'
    elif mode == 'absl':
        return '$%06x'
    elif mode == 'dpx':
        return '$%02x,X'
    elif mode == 'dpy':
        return '$%02x,Y'
    elif mode == 'absx':
        return '$%04x,X'
    elif mode == 'absy':
        return '$%04x,Y'
    elif mode == 'dpi':
        return '($%02x)'
    elif mode == 'dpxi':
        return '($%02x,X)'
    elif mode == 'dpyi':
        return '($%02x,Y)'
    elif mode == 'dpix':
        return '($%02x),X'
    elif mode == 'dpiy':
        return '($%02x),Y'
    elif mode == 'dpil':
        return '[$%02x]'
    elif mode == 'dpixl':
        return '[$%02x],X'
    elif mode == 'dpiyl':
        return '[$%02x],Y'
    elif mode == 'abslx':
        return '$%06x,X'
    elif mode == 'absly':
        return '$%06x,Y'
    elif mode == 'sr':
        return '$%02x,S'
    elif mode == 'srix':
        return '($%02x,S),X'
    elif mode == 'sriy':
        return '($%02x,S),Y'
    elif mode == 'absi':
        return '($%04x)'
    elif mode == 'absil':
        return '[$%04x]'
    elif mode == 'absxi':
        return '($%04x,X)'
    elif mode == 'absyi':
        return '($%04x,Y)'

class ADC(Instruction):
    opcodes = [
        0x61, 0x63, 0x65, 0x67, 0x69, 0x6D, 0x6F, 0x71, 0x72, 0x73, 0x75, 0x77,
        0x79, 0x7D, 0x7F
    ]
    opcode_info = {
        0x61: {'mode': 'dpxi', 'base-cycles': 6}, # 1B op     ^1^2
        0x63: {'mode': 'sr',   'base-cycles': 4}, # 1B op     ^1
        0x65: {'mode': 'dp',   'base-cycles': 3}, # 1B op     ^1^2
        0x67: {'mode': 'dpil', 'base-cycles': 6}, # 1B op     ^1^2
        0x69: {'mode': 'imm',  'base-cycles': 2}, # 1(+1)B op ^1
        0x6D: {'mode': 'abs',  'base-cycles': 4}, # 2B op     ^1
        0x6F: {'mode': 'absl', 'base-cycles': 5}, # 3B op     ^1
        0x71: {'mode': 'dpiy', 'base-cycles': 5}, # 1B op     ^1^2^3
        0x72: {'mode': 'dpi',  'base-cycles': 5}, # 1B op     ^1^2
        0x73: {'mode': 'sriy', 'base-cycles': 7}, # 1B op     ^1
        0x75: {'mode': 'dpx',  'base-cycles': 4}, # 1B op     ^1^2
        0x77: {'mode': 'dpixl','base-cycles': 6}, # 1B op     ^1^2
        0x79: {'mode': 'absy', 'base-cycles': 4}, # 2B op     ^1  ^3
        0x7D: {'mode': 'absx', 'base-cycles': 4}, # 2B op     ^1  ^3
        0x7F: {'mode': 'absil','base-cycles': 5}, # 3B op     ^1
        # ^1: all
        # ^2: [0x61, 0x65, 0x67, 0x71, 0x72, 0x75, 0x77]
        # ^3: [0x71, 0x79, 0x7D]
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.operand = 0
        self.bc = False # boundary cross (^3)
        self.op_literal = 0 # actual operand in code (not the value)

    def __repr__(self):
        return "ADC " + (getAddrFormat(self.opcode_info[self.opcode]['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.opcode == 0x69: # imm
            if cpu.get_flag("M"):
                self.operand = cpu.mem.read(off)
                self.op_literal = self.operand
                return 1
            else:
                self.operand = read16(off, cpu)
                self.op_literal = self.operand
                return 2
        else:
            if self.opcode in [0x61, 0x63, 0x65, 0x67, 0x71, 0x72, 0x73, 0x75, 0x77]:
                param = cpu.mem.read(off) # 1-byte opcodes
                width = 1
            elif self.opcode in [0x6D, 0x79, 0x7D]:
                param = read16(off, cpu)  # 2-byte opcodes
                width = 2
            else:
                param = read24(off, cpu)  # 3-byte opcodes
                width = 3
            mode = self.opcode_info[self.opcode]['mode']
            addr = getAddr(param, mode, cpu, False)

            # Find boundary crossing points
            if self.operand == 0x71: # dpiy
                self.bc = ((addr & 0xFF) - cpu.Y) & 0xFF00 != 0
            elif self.operand == 0x79: # absy
                self.bc = ((param & 0xFF) + cpu.Y) & 0xFF00 != 0
            elif self.operand == 0x7D: # absx
                self.bc = ((param & 0xFF) + cpu.Y) & 0xFF00 != 0

            if cpu.get_flag("M"):
                self.operand = cpu.mem.read(addr) # 1-byte
            else:
                self.operand = read16(addr, cpu) # 2-byte
            self.op_literal = param
            return width

    def _cycles(self, cpu):
        cyc = self.opcode_info[self.opcode]['base-cycles']
        # ^1: +1 if !M
        if not cpu.get_flag("M"):
            cyc += 1
        # ^2: +1 if LSB of DP != 0 (because DP is 16-bit for some absurd reason)
        if self.opcode in [0x61, 0x65, 0x67, 0x71, 0x72, 0x75, 0x77] \
                and cpu.DP & 0xFF:
            cyc += 1
        # ^3: +1 if adding index crosses page boundary or !X
        if self.opcode in [0x71, 0x79, 0x7D] \
                and (not cpu.get_flag("X") or self.bc):
            cyc += 1
        return cyc

    def execute(self, cpu):
        if cpu.get_flag("M"):
            cpu.A = (cpu.A + self.operand) & 0xFF
        else:
            cpu.A = (cpu.A + self.operand) & 0xFFFF
        return self._cycles(cpu)



def _registerInstruction(instrClass, reg):
    for c in instrClass.opcodes:
        reg[c] = instrClass


def getAllInstructions():
    reg = {}
    _registerInstruction(ADC, reg)
    return reg
