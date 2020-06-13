

"""
This refers to anything that can be read from or written to on the bus. This
could be RAM, ROM, or any variety of peripherals.
"""
class Memory:
    def read(self, addr):
        return 0

    def write(self, addr, value):
        pass


"""
RAM memory
"""
class RAM(Memory):
    def __init__(self, size):
        self.data = bytearray(size)
        self.size = size

    def read(self, addr):
        if addr > self.size:
            print("Error: more RAM mapped than available: attempt to access %06x" % addr)
            return 0
        return self.data[addr]


    def write(self, addr, value):
        if addr > self.size:
            print("Error: more RAM mapped than available: attempt to access %06x" % addr)
        else:
            self.data[addr] = value & 0xFF

"""
ROM memory
"""
class ROM(RAM):
    def write(self, addr, value):
        print("[invalid write %02x to ROM at %06x]" % (addr, value))

"""
Memory as it is seen by the CPU. Refers to proxies that can be mapped anywhere.
Memory is accessed using a 24-bit (3-byte) address and 8 bits of data.
"""
class AddressSpace:
    def __init__(self):
        self.devices = []

    def map(self, start, end, o_start, mem):
        n = len(self.devices)
        self.devices.append((start, end, o_start, mem))

    def read(self, addr):
        for dev in self.devices:
            if addr >= dev[0] and addr < dev[1]:
                o_addr = addr - dev[0] + dev[2]
                return dev[3].read(o_addr)
        return 0

    def write(self, addr, value):
        for dev in self.devices:
            if addr >= dev[0] and addr < dev[1]:
                o_addr = addr - dev[0] + dev[2]
                dev[3].write(o_addr, value)
