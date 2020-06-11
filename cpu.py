import memory

cpu_flags = {
    "N": 0x80, # negative
    "V": 0x40, # overflow
    "M": 0x20, # accumulator size (set => 8bits)
    "X": 0x10, # index size (set => 8bits)
    "D": 0x08, # decimal flag (does nothing on SNES)
    "I": 0x04, # IRQ disabled when set
    "Z": 0x02, # zero
    "C": 0x01  # carry (can be copied to the emulation flag)
}


class CPU:
    def __init__(self, mem):
        self.mem = mem
        self.reset = True
        self.cycle_count = 0
        self.A = 0  # Accumulator
        self.X = 0  # X index
        self.Y = 0  # Y index
        self.S = 0  # Stack pointer
        self.DB = 0 # Default bank
        self.DP = 0 # Direct page
        self.PB = 0 # Program bank
        self.P = 0  # Status flags
        self.PC = 0 # Program counter
        self.EMU = True # does nothing, just a debug info

    def set_flag(self, flag):
        self.P |= cpu_flags[flag]

    def clear_flag(self, flag):
        self.P &= ~cpu_flags[flag]

    def get_flag(self, flag):
        return self.P & cpu_flags[flag]

    def cycle(self):
        """
        Parse an instruction. May take several cycles. Exits when the PC changes
        """
        if self.reset:
            # Do reset sequence.
            self.set_flag("I")
            self.clear_flag("D")
            self.EMU = True
            self.set_flag("M")
            self.set_flag("X")
            self.DB = 0
            self.PB = 0
            # set high byte to 0x01
            self.SP = (self.SP & 0xFF) | 0x0100
            # Read reset vector
            self.PC = self.mem.read(0xFFFC) | (self.mem.read(0xFFFD) << 8)
            # Reset cycle counter
            self.cycle_count = 0

            self.reset = False
