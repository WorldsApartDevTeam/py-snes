
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
    elif mode == "rel": # relative (short) -- 8 bit addition
        return (bankreg << 16) | (cpu.PC & 0xFF00) | (((cpu.PC & 0xFF) + offset) & 0xFF)
    elif mode == "rell": # relative (long) -- 16 bit addition
        return nextAddr(cpu.PC, offset)
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
    if mode == 'imm':             # 1B
        return '#$%02x'
    elif mode in ['rel', 'dp']:   # 1B
        return '$%02x'
    elif mode in ['rell', 'abs']: #    2B
        return '$%04x'
    elif mode == 'absl':          #       3B
        return '$%06x'
    elif mode == 'dpx':           # 1B
        return '$%02x,X'
    elif mode == 'dpy':           # 1B
        return '$%02x,Y'
    elif mode == 'absx':          #    2B
        return '$%04x,X'
    elif mode == 'absy':          #    2B
        return '$%04x,Y'
    elif mode == 'dpi':           # 1B
        return '($%02x)'
    elif mode == 'dpxi':          # 1B
        return '($%02x,X)'
    elif mode == 'dpyi':          # 1B
        return '($%02x,Y)'
    elif mode == 'dpix':          # 1B
        return '($%02x),X'
    elif mode == 'dpiy':          # 1B
        return '($%02x),Y'
    elif mode == 'dpil':          # 1B
        return '[$%02x]'
    elif mode == 'dpixl':         # 1B
        return '[$%02x],X'
    elif mode == 'dpiyl':         # 1B
        return '[$%02x],Y'
    elif mode == 'abslx':         #       3B
        return '$%06x,X'
    elif mode == 'absly':         #       3B
        return '$%06x,Y'
    elif mode == 'sr':            # 1B
        return '$%02x,S'
    elif mode == 'srix':          # 1B
        return '($%02x,S),X'
    elif mode == 'sriy':          # 1B
        return '($%02x,S),Y'
    elif mode == 'absi':          #    2B
        return '($%04x)'
    elif mode == 'absil':         #    2B
        return '[$%04x]'
    elif mode == 'absxi':         #    2B
        return '($%04x,X)'
    elif mode == 'absyi':         #    2B
        return '($%04x,Y)'

def getParameter(addr, mode, cpu, two_byte, is_pb):
    # print("getParameter from %06x mode=%s two_byte=%d use_pb=%d" % (
    #         addr, mode, two_byte, is_pb))
    if mode == 'imm':
        if two_byte: # 16-bit immediate
            pm = read16(addr, cpu)
            return (pm, 2, pm)
        else:
            pm = cpu.mem.read(addr)
            return (pm, 1, pm)
    else:
        if mode in ['rel', 'dp', 'dpx', 'dpy', 'dpi', 'dpxi', 'dpyi', 'dpix',
                    'dpiy', 'dpil', 'dpixl', 'dpiyl', 'sr', 'srix', 'sriy']:
            # 1-byte addressed/indirect
            param = cpu.mem.read(addr)
            width = 1
        elif mode in ['rell', 'abs', 'absx', 'absy', 'absi', 'absil', 'absxi',
                        'absyi']:
            param = read16(addr, cpu)
            width = 2
        else:
            param = read24(addr, cpu)
            width = 3

        addr2 = getAddr(param, mode, cpu, is_pb)
        if two_byte:
            return (read16(addr2, cpu), width, param)
        else:
            return (cpu.mem.read(addr2), width, param)


def cycles(base, timing, cpu, bound_cross=False, branch_taken=False):
    cyc = base
    # ^1: +1 for M=0
    if 1 in timing and not cpu.get_flag("M"):
        cyc += 1
    # ^2: +1 if low byte of DP != 0
    if 2 in timing and cpu.DP & 0xFF:
        cyc += 1
    # ^3: +1 if page boundary cross or X=0
    if 3 in timing and (bound_cross or not cpu.get_flag("X")):
        cyc += 1
    # ^4: +2 if M=0
    if 4 in timing and not cpu.get_flag("M"):
        cyc += 2
    # ^5: +1 if branch taken
    if 5 in timing and branch_taken:
        cyc += 1
    # ^6: [emulation mode specific]
    # ^7: +1 if in native mode (i.e. always)
    if 7 in timing and not cpu.EMU:
        cyc += 1
    # ^8: +1 if X=0
    if 8 in timing and not cpu.get_flag("X"):
        cyc += 1
    # ^9, ^10: [shutdown instructions]
    return cyc


class ArithmeticInstruction(Instruction):

    def __init__(self, opcode):
        super().__init__(opcode)
        self.operand = 0
        self.bc = False # boundary cross (^3)
        self.op_literal = 0 # actual operand in code (not the value)

    #########################
    # Override These        #

    def _name(self):
        "What is this opcode called (for disassembly purposes)"
        return "[arithmetic]"

    def _op(self, a, b):
        "What does this opcode do?"
        return a + b

    def _flags(self):
        """What flags does this opcode affect?
        Arithmetic ops (ADC, SUB) affect Z, C, V, and N
        Bitwise ops (AND, ORA) affect Z and N only"""
        return ["Z", "C", "V", "N"]

    #                       #
    #########################

    def __repr__(self):
        return self._name() + " " + (getAddrFormat(self.opcode_info[self.opcode]['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        self.operand, width, param = getParameter(off, \
                            self.opcode_info[self.opcode]['mode'], cpu, \
                            not cpu.get_flag("M"), False)

        mode = self.opcode_info[self.opcode]['mode']
        if mode == 'dpiy': # dpiy
            addr = getAddr(param, mode, cpu, False)
            self.bc = ((addr & 0xFF) - cpu.Y) & 0xFF00 != 0
        elif mode == 'absy': # absy
            self.bc = ((param & 0xFF) + cpu.Y) & 0xFF00 != 0
        elif mode == 'absx': # absx
            self.bc = ((param & 0xFF) + cpu.X) & 0xFF00 != 0

        self.op_literal = param
        return width

    def execute(self, cpu):
        fs = self._flags()
        for f in fs:
            cpu.clear_flag(f)
        a = self._op(cpu.A, self.operand)
        if cpu.get_flag("M"):
            hi = cpu.A & 0x80
            cpu.A = a & 0xFF
            mask = 0xFF
        else:
            hi = cpu.A & 0x8000
            cpu.A = a & 0xFFFF
            mask = 0xFFFF

        if cpu.A == 0 and "Z" in fs:
            cpu.set_flag("Z")
        if a > mask and "C" in fs:
            cpu.set_flag("C")
        if cpu.A & (mask//2 + 1) and "N" in fs:
            cpu.set_flag("N")
        if (cpu.A & (mask//2 + 1)) != hi and "V" in fs:
            cpu.set_flag("V")
        return cycles(self.opcode_info[self.opcode]['bc'], \
                self.opcode_info[self.opcode]['timing'], cpu, bound_cross=self.bc)


class ADC(ArithmeticInstruction):
    opcodes = [
        0x61, 0x63, 0x65, 0x67, 0x69, 0x6D, 0x6F, 0x71, 0x72, 0x73, 0x75, 0x77,
        0x79, 0x7D, 0x7F
    ]
    opcode_info = {
        0x61: {'name': 'ADC', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x63: {'name': 'ADC', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0x65: {'name': 'ADC', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0x67: {'name': 'ADC', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x69: {'name': 'ADC', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [1]},
        0x6D: {'name': 'ADC', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0x6F: {'name': 'ADC', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0x71: {'name': 'ADC', 'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0x72: {'name': 'ADC', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0x73: {'name': 'ADC', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0x75: {'name': 'ADC', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0x77: {'name': 'ADC', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x79: {'name': 'ADC', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x7D: {'name': 'ADC', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x7F: {'name': 'ADC', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "ADC"

    def _op(self, a, b):
        return a + b

    def _flags(self):
        return ["Z", "C", "V", "N"]

class AND(ArithmeticInstruction):
    opcodes = [0x21, 0x23, 0x25, 0x27, 0x29, 0x2D, 0x2F, 0x31, 0x32, 0x33, 0x35,
                0x37, 0x39, 0x3D, 0x3F]
    opcode_info = {
        0x21: {'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x23: {'mode': 'sr',   'bc': 4, 'width': 1, 'timing': [1]},
        0x25: {'mode': 'dp',   'bc': 3, 'width': 1, 'timing': [1, 2]},
        0x27: {'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x29: {'mode': 'imm',  'bc': 2, 'width': 0, 'timing': [1]},
        0x2D: {'mode': 'abs',  'bc': 4, 'width': 2, 'timing': [1]},
        0x2F: {'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0x31: {'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0x32: {'mode': 'dpi',  'bc': 5, 'width': 1, 'timing': [1, 2]},
        0x33: {'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0x35: {'mode': 'dpx',  'bc': 4, 'width': 1, 'timing': [1, 2]},
        0x37: {'mode': 'dpiyl','bc': 6, 'width': 1, 'timing': [1, 2]},
        0x39: {'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x3D: {'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x3F: {'mode': 'abslx','bc': 5, 'width': 3, 'timing': [1]}
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "AND"

    def _op(self, a, b):
        return a & b

    def _flags(self):
        return ["N", "Z"]


class ASL(Instruction):
    opcodes = [0x06, 0x0A, 0x0E, 0x16, 0x1E]
    opcode_info = {
        0x06: {'mode': 'dp',   'base-cycles': 5, 'width': 1, 'timing': [2, 4]},
        0x0A: {'mode': 'acc',  'base-cycles': 2, 'width': 0, 'timing': []},
        0x0E: {'mode': 'abs',  'base-cycles': 6, 'width': 2, 'timing': [4]},
        0x16: {'mode': 'dpx',  'base-cycles': 6, 'width': 1, 'timing': [2, 4]},
        0x1E: {'mode': 'absx', 'base-cycles': 7, 'width': 2, 'timing': [4]}
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.operand = 0
        self.op_literal = 0 # actual operand in code (not the value)

    def __repr__(self):
        if self.opcode == 0x0A:
            return "ASL A"
        else:
            return "ASL " + (getAddrFormat(self.opcode_info[self.opcode]['mode']) % self.op_literal)

    def fetch(self, cpu):
        if self.opcode == 0x0A:
            return 0

        off = nextAddr(cpu.get_pc())
        if self.opcode_info[self.opcode]['width'] == 1:
            param = cpu.mem.read(off)
            width = 1
        else:
            param = read16(off, cpu)
            width = 2

        mode = self.opcode_info[self.opcode]['mode']
        self.addr = getAddr(param, mode, cpu, False)
        self.op_literal = param
        return width

    def _cycles(self, cpu):
        cyc = self.opcode_info[self.opcode]['base-cycles']
        if 2 in self.opcode_info[self.opcode]['timing'] \
                and cpu.DP & 0xFF:
            cyc += 1
        if 4 in self.opcode_info[self.opcode]['timing'] \
                and not cpu.get_flag("M"):
            cyc += 2
        return cyc

    def execute(self, cpu):
        cpu.clear_flag("N")
        cpu.clear_flag("Z")
        cpu.clear_flag("C")
        if self.opcode == 0x0A:
            # Shift accumulator (8 or 16 bits)
            if cpu.get_flag("M"):
                if cpu.A & 0x80:  cpu.set_flag("C")
                cpu.A = (cpu.A << 1) & 0xFF
                if cpu.A == 0:  cpu.set_flag("Z")
                elif cpu.A & 0x80:  cpu.set_flag("N")
            else:
                if cpu.A & 0x8000: cpu.set_flag("C")
                cpu.A = (cpu.A << 1) & 0xFFFF
                if cpu.A == 0: cpu.set_flag("Z")
                elif cpu.A & 0x8000:  cpu.set_flag("N")
        else:
            if cpu.get_flag("M"):
                # Shift memory in-place (8 bits)
                val = cpu.mem.read(self.addr)
                if val & 0x80: cpu.set_flag("C")
                val = (val << 1) & 0xFF
                cpu.mem.write(self.addr, val)
                if val == 0: cpu.set_flag("Z")
                elif val & 0x80: cpu.set_flag("N")
            else:
                val = read16(self.addr, cpu)
                if val & 0x8000: cpu.set_flag("C")
                val = (val << 1) & 0xFFFF
                cpu.mem.write(self.addr, val & 0xFF)
                cpu.mem.write(nextAddr(self.addr), (val >> 8) & 0xFF)
                if val == 0: cpu.set_flag("Z")
                elif val & 0x8000: cpu.set_flag("N")
        return cycles(self.opcode_info[self.opcode]['bc'], \
                self.opcode_info[self.opcode]['timing'], cpu)


class BranchInstruction(Instruction):
    # opcodes = [0x90],
    # opcode_info = {
    #     0x90: {'mode': 'rel', 'base-cycles': 2, 'width': 1, 'timing': [5, 6]}
    # }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.addr = 0
        self.op_literal = 0 # actual operand in code (not the value)

    def _name(self):
        return "[BRANCH]"

    def _doBranch(self, cpu):
        return False

    def __repr__(self):
        return self._name() + " " + (getAddrFormat('rel') % self.op_literal)

    def fetch(self, cpu):
        # always read this for the disasm
        self.op_literal = cpu.mem.read(nextAddr(cpu.get_pc()))
        if not self._doBranch(cpu):
            return 1 # skip this branch
        self.addr = getAddr(self.op_literal, 'rel', cpu, True) & 0xFFFF
        return -1 # we are branching; don't advance the PC

    def execute(self, cpu):
        if not self._doBranch(cpu):
            return 2 # no branch today
        cpu.PC = self.addr # Branch
        return 3


class BCC(BranchInstruction):
    opcodes = [0x90]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BCC"

    def _doBranch(self, cpu):
        return not cpu.get_flag("C")


class BCS(BranchInstruction):
    opcodes = [0xB0]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BCS"

    def _doBranch(self, cpu):
        return cpu.get_flag("C")


class BEQ(BranchInstruction):
    opcodes = [0xF0]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BEQ"

    def _doBranch(self, cpu):
        return cpu.get_flag("Z")


class BIT(Instruction): # The weird one. People find this useful in all sorts of ways
    opcodes = [0x24, 0x2C, 0x34, 0x3C, 0x89]
    opcode_info = {
        0x24: {'mode': 'dp',   'base-cycles': 3, 'width': 1, 'timing': [1, 2]},
        0x2C: {'mode': 'abs',  'base-cycles': 4, 'width': 2, 'timing': [1]},
        0x34: {'mode': 'dpx',  'base-cycles': 4, 'width': 1, 'timing': [1, 2]},
        0x3C: {'mode': 'absx', 'base-cycles': 4, 'width': 2, 'timing': [1, 3]},
        0x89: {'mode': 'imm',  'base-cycles': 2, 'width': 0, 'timing': [1]}
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.addr = 0
        self.op_literal = 0 # actual operand in code (not the value)

    def __repr__(self):
        return "BIT " + (getAddrFormat(self.opcode_info[self.opcode]['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        inf = self.opcode_info[self.opcode]

        self.operand, width, param = getParameter(off, inf['mode'], cpu, \
                            not cpu.get_flag("M"), False)

        if mode == 'absx': # absx
            self.bc = ((param & 0xFF) + cpu.X) & 0xFF00 != 0

        self.op_literal = param
        return width

    def execute(self, cpu):
        cpu.clear_flag("Z")
        cpu.clear_flag("N")
        cpu.clear_flag("V")
        if self.operand & cpu.A == 0:
            cpu.set_flag("Z")
        if cpu.get_flag("M"):
            if self.operand & 0x80:
                cpu.set_flag("N")
            if self.operand & 0x40:
                cpu.set_flag("V")
        else:
            if self.operand & 0x8000:
                cpu.set_flag("N")
            if self.operand & 0x4000:
                cpu.set_flag("V")

        return cycles(self.opcode_info[self.opcode]['base-cycles'], \
                self.opcode_info[self.opcode]['timing'], cpu, bound_cross=self.bc)


class BMI(BranchInstruction):
    opcodes = [0x30]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BMI"

    def _doBranch(self, cpu):
        return cpu.get_flag("N")


class BNE(BranchInstruction):
    opcodes = [0xD0]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BNE"

    def _doBranch(self, cpu):
        return not cpu.get_flag("Z")


class BPL(BranchInstruction):
    opcodes = [0x10]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BPL"

    def _doBranch(self, cpu):
        return not cpu.get_flag("N")


class BRA(BranchInstruction):
    opcodes = [0x80]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BRA"

    def _doBranch(self, cpu):
        return True


class BRK(Instruction):
    #####################################################################################
    # Unimplemented!
    pass


class BRL(Instruction):
    opcodes = [0x82]

    def __init__(self, opcode):
        super().__init__(opcode)
        self.addr = 0
        self.op_literal = 0 # actual operand in code (not the value)


    def __repr__(self):
        return "BRL " + (getAddrFormat('rell') % self.op_literal)

    def fetch(self, cpu):
        # always read this for the disasm
        self.op_literal = read16(nextAddr(cpu.get_pc()), cpu)
        self.addr = getAddr(self.op_literal, 'rell', cpu, True) & 0xFFFF
        return -1 # we are branching; don't advance the PC

    def execute(self, cpu):
        cpu.PC = self.addr # Branch
        return 4


class BVC(BranchInstruction):
    opcodes = [0x50]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BVC"

    def _doBranch(self, cpu):
        return not cpu.get_flag("V")


class BVS(BranchInstruction):
    opcodes = [0x70]

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "BVS"

    def _doBranch(self, cpu):
        return cpu.get_flag("V")


class ClearInst(Instruction):
    opcodes = [0x18, 0xD8, 0x58, 0xB8]

    opcode_info = {
        0x18: {'name': "CLC", 'flag': "C"},
        0xD8: {'name': "CLD", 'flag': "D"},
        0x58: {'name': "CLI", 'flag': "I"},
        0xB8: {'name': "CLV", 'flag': "V"}
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def __repr__(self):
        return self.opcode_info[self.opcode]['name']

    def fetch(self, cpu):
        return 0

    def execute(self, cpu):
        cpu.clear_flag(self.opcode_info[self.opcode]['flag'])
        return 2


class CMP(Instruction):
    opcodes = [0xC1, 0xC3, 0xC5, 0xC7, 0xC9, 0xCD, 0xCF, 0xD1, 0xD2, 0xD3, 0xD5,
                0xD7, 0xD9, 0xDD, 0xDF, 0xE0, 0xE4, 0xEC, 0xC0, 0xC4, 0xCC]

    opcode_info = {
        0xC1: {'name': 'CMP', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xC3: {'name': 'CMP', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0xC5: {'name': 'CMP', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0xC7: {'name': 'CMP', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xC9: {'name': 'CMP', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [1]},
        0xCD: {'name': 'CMP', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0xCF: {'name': 'CMP', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0xD1: {'name': 'CMP', 'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0xD2: {'name': 'CMP', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0xD3: {'name': 'CMP', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0xD5: {'name': 'CMP', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0xD7: {'name': 'CMP', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xD9: {'name': 'CMP', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0xDD: {'name': 'CMP', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0xDF: {'name': 'CMP', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
        0xE0: {'name': 'CPX', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [8]},
        0xE4: {'name': 'CPX', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [2, 8]},
        0xEC: {'name': 'CPX', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [8]},
        0xC0: {'name': 'CPY', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [8]},
        0xC4: {'name': 'CPY', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [2, 8]},
        0xCC: {'name': 'CPY', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [8]}
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        if self.inf['name'] == 'CMP':
            self.reg = "A"
        elif self.inf['name'] == 'CPX':
            self.reg = "X"
        else:
            self.reg = "Y"
        self.op_literal = 0
        self.operand = 0
        self.bc = False

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        # def getParameter(addr, mode, cpu, two_byte, is_pb):
        # return (cpu.mem.read(addr2), width, param)
        off = nextAddr(cpu.get_pc())
        if self.reg == "A":
            tb = cpu.get_flag("M")
        else:
            tb = cpu.get_flag("X")

        self.operand, width, param = getParameter(off, self.inf['mode'], cpu, tb, False)

        if self.inf['mode'] == 'dpiy': # dpiy
            addr = getAddr(param, self.inf['mode'], cpu, False)
            self.bc = ((addr & 0xFF) - cpu.Y) & 0xFF00 != 0
        elif self.inf['mode'] == 'absy': # absy
            self.bc = ((param & 0xFF) + cpu.Y) & 0xFF00 != 0
        elif self.inf['mode'] == 'absx': # absx
            self.bc = ((param & 0xFF) + cpu.X) & 0xFF00 != 0

        self.op_literal = param
        return width

    def execute(self, cpu):
        # CMP acts exactly like SUB but without changing the accumulator
        if self.reg == "A": w = not cpu.get_flag("M")
        else:               w = not cup.get_flag("X")
        mask = 0xFFFF if w else 0xFF
        hibit = 0x8000 if w else 0x80
        if self.reg == "A":   val = (cpu.A - self.operand)
        elif self.reg == "X": val = (cpu.X - self.operand)
        elif self.reg == "Y": val = (cpu.Y - self.operand)
        cpu.clear_flag("N")
        cpu.clear_flag("Z")
        cpu.clear_flag("C")
        if val > mask:  cpu.set_flag("C")
        val &= mask
        if val & hibit: cpu.set_flag("N")
        if val == 0:    cpu.set_flag("Z")
        return cycles(self.opcode_info[self.opcode]['bc'], \
                self.opcode_info[self.opcode]['timing'], cpu, bound_cross=self.bc)


class COP(Instruction):
    #################################################################################
    # Unimplemented instruction!
    pass


class DEC(Instruction):
    opcodes = [0x3A, 0xC6, 0xCE, 0xD6, 0xDE, 0xCA, 0x88, 0x1A, 0xE6, 0xEE, 0xF6,
                0xFE, 0xE8, 0xC8]
    opcode_info = {
        0x3A: {'name': 'DEA', 'mode': 'acc', 'bc': 2, 'width': 0, 'timing': []},
        0xC6: {'name': 'DEC', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0xCE: {'name': 'DEC', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
        0xD6: {'name': 'DEC', 'mode': 'dpx', 'bc': 6, 'width': 1, 'timing': [2, 4]},
        0xDE: {'name': 'DEC', 'mode': 'absx', 'bc': 7, 'width': 2, 'timing': [4]},
        0xCA: {'name': 'DEX', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
        0x88: {'name': 'DEY', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
        0x1A: {'name': 'INA', 'mode': 'acc', 'bc': 2, 'width': 0, 'timing': []},
        0xE6: {'name': 'INC', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0xEE: {'name': 'INC', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
        0xF6: {'name': 'INC', 'mode': 'dpx', 'bc': 6, 'width': 1, 'timing': [2, 4]},
        0xFE: {'name': 'INC', 'mode': 'absx', 'bc': 7, 'width': 2, 'timing': [4]},
        0xE8: {'name': 'INX', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
        0xC8: {'name': 'INY', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        self.op_literal = 0
        self.addr = 0

    def __repr__(self):
        if self.inf['width'] == 0:
            return self.inf['name']
        else:
            return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.inf['width'] == 0:
            # Register operations don't need fetch
            return 0
        # non-register modes: [dp, dpx, abs, absx]
        if self.inf['width'] == 1:
            param = cpu.mem.read(off)
            w = 1
        else:
            param = read16(off)
            w = 2

        self.addr = getAddr(param, self.inf['mode'], cpu, False)
        self.op_literal = param
        return w

    def _op(self, a):
        if 'IN' in self.inf['name']:
            return a+1
        else:
            return a-1

    def execute(self, cpu):

        if self.inf['name'][2] == 'A': # DEA, INA
            mask = 0xFF if cpu.get_flag("M") else 0xFFFF
            cpu.A = self._op(cpu.A) & mask
            val = cpu.A
        elif self.inf['name'][2] == 'X': # DEX
            mask = 0xFF if cpu.get_flag("X") else 0xFFFF
            cpu.X = self._op(cpu.X) & mask
            val = cpu.X
        elif self.inf['name'][2] == 'Y': # DEY
            mask = 0xFF if cpu.get_flag("X") else 0xFFFF
            cpu.Y = self._op(cpu.Y) & mask
            val = cpu.Y
        else:
            if cpu.get_flag("M"):
                # 8-bit
                mask = 0xFF
                val = self._op(cpu.mem.read(self.addr)) & mask
                cpu.mem.write(self.addr, val)
            else:
                mask = 0xFFFF
                val = self._op(read16(self.addr, cpu)) & mask
                cpu.mem.write(self.addr, val & 0xFF)
                cpu.mem.write(self.addr+1, (val >> 8) & 0xFF)
        cpu.clear_flag("N")
        cpu.clear_flag("Z")
        if val & (mask//2 + 1): # mask//2 + 1 => 0x80 or 0x8000
            cpu.set_flag("N")
        elif val == 0:
            cpu.set_flag("Z")
        return cycles(self.opcode_info[self.opcode]['bc'], \
                self.opcode_info[self.opcode]['timing'], cpu)


class EOR(ArithmeticInstruction):
    opcodes = [0x41, 0x43, 0x45, 0x47, 0x49, 0x4D, 0x4F, 0x51, 0x52, 0x53, 0x55,
                0x57, 0x59, 0x5D, 0x5F]

    opcode_info = {
        0x41: {'name': 'EOR', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x43: {'name': 'EOR', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0x45: {'name': 'EOR', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0x47: {'name': 'EOR', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x49: {'name': 'EOR', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [1]},
        0x4D: {'name': 'EOR', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0x4F: {'name': 'EOR', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0x51: {'name': 'EOR', 'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0x52: {'name': 'EOR', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0x53: {'name': 'EOR', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0x55: {'name': 'EOR', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0x57: {'name': 'EOR', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x59: {'name': 'EOR', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x5D: {'name': 'EOR', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x5F: {'name': 'EOR', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "EOR"

    def _op(self, a, b):
        return a ^ b

    def _flags(self):
        return ["N", "Z"]


class JMP(Instruction):
    opcodes = [0x4C, 0x5C, 0x6C, 0x7C, 0xDC]
    opcode_info = {
        0x4C: {'name': 'JMP', 'mode': 'abs', 'bc': 3, 'width': 2, 'timing': []},
        0x5C: {'name': 'JML', 'mode': 'absl', 'bc': 4, 'width': 3, 'timing': []},
        0x6C: {'name': 'JMP', 'mode': 'absi', 'bc': 5, 'width': 2, 'timing': []},
        0x7C: {'name': 'JMP', 'mode': 'absxi', 'bc': 6, 'width': 2, 'timing': []},
        0xDC: {'name': 'JML', 'mode': 'absil', 'bc': 6, 'width': 2, 'timing': []},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.addr = 0
        self.op_literal = 0
        self.inf = self.opcode_info[self.opcode]

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.inf['width'] == 2:
            self.op_literal = read16(off, cpu)
        else:
            self.op_literal = read24(off, cpu)

        self.addr = getAddr(self.op_literal, self.inf['mode'], cpu, True)
        return self.inf['width']

    def execute(self, cpu):
        cpu.PB = (self.addr >> 16) & 0xFF
        cpu.PC = self.addr & 0xFFFF
        return self.inf['bc']


class JSR(Instruction):
    opcodes = [0x20, 0x22, 0xFC]
    opcode_info = {
        0x20: {'name': 'JSR', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': []},
        0x22: {'name': 'JSL', 'mode': 'absl', 'bc': 8, 'width': 3, 'timing': []},
        0xFC: {'name': 'JSR', 'mode': 'absxi', 'bc': 8, 'width': 2, 'timing': []},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.addr = 0
        self.op_literal = 0
        self.inf = self.opcode_info[self.opcode]

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.inf['width'] == 2:
            self.op_literal = read16(off, cpu)
        else:
            self.op_literal = read24(off, cpu)

        self.addr = getAddr(self.op_literal, self.inf['mode'], cpu, True)
        return self.inf['width']

    def execute(self, cpu):
        rt_addr = nextAddr(cpu.get_pc(), self.inf['width'])
        if self.inf['width'] == 3:
            cpu.stack_push(cpu.PB)
        cpu.stack_push(rt_addr & 0xFF)
        cpu.stack_push((rt_addr >> 8) & 0xFF)

        if self.inf['width'] == 3:
            cpu.PB = (self.addr >> 16) & 0xFF
        cpu.PC = self.addr & 0xFFFF
        return self.inf['bc']


class LDA(Instruction):
    opcodes = [0xA1, 0xA3, 0xA5, 0xA7, 0xA9, 0xAD, 0xAF, 0xB1, 0xB2, 0xB3, 0xB5,
                0xB7, 0xB9, 0xBD, 0xBF, 0xA2, 0xA6, 0xAE, 0xB6, 0xBE, 0xA0, 0xA4,
                0xAC, 0xB4, 0xBC]
    opcode_info = {
        0xA1: {'name': 'LDA', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xA3: {'name': 'LDA', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0xA5: {'name': 'LDA', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0xA7: {'name': 'LDA', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xA9: {'name': 'LDA', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [1]},
        0xAD: {'name': 'LDA', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0xAF: {'name': 'LDA', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0xB1: {'name': 'LDA', 'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0xB2: {'name': 'LDA', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0xB3: {'name': 'LDA', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0xB5: {'name': 'LDA', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0xB7: {'name': 'LDA', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xB9: {'name': 'LDA', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0xBD: {'name': 'LDA', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0xBF: {'name': 'LDA', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
        0xA2: {'name': 'LDX', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [8]},
        0xA6: {'name': 'LDX', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [2, 8]},
        0xAE: {'name': 'LDX', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [8]},
        0xB6: {'name': 'LDX', 'mode': 'dpy', 'bc': 4, 'width': 1, 'timing': [2, 8]},
        0xBE: {'name': 'LDX', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [3, 8]},
        0xA0: {'name': 'LDY', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [8]},
        0xA4: {'name': 'LDY', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [2, 8]},
        0xAC: {'name': 'LDY', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [8]},
        0xB4: {'name': 'LDY', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [2, 8]},
        0xBC: {'name': 'LDY', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [3, 8]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.op_literal = 0
        self.operand = 0
        self.inf = self.opcode_info[self.opcode]
        self.reg = self.inf['name'][2]

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.reg == "A":
            tb = cpu.get_flag("M")
        else:
            tb = cpu.get_flag("X")
        self.operand, width, param = getParameter(off, self.inf['mode'], cpu, tb, False)

        # check boundary cross for timing
        if mode == 'dpiy': # dpiy
            addr = getAddr(param, self.inf['mode'], cpu, False)
            self.bc = ((addr & 0xFF) - cpu.Y) & 0xFF00 != 0
        elif mode == 'absy': # absy
            self.bc = ((param & 0xFF) + cpu.Y) & 0xFF00 != 0
        elif mode == 'absx': # absx
            self.bc = ((param & 0xFF) + cpu.X) & 0xFF00 != 0

        self.op_literal = param
        return width

    def execute(self, cpu):
        if self.reg == "A":
            cpu.A = self.operand
            hi = 0x80 if cpu.get_flag("M") else 0x8000
        elif self.reg == "X":
            cpu.X = self.operand
            hi = 0x80 if cpu.get_flag("X") else 0x8000
        else:
            cpu.Y = self.operand
            hi = 0x80 if cpu.get_flag("X") else 0x8000

        cpu.clear_flag("Z")
        cpu.clear_flag("N")
        if self.operand == 0:
            cpu.set_flag("Z")
        elif self.operand & hi:
            cpu.set_flag("N")
        return cycles(self.opcode_info[self.opcode]['bc'], \
                self.opcode_info[self.opcode]['timing'], cpu, bound_cross=self.bc)


class LSR(Instruction):
    opcodes = [0x46, 0x4A, 0x4E, 0x56, 0x5E]
    opcode_info = {
        0x46: {'name': 'LSR', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0x4A: {'name': 'LSR', 'mode': 'acc', 'bc': 2, 'width': 0, 'timing': []},
        0x4E: {'name': 'LSR', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
        0x56: {'name': 'LSR', 'mode': 'dpx', 'bc': 6, 'width': 1, 'timing': [2, 4]},
        0x5E: {'name': 'LSR', 'mode': 'absx', 'bc': 7, 'width': 2, 'timing': [4]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.op_literal = 0
        self.addr = 0
        self.inf = self.opcode_info[self.opcode]

    def fetch(self, cpu):
        if self.opcode == 0x4A:
            return 0

        off = nextAddr(cpu.get_pc())
        if self.opcode_info[self.opcode]['width'] == 1:
            param = cpu.mem.read(off)
            width = 1
        else:
            param = read16(off, cpu)
            width = 2

        mode = self.opcode_info[self.opcode]['mode']
        self.addr = getAddr(param, mode, cpu, False)
        self.op_literal = param
        return width

    def execute(self, cpu):
        cpu.clear_flag("N")
        cpu.clear_flag("Z")
        cpu.clear_flag("C")
        if self.opcode == 0x4A:
            # Shift accumulator (8 or 16 bits)
            if cpu.get_flag("M"):
                if cpu.A & 0x80:  cpu.set_flag("C")
                cpu.A = (cpu.A >> 1) & 0xFF
                if cpu.A == 0:  cpu.set_flag("Z")
                elif cpu.A & 0x80:  cpu.set_flag("N")
            else:
                if cpu.A & 0x8000: cpu.set_flag("C")
                cpu.A = (cpu.A >> 1) & 0xFFFF
                if cpu.A == 0: cpu.set_flag("Z")
                elif cpu.A & 0x8000:  cpu.set_flag("N")
        else:
            if cpu.get_flag("M"):
                # Shift memory in-place (8 bits)
                val = cpu.mem.read(self.addr)
                if val & 0x80: cpu.set_flag("C")
                val = (val >> 1) & 0xFF
                cpu.mem.write(self.addr, val)
                if val == 0: cpu.set_flag("Z")
                elif val & 0x80: cpu.set_flag("N")
            else:
                val = read16(self.addr, cpu)
                if val & 0x8000: cpu.set_flag("C")
                val = (val >> 1) & 0xFFFF
                cpu.mem.write(self.addr, val & 0xFF)
                cpu.mem.write(nextAddr(self.addr), (val >> 8) & 0xFF)
                if val == 0: cpu.set_flag("Z")
                elif val & 0x8000: cpu.set_flag("N")
        return cycles(self.opcode_info[self.opcode]['bc'], \
                self.opcode_info[self.opcode]['timing'], cpu)


class MVN(Instruction):
    ##################################################################################
    # Unimplemented!
    pass


class NOP(Instruction):
    opcodes = [0xEA]

    def __init__(self, opcode):
        super().__init__(opcode)

    def __repr__(self):
        return "NOP"

    def fetch(self, cpu):
        return 0

    def execute(self, cpu):
        return 2


class ORA(ArithmeticInstruction):
    opcodes = [0x01, 0x03, 0x05, 0x07, 0x09, 0x0D, 0x0F, 0x11, 0x12, 0x13, 0x15,
                0x17, 0x19, 0x1D, 0x1F]
    opcode_info = {
        0x01: {'name': 'ORA', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x03: {'name': 'ORA', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0x05: {'name': 'ORA', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0x07: {'name': 'ORA', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x09: {'name': 'ORA', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [1]},
        0x0D: {'name': 'ORA', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0x0F: {'name': 'ORA', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0x11: {'name': 'ORA', 'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0x12: {'name': 'ORA', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0x13: {'name': 'ORA', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0x15: {'name': 'ORA', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0x17: {'name': 'ORA', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x19: {'name': 'ORA', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x1D: {'name': 'ORA', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0x1F: {'name': 'ORA', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "ORA"

    def _op(self, a, b):
        return a | b

    def _flags(self):
        return ["N", "Z"]


class PushAddrInstruction(Instruction):
    opcodes = [0xF4, 0xD4, 0x62]
    opcode_info = {
        0xF4: {'name': 'PEA', 'mode': 'abs', 'bc': 5, 'width': 2, 'timing': []},
        0xD4: {'name': 'PEI', 'mode': 'dpi', 'bc': 6, 'width': 1, 'timing': [2]},
        0x62: {'name': 'PER', 'mode': 'rell', 'bc': 6, 'width': 2, 'timing': []},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        self.op_literal = 0
        self.addr = 0

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.inf['width'] == 1:
            param = cpu.mem.read(off)
        else:
            param = read16(off, cpu)
        self.addr = getAddr(off, mode, cpu, True)
        return self.inf['width']

    def execute(self, cpu):
        cpu.stack_push(self.addr & 0xFF)
        cpu.stack_push((self.addr >> 8) & 0xFF)
        return cycles(self.inf['bc'], self.inf['timing'], cpu)


class PushInstruction(Instruction):
    opcodes = [0x48, 0x8B, 0x0B, 0x4B, 0x08, 0xDA, 0x5A]
    opcode_info = {
        0x48: {'name': 'PHA', 'mode': 'imp', 'bc': 3, 'width': 0, 'timing': [1]},
        0x8B: {'name': 'PHB', 'mode': 'imp', 'bc': 3, 'width': 0, 'timing': []},
        0x0B: {'name': 'PHD', 'mode': 'imp', 'bc': 4, 'width': 0, 'timing': []},
        0x4B: {'name': 'PHK', 'mode': 'imp', 'bc': 3, 'width': 0, 'timing': []},
        0x08: {'name': 'PHP', 'mode': 'imp', 'bc': 3, 'width': 0, 'timing': []},
        0xDA: {'name': 'PHX', 'mode': 'imp', 'bc': 3, 'width': 0, 'timing': [8]},
        0x5A: {'name': 'PHY', 'mode': 'imp', 'bc': 3, 'width': 0, 'timing': [8]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        self.val = 0
        self.width = 1

    def __repr__(self):
        return self.inf['name']

    def fetch(self, cpu):
        if self.opcode == 0x48: # PHA -> push A
            self.val = cpu.A
            self.width = 1 if cpu.get_flag("M") else 2
        elif self.opcode == 0x8B: # PHB -> push DB
            self.val = cpu.DB
            self.width = 1
        elif self.opcode == 0x0B: # PHD -> push DP
            self.val = cpu.DP
            self.width = 2
        elif self.opcode == 0x4B: # PHK -> push PB
            self.val = cpu.PB
            self.width = 1
        elif self.opcode == 0x08: # PHP -> push P
            self.val = cpu.P
            self.width = 1
        elif self.opcode == 0xDA: # PHX -> push X
            self.val = cpu.X
            self.width = 1 if cpu.get_flag("X") else 2
        elif self.opcode == 0x5A: # PHY -> push Y
            self.val = cpu.Y
            self.width = 1 if cpu.get_flag("X") else 2
        return 0

    def execute(self, cpu):
        if self.width == 2:
            cpu.stack_push((self.val >> 8) & 0xFF)
        cpu.stack_push(self.val & 0xFF)
        return cycles(self.inf['bc'], self.inf['timing'], cpu)


class PullInstruction(Instruction):
    opcodes = [0x68, 0xAB, 0x2B, 0x28, 0xFA, 0x7A]
    opcode_info = {
        0x68: {'name': 'PLA', 'mode': 'imp', 'bc': 4, 'width': 0, 'timing': [1]},
        0xAB: {'name': 'PLB', 'mode': 'imp', 'bc': 4, 'width': 0, 'timing': []},
        0x2B: {'name': 'PLD', 'mode': 'imp', 'bc': 5, 'width': 0, 'timing': []},
        0x28: {'name': 'PLP', 'mode': 'imp', 'bc': 4, 'width': 0, 'timing': []},
        0xFA: {'name': 'PLX', 'mode': 'imp', 'bc': 4, 'width': 0, 'timing': [8]},
        0x7A: {'name': 'PLY', 'mode': 'imp', 'bc': 4, 'width': 0, 'timing': [8]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        self.val = 0
        self.width = 1

    def __repr__(self):
        return self.inf['name']

    def fetch(self, cpu):
        if self.opcode == 0x68: # A
            self.width = 1 if cpu.get_flag("M") else 2
        elif self.opcode == 0xAB: # DB
            self.width = 1
        elif self.opcode == 0x2B: # DP
            self.width = 2
        elif self.opcode == 0x28: # P
            self.width = 1
        elif self.opcode == 0xFA: # X
            self.width = 1 if cpu.get_flag("X") else 2
        elif self.opcode == 0x7A: # Y
            self.width = 1 if cpu.get_flag("Y") else 2
        return 0

    def execute(self, cpu):
        val = cpu.stack_pop()
        if self.width == 2:
            val |= cpu.stack_pop() << 8

        if self.opcode == 0x68:   cpu.A = val
        elif self.opcode == 0xAB: cpu.DB = val
        elif self.opcode == 0x2B: cpu.DP = val
        elif self.opcode == 0x28: cpu.P = val
        elif self.opcode == 0xFA: cpu.X = val
        elif self.opcode == 0x7A: cpu.Y = val
        return cycles(self.inf['bc'], self.inf['timing'], cpu)


class REP(Instruction):
    opcodes = [0xC2]

    def __init__(self, opcode):
        super().__init__(opcode)
        self.op = 0

    def __repr__(self):
        return "REP #%02x" % self.op

    def fetch(self, cpu):
        self.op = cpu.mem.read(nextAddr(cpu.PC))
        return 1

    def execute(self, cpu):
        cpu.P &= ~self.op
        return 3

class ROL(Instruction):
    opcodes = [0x26, 0x2A, 0x2E, 0x36, 0x3E, 0x66, 0x6A, 0x6E, 0x76, 0x7E]
    opcode_info = {
        0x26: {'name': 'ROL', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0x2A: {'name': 'ROL', 'mode': 'acc', 'bc': 2, 'width': 0, 'timing': []},
        0x2E: {'name': 'ROL', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
        0x36: {'name': 'ROL', 'mode': 'dpx', 'bc': 6, 'width': 1, 'timing': [2, 4]},
        0x3E: {'name': 'ROL', 'mode': 'absx', 'bc': 7, 'width': 2, 'timing': [4]},
        0x66: {'name': 'ROR', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0x6A: {'name': 'ROR', 'mode': 'acc', 'bc': 2, 'width': 0, 'timing': []},
        0x6E: {'name': 'ROR', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
        0x76: {'name': 'ROR', 'mode': 'dpx', 'bc': 6, 'width': 1, 'timing': [2, 4]},
        0x7E: {'name': 'ROR', 'mode': 'absx', 'bc': 7, 'width': 2, 'timing': [4]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        slef.dir = self.inf['name'][2]
        self.op_literal = 0
        self.addr = 0

    def __repr__(self):
        if self.inf['mode'] == 'acc':
            return self.inf['name'] + " A"
        else:
            return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        if self.inf['mode'] == 'acc':
            return 0
        else:
            off = nextAddr(cpu.get_pc())
            self.addr, width, self.op_literal = \
                getParameter(off, self.inf['mode'], cpu, not cpu.get_flag("M"), False)
            return width

    def execute(self, cpu):
        hi = 0x8000 if not cpu.get_flag("M") else 0x80
        mask = 0xFFFF if not cpu.get_flag("M") else 0xFF
        if self.inf['mode'] == 'acc':
            if self.dir == "L":
                cb = cpu.A & hi
                cpu.A = (cpu.A << 1) & mask
                if cpu.get_flag("C"): cpu.A |= 1 # shift in a 1
            else:
                cb = cpu.A & 1
                cpu.A = (cpu.A >> 1) & mask
                if cpu.get_flag("C"): cpu.A |= hi
            val = cpu.A
        else:
            val = cpu.mem.read(self.addr)
            if mask & 0xFF00:
                val |= cpu.mem.read(nextAddr(self.addr)) << 8
            if self.dir == "L":
                cb = val & hi
                val = (val << 1) & mask
                if cpu.get_flag("C"): val |= 1
            else:
                cb = val & 1
                val = (val >> 1) & mask
                if cpu.get_flag("C"): val |= hi
            cpu.mem.write(self.addr, val & 0xFF)
            if mask & 0xFF00:
                cpu.mem.write(nextAddr(self.addr), (val >> 8) & 0xFF)
        cpu.clear_flag("C")
        cpu.clear_flag("N")
        cpu.clear_flag("Z")
        if cb:
            cpu.set_flag("C")
        if val == 0:
            cpu.set_flag0("Z")
        if val & hi:
            cpu.set_flag("N")
        return cycles(self.inf['bc'], self.inf['timing'], cpu)


class ReturnInstruction(Instruction):
    opcodes = [0x40, 0x6B, 0x60]
    opcode_info = {
        0x40: {'name': 'RTI', 'mode': 'imp', 'bc': 6, 'width': 0, 'timing': [7]},
        0x6B: {'name': 'RTL', 'mode': 'imp', 'bc': 6, 'width': 0, 'timing': []},
        0x60: {'name': 'RTS', 'mode': 'imp', 'bc': 6, 'width': 0, 'timing': []},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]

    def __repr__(self):
        return self.inf['name']

    def fetch(self, cpu):
        return 0

    def execute(self, cpu):
        if self.opcode == 0x40:
            # RTI: pull P, PC, K
            cpu.P   = cpu.stack_pop()
            cpu.PC  = cpu.stack_pop()
            cpu.PC |= cpu.stack_pop() << 8
            cpu.PB  = cpu.stack_pop()
            return 7
        else:
            # RTS: pull PC
            cpu.PC  = cpu.stack_pop()
            cpu.PC |= cpu.stack_pop() << 8
            cpu.PC = nextAddr(cpu.PC)
            if self.opcode == 0x6B:
                cpu.PB = cpu.stack_pop()
            return 6


class SBC(ArithmeticInstruction):
    opcodes = [0xE1, 0xE3, 0xE5, 0xE7, 0xE9, 0xED, 0xEF, 0xF1, 0xF2, 0xF3, 0xF5,
                0xF7, 0xF9, 0xFD, 0xFF]
    opcode_info = {
        0xE1: {'name': 'SBC', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xE3: {'name': 'SBC', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0xE5: {'name': 'SBC', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0xE7: {'name': 'SBC', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xE9: {'name': 'SBC', 'mode': 'imm', 'bc': 2, 'width': 0, 'timing': [1]},
        0xED: {'name': 'SBC', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0xEF: {'name': 'SBC', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0xF1: {'name': 'SBC', 'mode': 'dpiy', 'bc': 5, 'width': 1, 'timing': [1, 2, 3]},
        0xF2: {'name': 'SBC', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0xF3: {'name': 'SBC', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0xF5: {'name': 'SBC', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0xF7: {'name': 'SBC', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0xF9: {'name': 'SBC', 'mode': 'absy', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0xFD: {'name': 'SBC', 'mode': 'absx', 'bc': 4, 'width': 2, 'timing': [1, 3]},
        0xFF: {'name': 'SBC', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def _name(self):
        return "SBC"

    def _op(self, a, b):
        return a - b

    def _flags(self):
        return ["Z", "C", "V", "N"]


class SetInstruction(Instruction):
    opcodes = [0x38, 0xF8, 0x78]
    opcode_info = {
        0x38: {'name': 'SEC', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
        0xF8: {'name': 'SED', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
        0x78: {'name': 'SEI', 'mode': 'imp', 'bc': 2, 'width': 0, 'timing': []},
    }

    def __init__(self, opcode):
        super().__init__(opcode)

    def __repr__(self):
        return self.opcode_info[self.opcode]['name']

    def fetch(self, cpu):
        return 0

    def execute(self, cpu):
        if self.opcode == 0x38:   cpu.set_flag("C")
        elif self.opcode == 0xF8: cpu.set_flag("D")
        elif self.opcode == 0x78: cpu.set_flag("I")
        return 2


class SEP(Instruction):
    opcodes = [0xE2]

    def __init__(self, opcode):
        super().__init__(opcode)
        self.op = 0

    def __repr__(self):
        return "SEP #%02x" % self.op

    def fetch(self, cpu):
        self.op = cpu.mem.read(nextAddr(cpu.get_pc()))
        return 1

    def execute(self, cpu):
        cpu.P |= self.op
        return 2


class STA(Instruction):
    opcodes = [0x81, 0x83, 0x85, 0x87, 0x8D, 0x8F, 0x91, 0x92, 0x93, 0x95, 0x97,
                0x99, 0x9D, 0x9F, 0x86, 0x8E, 0x96, 0x84, 0x8C, 0x94, 0x64, 0x74,
                0x9C, 0x9E]

    opcode_info = {
        0x81: {'name': 'STA', 'mode': 'dpxi', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x83: {'name': 'STA', 'mode': 'sr', 'bc': 4, 'width': 1, 'timing': [1]},
        0x85: {'name': 'STA', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0x87: {'name': 'STA', 'mode': 'dpil', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x8D: {'name': 'STA', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0x8F: {'name': 'STA', 'mode': 'absl', 'bc': 5, 'width': 3, 'timing': [1]},
        0x91: {'name': 'STA', 'mode': 'dpiy', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x92: {'name': 'STA', 'mode': 'dpi', 'bc': 5, 'width': 1, 'timing': [1, 2]},
        0x93: {'name': 'STA', 'mode': 'sriy', 'bc': 7, 'width': 1, 'timing': [1]},
        0x95: {'name': 'STA', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0x97: {'name': 'STA', 'mode': 'dpiyl', 'bc': 6, 'width': 1, 'timing': [1, 2]},
        0x99: {'name': 'STA', 'mode': 'absy', 'bc': 5, 'width': 2, 'timing': [1]},
        0x9D: {'name': 'STA', 'mode': 'absx', 'bc': 5, 'width': 2, 'timing': [1]},
        0x9F: {'name': 'STA', 'mode': 'abslx', 'bc': 5, 'width': 3, 'timing': [1]},
        0x86: {'name': 'STX', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [2, 8]},
        0x8E: {'name': 'STX', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [8]},
        0x96: {'name': 'STX', 'mode': 'dpy', 'bc': 4, 'width': 1, 'timing': [2, 8]},
        0x84: {'name': 'STY', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [2, 8]},
        0x8C: {'name': 'STY', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [8]},
        0x94: {'name': 'STY', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [2, 8]},
        0x64: {'name': 'STZ', 'mode': 'dp', 'bc': 3, 'width': 1, 'timing': [1, 2]},
        0x74: {'name': 'STZ', 'mode': 'dpx', 'bc': 4, 'width': 1, 'timing': [1, 2]},
        0x9C: {'name': 'STZ', 'mode': 'abs', 'bc': 4, 'width': 2, 'timing': [1]},
        0x9E: {'name': 'STZ', 'mode': 'absx', 'bc': 5, 'width': 2, 'timing': [1]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.op_literal = 0
        self.addr = 0
        self.inf = self.opcode_info[self.opcode]
        self.reg = self.inf['name'][2]

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        if self.inf['width'] == 1:
            self.op_literal = cpu.mem.read(off)
        elif self.inf['width'] == 2:
            self.op_literal = read16(off, cpu)
        else:
            self.op_literal = read24(off, cpu)

        self.addr = getAddr(self.op_literal, self.inf['mode'], cpu, False)

        return self.inf['width']

    def execute(self, cpu):
        if self.reg == "A":
            val = cpu.A
            w = 1 if cpu.get_flag("M") else 2
        elif self.reg == "X":
            val = cpu.X
            w = 1 if cpu.get_flag("X") else 2
        elif self.reg == "Y":
            val = cpu.Y
            w = 1 if cpu.get_flag("X") else 2
        else:
            val = 0
            w = 1 if cpu.get_flag("M") else 2

        cpu.mem.write(self.addr, val & 0xFF)
        if w == 2:
            cpu.mem.write(nextAddr(self.addr), (val>>8) & 0xFF)
        return cycles(self.inf['bc'], self.inf['timing'], cpu)


class TransferInstruction(Instruction):
    opcodes = [0xAA, 0xAB, 0x5B, 0x1B, 0x7B, 0x3B, 0xBA, 0x8A, 0x9A, 0x9B, 0x98,
                0xBB]
    opcode_info = {
        0xAA: {'name': 'TAX', 'src': 'A', 'dst': 'X'},
        0xA8: {'name': 'TAY', 'src': 'A', 'dst': 'Y'},
        0x5B: {'name': 'TCD', 'src': 'C', 'dst': 'DP'},
        0x1B: {'name': 'TCS', 'src': 'C', 'dst': 'S'},
        0x7B: {'name': 'TDC', 'src': 'DP', 'dst': 'C'},
        0x3B: {'name': 'TSC', 'src': 'S', 'dst': 'C'},
        0xBA: {'name': 'TSX', 'src': 'S', 'dst': 'X'},
        0x8A: {'name': 'TXA', 'src': 'X', 'dst': 'A'},
        0x9A: {'name': 'TXS', 'src': 'X', 'dst': 'S'},
        0x9B: {'name': 'TXY', 'src': 'X', 'dst': 'Y'},
        0x98: {'name': 'TYA', 'src': 'Y', 'dst': 'A'},
        0xBB: {'name': 'TYX', 'src': 'Y', 'dst': 'X'},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]

    def __repr__(self):
        return self.inf['name']

    def fetch(self, cpu):
        if self.inf['src'] == 'A' or self.inf['src'] == 'C':
            self.src = cpu.get_full_a()
        elif self.inf['src'] == 'DP':
            self.src = cpu.DP
        elif self.inf['src'] == 'S':
            self.src = cpu.S
        elif self.inf['src'] == 'X':
            self.src = cpu.X
        elif self.inf['src'] == 'Y':
            self.src = cpu.Y
        return 0

    def execute(self, cpu):
        if self.inf['dst'] == 'X':
            if cpu.get_flag("X"): cpu.X = self.src & 0xFF
            else:                 cpu.X = self.src
            dst = cpu.X
            ds = 1 if cpu.get_flag("X") else 2
        elif self.inf['dst'] == 'Y':
            if cpu.get_flag("X"): cpu.Y = self.src & 0xFF
            else:                 cpu.Y = self.src
            dst = cpu.Y
            ds = 1 if cpu.get_flag("X") else 2
        elif self.inf['dst'] == 'DP':
            cpu.DP = self.src
            dst = cpu.DP
            ds = 2
        elif self.inf['dst'] == 'S':
            cpu.S = self.src
            dst = cpu.S
            ds = 1
        elif self.inf['dst'] == 'C':
            cpu.set_full_a(self.src)
            dst = cpu.get_full_a()
            ds = 2
        elif self.inf['dst'] == 'A':
            if cpu.get_flag("M"): cpu.A = self.src & 0xFF
            else:                 cpu.A = self.src
            dst = cpu.A
            ds = 1 if cpu.get_flag("M") else 2

        if self.inf['dst'] != 'S':
            cpu.clear_flag("N")
            cpu.clear_flag("Z")
            hi = 0x8000 if ds == 2 else 0x80
            if dst & hi:
                cpu.set_flag("N")
            elif dst == 0:
                cpu.set_flag("Z")
        return 2


class TRB(Instruction):
    opcodes = [0x14, 0x1C, 0x04, 0x0C]
    opcode_info = {
        0x14: {'name': 'TRB', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0x1C: {'name': 'TRB', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
        0x04: {'name': 'TSB', 'mode': 'dp', 'bc': 5, 'width': 1, 'timing': [2, 4]},
        0x0C: {'name': 'TSB', 'mode': 'abs', 'bc': 6, 'width': 2, 'timing': [4]},
    }

    def __init__(self, opcode):
        super().__init__(opcode)
        self.inf = self.opcode_info[self.opcode]
        self.tp = self.inf['mode'][1]
        self.op_literal = 0
        self.operand = 0

    def __repr__(self):
        return self.inf['name'] + " " + (getAddrFormat(self.inf['mode']) % self.op_literal)

    def fetch(self, cpu):
        off = nextAddr(cpu.get_pc())
        self.operand, width, self.op_literal = \
            getParameter(off, self.inf['mode'], cpu, not cpu.get_flag("M"), False)
        return width

    def execute(self, cpu):
        if self.tp == "R":
            self.operand &= ~cpu.A
        elif self.tp == "S":
            self.operand |= cpu.A
        a = self.operand & cpu.A
        cpu.clear_flag("Z")
        if a == 0:
            cpu.set_flag("Z")
        return cycles(self.inf['bc'], self.inf['timing'], cpu)


class WAI(Instruction):
    #################################################################################
    # Unimplemented instruction!
    pass


class XBA(Instruction):
    opcodes = [0xEB]

    def __init__(self, o):
        super().__init__(o)

    def __repr_(self):
        return "XBA"

    def fetch(self, cpu):
        return 0

    def execute(self, cpu):
        b = cpu.B
        a = cpu.A & 0xFF
        cpu.set_full_a((a << 8) | b)
        return 3


class XCE(Instruction):
    opcodes = [0xFB]

    def __init__(self, o):
        super().__init__(o)

    def __repr_(self):
        return "XCE"

    def fetch(self, cpu):
        return 0

    def execute(self, cpu):
        e = cpu.EMU
        cpu.EMU = cpu.get_flag("C")
        if e: cpu.set_flag("C")
        else: cpu.clear_flag("C")
        return 2


def _registerInstruction(instrClass, reg):
    for c in instrClass.opcodes:
        reg[c] = instrClass


def getAllInstructions():
    reg = {}
    _registerInstruction(ADC, reg)
    _registerInstruction(AND, reg)
    _registerInstruction(ASL, reg)
    _registerInstruction(BCC, reg)
    _registerInstruction(BCS, reg)
    _registerInstruction(BEQ, reg)
    _registerInstruction(BIT, reg)
    _registerInstruction(BMI, reg)
    _registerInstruction(BNE, reg)
    _registerInstruction(BPL, reg)
    _registerInstruction(BRA, reg)
    _registerInstruction(ASL, reg)
    # _registerInstruction(BRK, reg)
    _registerInstruction(BRL, reg)
    _registerInstruction(BVC, reg)
    _registerInstruction(BVS, reg)
    _registerInstruction(ClearInst, reg)
    _registerInstruction(CMP, reg)
    # _registerInstruction(COP, reg)
    _registerInstruction(DEC, reg)
    _registerInstruction(EOR, reg)
    _registerInstruction(JMP, reg)
    _registerInstruction(JSR, reg)
    _registerInstruction(LDA, reg)
    _registerInstruction(LSR, reg)
    _registerInstruction(ASL, reg)
    # _registerInstruction(MVN, reg)
    _registerInstruction(NOP, reg)
    _registerInstruction(ORA, reg)
    _registerInstruction(PushAddrInstruction, reg)
    _registerInstruction(PushInstruction, reg)
    _registerInstruction(PullInstruction, reg)
    _registerInstruction(REP, reg)
    _registerInstruction(ROL, reg)
    _registerInstruction(ReturnInstruction, reg)
    _registerInstruction(SBC, reg)
    _registerInstruction(SetInstruction, reg)
    _registerInstruction(SEP, reg)
    _registerInstruction(STA, reg)
    _registerInstruction(TransferInstruction, reg)
    _registerInstruction(TRB, reg)
    # _registerInstruction(WAI, reg)
    _registerInstruction(XBA, reg)
    _registerInstruction(XCE, reg)
    return reg
