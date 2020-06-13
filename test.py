from cpu import CPU
import memory
import sys
import os
import subprocess

def compile():
    os.chdir('cc65')
    subprocess.run(['bash', 'compile.sh'])
    os.chdir('..')

class DebugOut(memory.Memory):
    def __init__(self):
        self.mem = [0] * 4
        self.debugs = []
        # 0: width [1-3]
        # 1-3: value
        # 4: enable

    def read(self, addr):
        return 0

    def write(self, addr, value):
        if addr == 4:
            s = self.mem[0]
            if s == 0:
                return
            if s == 1:
                self.debugs.append("==> $%02x" % self.mem[1])
            elif s == 2:
                self.debugs.append("==> $%04x" % (self.mem[1] | (self.mem[2] << 8)))
            else:
                self.debugs.append("==> $%06x" % (self.mem[1] | (self.mem[2] << 8) | (self.mem[3] << 16)))
        else:
            self.mem[addr] = value

    def dump(self):
        for dbg in self.debugs:
            print(dbg)
        self.debugs = []


def main(fname):
    print("Compiling...")
    compile()
    print("Initializing processor and RAM")
    ram = memory.RAM(0x40000) # 256K of RAM
    dbg = DebugOut()

    mem = memory.AddressSpace()
    #       start      end        location
    mem.map(0x000000,  0x040000,  0x000000, ram)
    mem.map(0x040000,  0x040005,  0x000000, dbg)

    cpu = CPU(mem)

    ram.write(0xFFFC, 0x00)
    ram.write(0xFFFD, 0x08)

    addr = 0x0800
    with open(fname, 'rb') as f:
        while True:
            v = f.read(1)
            if len(v) == 0:
                break
            ram.write(addr, v[0])
            addr += 1

    while not cpu.halt:
        cpu.cycle()

    dbg.dump()

if __name__ == "__main__":
    main(sys.argv[1])
