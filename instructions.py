
class Instruction:
    opcodes=[]

    def __init__(self, opcode):
        self.opcode = opcode

    def __repr__(self):
        return "UNK"

    def fetch(self, cpu):
        pass

    def execute(self, cpu):
        return 2 # return cycle count

def nextAddr(addr):
    bank = addr & 0xFF0000
    addrlo = addr & 0xFFFF
    return bank | (addrlo + 1) & 0xFFFF

def getAddr(offset, mode, cpu, is_pb):
    if is_pb:
        bankreg = cpu.PB
    else:
        bankreg = cpu.DB

    if mode == "imm":
        return 0 # means nothing to getAddr
    elif mode == "abs": # absolute
        return (bankreg << 16) | (offset & 0xFFFF)
    elif mode == "absl": # absolute long
        return offset & 0xFFFFFF
    elif mode == "absx": # absolute indexed X
        return (bankreg << 16) | ((offset + cpu.X) & 0xFFFF)
    elif mode == "absy": # absolute indexed Y
        return (bankreg << 16) | ((offset + cpu.Y) & 0xFFFF)
    elif mode == "abslx": # absolute long indexed X
        return (offset + cpu.X) & 0xFFFFFF
    elif mode == "absly": # absolute long indexed Y (possibly unavailable)
        return (offset + cpu.Y) & 0xFFFFFF
    elif mode == "rel": # relative (short)
        return (bankreg << 16) | ((offset + cpu.PC) & 0xFFFF)
    elif mode == "rell": # relative (long)
        return (offset + CPU.PC) & 0xFFFFFF
    elif mode == "dp": # direct page
        return (bankreg << 16) | (cpu.DP << 8) | (offset & 0xFF)
    elif mode == "dpx": # direct page indexed X
        return (bankreg << 16) | (cpu.DP << 8) | ((offset + cpu.X) & 0xFF)
    elif mode == "dpy": # direct page indexed Y
        return (bankreg << 16) | (cpu.DP << 8) | ((offset + cpu.Y) & 0xFF)
    elif mode == "absi": # absolute indirect
        ind_addr = getAddr(offset, "abs", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ind_data
    elif mode == "absil": # absolute indirect long
        ind_addr = getAddr(offset, "abs", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr); ind_addr = nextAddr(ind_addr)
        ind_data |= cpu.mem.read(ind_addr) << 8); ind_addr = nextAddr(ind_addr)
        ind_data |= cpu.mem.read(ind_addr) << 16)

        return ind_data
    elif mode == "absxi": # absolute (indexed X) indirect
        ind_addr = getAddr(offset, "absx", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ind_data
    elif mode == "absyi": # absolute (indexed Y) indirect
        ind_addr = getAddr(offset, "absy", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ind_data
    elif mode == "dpi": # direct page indirect
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ind_data
    elif mode == "dpxi": # direct-page (indexed X) indirect
        ind_addr = getAddr(offset, "dpx", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ind_data
    elif mode == "dpyi": # direct-page (indexed Y) indirect
        ind_addr = getAddr(offset, "dpy", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ind_data
    elif mode == "dpix": # direct-page indirect, indexed X
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ((ind_data + cpu.X) & 0xFFFF)
    elif mode == "dpiy": # direct-page indirect, indexed Y
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr) | (cpu.mem.read(nextAddr(ind_addr)) << 8)
        return (bankreg << 16) | ((ind_data + cpu.Y) & 0xFFFF)
    elif mode == "dpil": # direct-page indirect long
        ind_addr = getAddr(offset, "dp", cpu, is_pb)
        ind_data = cpu.mem.read(ind_addr); ind_addr = nextAddr(ind_addr)
        ind_data |= cpu.mem.read(ind_addr) << 8); ind_addr = nextAddr(ind_addr)
        ind_data |= cpu.mem.read(ind_addr) << 16)

        return ind_data
    elif mode == "dpixl": # direct-page indirect, indexed X, long
        return (getAddr(offset, "dpil", cpu, is_pb) + cpu.X) & 0xFFFFFF
    elif mode == "dpiyl": # direct-page indirect, indexed Y, long
        return (getAddr(offset, "dpil", cpu, is_pb) + cpu.Y) & 0xFFFFFF

class ADC:
    opcodes = [
        0x61, # DP indirect[X]
        0x63, # Stack relative (S + n)
        0x65, # Direct Page (0xDB DP nn)
        0x67, # DP indirect long
        0x69, # Immediate
        0x6D, # Absolute
        0x6F, # Absolute long
        0x71, # DP indirect[Y]
        0x72, # DP indirect
        0x73, # Stack indirect[Y]
        0x75, # Direct Page[X]
        0x77, # DP indirect long[Y]
        0x79, # Absolute[Y]
        0x7D, # Absolute[X]
        0x7F  # Absolute long[X]
    ]

    def __init__(self, opcode):
        super().__init__(opcode)

    def fetch(self, cpu):
