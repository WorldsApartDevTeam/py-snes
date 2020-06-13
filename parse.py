modes = {
    'DP Indexed Indirect,X': 'dpxi',
    'Stack Relative':        'sr',
    'Direct Page':           'dp',
    'DP Indirect Long':      'dpil',
    'Immediate':             'imm',
    'Absolute':              'abs',
    'Absolute Long':         'absl',
    'DP Indirect Indexed, Y':'dpiy',
    'DP Indirect':           'dpi',
    'SR Indirect Indexed,Y': 'sriy',
    'DP Indexed,X':          'dpx',
    'DP Indirect Long Indexed, Y': 'dpiyl',
    'Absolute Indexed,Y':    'absy',
    'Absolute Indexed,X':    'absx',
    'Absolute Long Indexed,X': 'abslx',
    'Accumulator':           'acc',
    'Implied':               'imp',
    'Absolute Indirect':     'absi',
    'Absolute Indexed Indirect': 'absxi',
    'Absolute Indirect Long':'absil',
    'DP Indexed,Y':          'dpy',
    'PC Relative Long':      'rell',
    'Stack (Push)':          'imp',
    'Stack (Pull)':          'imp',
    'Stack (RTI)':           'imp',
    'Stack (RTL)':           'imp',
    'Stack (RTS)':           'imp'
}

with open('cmp.txt', 'r') as f:
    data = '{\n'
    for line in f:
        sp = line.split('\t')
        # print(sp)
        name = sp[0].split(' ')[0]
        hex = "0x" + sp[3].strip()
        mode = modes[sp[4].strip()]
        width = sp[6].strip()
        if '[' in width:
            width = 1
        width = int(width)-1
        cyc_sp = sp[7].replace(']', '').replace('^', '').replace('\n', '').split('[')
        base_cyc = cyc_sp[0]
        timing = cyc_sp[1:]
        out = "    %s: {'name': '%s', 'mode': '%s', 'bc': %s, 'width': %s, 'timing': %s},\n" % \
            (hex, name, mode, base_cyc, width, str(timing).replace("'", ''))
        data += out
    data += '}\n'
    print(data)
