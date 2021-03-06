import memory
import instructions

cpu_flags = {
    "N": 0x80, # negative
    "V": 0x40, # overflow
    "M": 0x20, # accumulator size (set => 8bits)
    "X": 0x10, # index size (set => 8bits)
    "D": 0x08, # decimal flag (does nothing on SNES, I think)
    "I": 0x04, # IRQ disabled when set
    "Z": 0x02, # zero
    "C": 0x01  # carry (can be copied to the emulation flag)
}


class CPU:
    def __init__(self, mem):
        self.mem = mem
        self.reset = True
        self.halt = False
        self.cycle_count = 0
        self.A = 0  # Accumulator
        self.B = 0  # backup copy of the high byte in 8-bit mode
        self.X = 0  # X index
        self.Y = 0  # Y index
        self.S = 0  # Stack pointer
        self.DB = 0 # Default bank
        self.DP = 0 # Direct page
        self.PB = 0 # Program bank
        self.P = 0  # Status flags
        self.PC = 0 # Program counter
        self.EMU = True # does nothing, just a debug info
        self.instructions = instructions.getAllInstructions()

    def set_flag(self, flag):
        self.P |= cpu_flags[flag]

    def clear_flag(self, flag):
        self.P &= ~cpu_flags[flag]

    def get_flag(self, flag):
        return self.P & cpu_flags[flag]

    def get_pc(self):
        return (self.PB << 16) | self.PC

    def stack_push(self, b):
        self.mem.write(self.S, b)
        self.S = (self.S - 1) & 0xFFFF

    def stack_pop(self):
        self.S = (self.S + 1) & 0xFFFF
        return self.mem.read(self.S)

    def get_full_a(self):
        return (self.B << 8) | self.A

    def set_full_a(self, a):
        if self.get_flag("M"):
            self.A = a & 0xFF
        else:
            self.A = a & 0xFFFF
        self.B = (a>>8) & 0xFF

    def cycle(self):
        """
        Parse an instruction. May take several cycles. Exits when the PC changes
        """
        if self.halt:
            return

        if self.reset:
            # Do reset sequence.
            print("[reset]")
            self.set_flag("I")
            self.clear_flag("D")
            self.EMU = True
            self.set_flag("M")
            self.set_flag("X")
            self.DB = 0
            self.PB = 0
            self.S = 0x01FF
            # Read reset vector
            self.PC = self.mem.read(0xFFFC) | (self.mem.read(0xFFFD) << 8)
            # Reset cycle counter
            self.cycle_count = 0

            self.reset = False
        opcode = self.mem.read(self.get_pc())
        if not opcode in self.instructions:
            print("ILLEGAL OPCODE %02x @ $%06x -- halting" % (opcode, self.get_pc()))
            self.halt = True
            return
        # print("%02x -- %s" % (opcode, self.instructions[opcode]))
        instr = self.instructions[opcode](opcode)
        old_m = self.get_flag("M")

        step = instr.fetch(self)
        print("[$%02x:%04x]: %s" % (self.PB, self.PC, instr))
        cycles = instr.execute(self)
        if not self.get_flag("M"):
            # Back up high byte in B
            if old_m:
                self.A |= self.B << 8
            else:
                self.B = (self.A >> 8) & 0xFF
        if self.get_flag("X"):
            # Force X and Y to 0
            self.X &= 0xFF
            self.Y &= 0xFF

        self.PC = instructions.nextAddr(self.PC, step+1)
        self.cycle_count += cycles

def main():
    ram = memory.RAM(0x10000) # 64K of RAM

    mem = memory.AddressSpace()
    mem.map(0x0000, 0x10000, 0x0000, ram)

    cpu = CPU(mem)

    # Set reset vector 0x0800
    ram.write(0xFFFC, 0x00)
    ram.write(0xFFFD, 0x08)

    # Write some code
    ram.write(0x0800, 0x69) # ADC immediate (8 bits, since we don't have REP)
    ram.write(0x0801, 0x05) # 5
    ram.write(0x0802, 0x6D) # ADC absolute (again, 8 bits)
    ram.write(0x0803, 0x00) # Address 0xFD00
    ram.write(0x0804, 0xFD)

    # Put our variable
    ram.write(0xFD00, 0xFE) # -2

    while not cpu.halt:
        cpu.cycle()
    print("A = %d" % cpu.A)
    print("cycle count = %d" % cpu.cycle_count)

if __name__ == "__main__":
    main()
