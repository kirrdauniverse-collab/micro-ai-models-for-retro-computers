#!/usr/bin/env python3
"""z80emu.py - compact Z80 CPU emulator (documented instructions, approximate T-states).

Only what the project needs is exercised, but the decoder follows the standard
x/y/z/p/q scheme so unknown opcodes raise instead of silently misbehaving.
"""

S_, Z_, Y_, H_, X_, P_, N_, C_ = 0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01

PAR = [0] * 256
for _i in range(256):
    PAR[_i] = P_ if bin(_i).count('1') % 2 == 0 else 0


class Z80Error(Exception):
    pass


class Z80:
    def __init__(self):
        self.mem = bytearray(65536)
        self.rom_end = 0x4000          # writes below are ignored (ROM)
        self.rom_writes = []
        self.ram_top = 0x8000          # writes at/above are ignored (16K machine)
        self.high_writes = []
        self.port_in = lambda port: 0xFF
        self.port_out = lambda port, v: None
        self.r = [0] * 8               # B C D E H L (unused) A
        self.f = 0
        self.ix = self.iy = 0
        self.sp = 0xFFFF
        self.pc = 0
        self.i = self.rr = 0
        self.alt = [0] * 8
        self.alt_f = 0
        self.iff = 0
        self.halted = False
        self.t = 0
        self.insns = 0
        self.hooks = {}                 # pc -> callable(cpu) -> True if it handled (and did RET itself)
        self.alt_used = False
        self.exec_high = []             # M1 fetches >= 0x8000

    # ----- memory -----
    def rb(self, a):
        return self.mem[a & 0xFFFF]

    def wb(self, a, v):
        a &= 0xFFFF
        if a < self.rom_end:
            self.rom_writes.append((self.pc, a))
            return
        if a >= self.ram_top:
            self.high_writes.append((self.pc, a))
            return
        self.mem[a] = v & 255

    def rw(self, a):
        return self.rb(a) | self.rb(a + 1) << 8

    def ww(self, a, v):
        self.wb(a, v & 255)
        self.wb(a + 1, (v >> 8) & 255)

    def fetch(self):
        v = self.mem[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        return v

    def fetch16(self):
        lo = self.fetch()
        return lo | self.fetch() << 8

    def push(self, v):
        self.sp = (self.sp - 2) & 0xFFFF
        self.ww(self.sp, v)

    def pop(self):
        v = self.rw(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        return v

    # ----- register helpers -----
    @property
    def a(self): return self.r[7]
    @a.setter
    def a(self, v): self.r[7] = v & 255
    @property
    def hl(self): return self.r[4] << 8 | self.r[5]
    @hl.setter
    def hl(self, v): self.r[4], self.r[5] = (v >> 8) & 255, v & 255
    @property
    def de(self): return self.r[2] << 8 | self.r[3]
    @de.setter
    def de(self, v): self.r[2], self.r[3] = (v >> 8) & 255, v & 255
    @property
    def bc(self): return self.r[0] << 8 | self.r[1]
    @bc.setter
    def bc(self, v): self.r[0], self.r[1] = (v >> 8) & 255, v & 255

    def rp(self, p):      # BC DE HL SP
        return (self.bc, self.de, self.hl, self.sp)[p]

    def set_rp(self, p, v):
        v &= 0xFFFF
        if p == 0: self.bc = v
        elif p == 1: self.de = v
        elif p == 2: self.hl = v
        else: self.sp = v

    def rp2(self, p):     # BC DE HL AF
        return (self.bc, self.de, self.hl, self.a << 8 | self.f)[p]

    def set_rp2(self, p, v):
        v &= 0xFFFF
        if p == 3:
            self.a, self.f = v >> 8, v & 255
        else:
            self.set_rp(p, v)

    # ----- ALU -----
    def alu(self, op, v):
        a = self.a
        if op == 0 or op == 1:       # add / adc
            c = (self.f & C_) if op == 1 else 0
            res = a + v + c
            self.f = (res & S_) | (Z_ if (res & 255) == 0 else 0) | ((a ^ v ^ res) & H_) \
                | (P_ if ((a ^ res) & (v ^ res) & 0x80) else 0) | (C_ if res > 255 else 0) | (res & (Y_ | X_))
            self.a = res
        elif op in (2, 3, 7):        # sub / sbc / cp
            c = (self.f & C_) if op == 3 else 0
            res = a - v - c
            self.f = (res & S_) | (Z_ if (res & 255) == 0 else 0) | ((a ^ v ^ res) & H_) \
                | (P_ if ((a ^ v) & (a ^ res) & 0x80) else 0) | N_ | (C_ if res < 0 else 0)
            if op == 7:
                self.f = (self.f & ~(Y_ | X_)) | (v & (Y_ | X_))
            else:
                self.f |= res & (Y_ | X_)
                self.a = res
        elif op == 4:
            r = a & v
            self.a = r
            self.f = (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | H_ | PAR[r]
        elif op == 5:
            r = a ^ v
            self.a = r
            self.f = (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | PAR[r]
        else:
            r = a | v
            self.a = r
            self.f = (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | PAR[r]

    def inc8(self, v):
        r = (v + 1) & 255
        self.f = (self.f & C_) | (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | ((v ^ r) & H_) | (P_ if v == 0x7F else 0)
        return r

    def dec8(self, v):
        r = (v - 1) & 255
        self.f = (self.f & C_) | (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | ((v ^ r) & H_) | (P_ if v == 0x80 else 0) | N_
        return r

    def cond(self, c):
        f = self.f
        return (not f & Z_, bool(f & Z_), not f & C_, bool(f & C_), not f & P_, bool(f & P_), not f & S_, bool(f & S_))[c]

    def rot(self, op, v):
        c = self.f & C_
        if op == 0:
            c = v >> 7; r = ((v << 1) | c) & 255
        elif op == 1:
            c = v & 1; r = (v >> 1) | (c << 7)
        elif op == 2:
            nc = v >> 7; r = ((v << 1) | c) & 255; c = nc
        elif op == 3:
            nc = v & 1; r = (v >> 1) | (c << 7); c = nc
        elif op == 4:
            c = v >> 7; r = (v << 1) & 255
        elif op == 5:
            c = v & 1; r = (v >> 1) | (v & 0x80)
        elif op == 6:
            c = v >> 7; r = ((v << 1) | 1) & 255
        else:
            c = v & 1; r = v >> 1
        self.f = (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | PAR[r] | c
        return r

    # ----- register by 3-bit code -----
    def getr(self, z, addr=None):
        return self.rb(addr) if z == 6 else self.r[z]

    def setr(self, z, v, addr=None):
        if z == 6:
            self.wb(addr, v)
        else:
            self.r[z] = v & 255

    # ----- execution -----
    def step(self):
        if self.pc in self.hooks:
            if self.hooks[self.pc](self):
                return
        if self.halted:
            self.t += 4
            return
        if self.pc >= 0x8000:
            self.exec_high.append(self.pc)
        self.insns += 1
        self.rr = (self.rr + 1) & 0x7F
        op = self.fetch()
        if op == 0xCB:
            return self.op_cb(None)
        if op == 0xED:
            return self.op_ed()
        if op in (0xDD, 0xFD):
            return self.op_idx(op)
        self.op_main(op)

    def disp_addr(self, base):
        d = self.fetch()
        if d > 127:
            d -= 256
        return (base + d) & 0xFFFF

    def op_main(self, op, hlreg=None):
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        p, q = y >> 1, y & 1
        if x == 1:
            if op == 0x76:
                self.halted = True
                self.t += 4
                return
            v = self.getr(z, self.hl)
            self.setr(y, v, self.hl)
            self.t += 7 if (z == 6 or y == 6) else 4
            return
        if x == 2:
            self.alu(y, self.getr(z, self.hl))
            self.t += 7 if z == 6 else 4
            return
        if x == 0:
            if z == 0:
                if y == 0:
                    self.t += 4
                elif y == 1:
                    self.f, self.alt_f = self.alt_f, self.f
                    self.r[7], self.alt[7] = self.alt[7], self.r[7]
                    self.alt_used = True
                    self.t += 4
                elif y == 2:
                    d = self.fetch(); d = d - 256 if d > 127 else d
                    self.r[0] = (self.r[0] - 1) & 255
                    if self.r[0]:
                        self.pc = (self.pc + d) & 0xFFFF
                        self.t += 13
                    else:
                        self.t += 8
                elif y == 3:
                    d = self.fetch(); d = d - 256 if d > 127 else d
                    self.pc = (self.pc + d) & 0xFFFF
                    self.t += 12
                else:
                    d = self.fetch(); d = d - 256 if d > 127 else d
                    if self.cond(y - 4):
                        self.pc = (self.pc + d) & 0xFFFF
                        self.t += 12
                    else:
                        self.t += 7
            elif z == 1:
                if q == 0:
                    self.set_rp(p, self.fetch16())
                    self.t += 10
                else:
                    a, b = self.hl, self.rp(p)
                    res = a + b
                    self.f = (self.f & (S_ | Z_ | P_)) | (((a ^ b ^ res) >> 8) & H_) | (C_ if res > 0xFFFF else 0) | ((res >> 8) & (Y_ | X_))
                    self.hl = res
                    self.t += 11
            elif z == 2:
                if q == 0:
                    if p == 0: self.wb(self.bc, self.a)
                    elif p == 1: self.wb(self.de, self.a)
                    elif p == 2: self.ww(self.fetch16(), self.hl)
                    else: self.wb(self.fetch16(), self.a)
                    self.t += (7, 7, 16, 13)[p]
                else:
                    if p == 0: self.a = self.rb(self.bc)
                    elif p == 1: self.a = self.rb(self.de)
                    elif p == 2: self.hl = self.rw(self.fetch16())
                    else: self.a = self.rb(self.fetch16())
                    self.t += (7, 7, 16, 13)[p]
            elif z == 3:
                self.set_rp(p, self.rp(p) + (1 if q == 0 else -1))
                self.t += 6
            elif z == 4:
                v = self.inc8(self.getr(y, self.hl))
                self.setr(y, v, self.hl)
                self.t += 11 if y == 6 else 4
            elif z == 5:
                v = self.dec8(self.getr(y, self.hl))
                self.setr(y, v, self.hl)
                self.t += 11 if y == 6 else 4
            elif z == 6:
                n = self.fetch()
                self.setr(y, n, self.hl)
                self.t += 10 if y == 6 else 7
            else:
                a = self.a
                if y == 0:
                    c = a >> 7; self.a = ((a << 1) | c); self.f = (self.f & (S_ | Z_ | P_)) | c | (self.a & (Y_ | X_))
                elif y == 1:
                    c = a & 1; self.a = (a >> 1) | (c << 7); self.f = (self.f & (S_ | Z_ | P_)) | c | (self.a & (Y_ | X_))
                elif y == 2:
                    c = a >> 7; self.a = (a << 1) | (self.f & C_); self.f = (self.f & (S_ | Z_ | P_)) | c | (self.a & (Y_ | X_))
                elif y == 3:
                    c = a & 1; self.a = (a >> 1) | ((self.f & C_) << 7); self.f = (self.f & (S_ | Z_ | P_)) | c | (self.a & (Y_ | X_))
                elif y == 4:   # DAA
                    f = self.f; adj = 0; c = f & C_
                    if (f & H_) or (a & 15) > 9: adj |= 6
                    if c or a > 0x99: adj |= 0x60; c = C_
                    if f & N_:
                        r = (a - adj) & 255; h = H_ if ((f & H_) and (a & 15) < 6) else 0
                    else:
                        r = (a + adj) & 255; h = H_ if (a & 15) > 9 else 0
                    self.a = r
                    self.f = (r & (S_ | Y_ | X_)) | (Z_ if r == 0 else 0) | h | PAR[r] | (f & N_) | c
                elif y == 5:
                    self.a = a ^ 255; self.f = (self.f & (S_ | Z_ | P_ | C_)) | H_ | N_ | (self.a & (Y_ | X_))
                elif y == 6:
                    self.f = (self.f & (S_ | Z_ | P_)) | C_ | (a & (Y_ | X_))
                else:
                    c = self.f & C_
                    self.f = (self.f & (S_ | Z_ | P_)) | (H_ if c else 0) | (0 if c else C_) | (a & (Y_ | X_))
                self.t += 4
            return
        # x == 3
        if z == 0:
            if self.cond(y):
                self.pc = self.pop(); self.t += 11
            else:
                self.t += 5
        elif z == 1:
            if q == 0:
                self.set_rp2(p, self.pop()); self.t += 10
            else:
                if p == 0: self.pc = self.pop(); self.t += 10
                elif p == 1:
                    self.exx(); self.t += 4
                elif p == 2: self.pc = self.hl; self.t += 4
                else: self.sp = self.hl; self.t += 6
        elif z == 2:
            a = self.fetch16()
            if self.cond(y): self.pc = a
            self.t += 10
        elif z == 3:
            if y == 0:
                self.pc = self.fetch16(); self.t += 10
            elif y == 2:
                n = self.fetch(); self.port_out(self.a << 8 | n, self.a); self.t += 11
            elif y == 3:
                n = self.fetch(); self.a = self.port_in(self.a << 8 | n); self.t += 11
            elif y == 4:
                v = self.rw(self.sp); self.ww(self.sp, self.hl); self.hl = v; self.t += 19
            elif y == 5:
                d = self.de; self.de = self.hl; self.hl = d; self.t += 4
            elif y == 6:
                self.iff = 0; self.t += 4
            elif y == 7:
                self.iff = 1; self.t += 4
            else:
                raise Z80Error('CB handled earlier')
        elif z == 4:
            a = self.fetch16()
            if self.cond(y):
                self.push(self.pc); self.pc = a; self.t += 17
            else:
                self.t += 10
        elif z == 5:
            if q == 0:
                self.push(self.rp2(p)); self.t += 11
            elif p == 0:
                a = self.fetch16(); self.push(self.pc); self.pc = a; self.t += 17
            else:
                raise Z80Error('prefix in op_main')
        elif z == 6:
            self.alu(y, self.fetch()); self.t += 7
        else:
            self.push(self.pc); self.pc = y * 8; self.t += 11

    def exx(self):
        for k in range(6):
            self.r[k], self.alt[k] = self.alt[k], self.r[k]
        self.alt_used = True

    def op_cb(self, addr, ixd=False):
        if addr is not None:
            op = self.fetch()
        else:
            op = self.fetch()
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        a = addr if addr is not None else self.hl
        v = self.getr(z, a) if addr is None else self.rb(addr)
        if x == 0:
            r = self.rot(y, v)
            self.setr(z, r, a) if addr is None else self.wb(addr, r)
            if addr is not None and z != 6:
                self.r[z] = r
        elif x == 1:
            b = (v >> y) & 1
            self.f = (self.f & C_) | H_ | (Z_ | P_ if not b else 0) | (S_ if (y == 7 and b) else 0) | (v & (Y_ | X_))
        elif x == 2:
            r = v & ~(1 << y)
            self.setr(z, r, a) if addr is None else self.wb(addr, r)
        else:
            r = v | (1 << y)
            self.setr(z, r, a) if addr is None else self.wb(addr, r)
        self.t += (12 if x == 1 else 15) if (z == 6 or addr is not None) else 8

    def op_ed(self):
        op = self.fetch()
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        p, q = y >> 1, y & 1
        if x == 1:
            if z == 0:
                v = self.port_in(self.bc)
                if y != 6:
                    self.r[y] = v
                self.f = (self.f & C_) | (v & (S_ | Y_ | X_)) | (Z_ if v == 0 else 0) | PAR[v]
                self.t += 12
            elif z == 1:
                self.port_out(self.bc, 0 if y == 6 else self.r[y]); self.t += 12
            elif z == 2:
                a, b = self.hl, self.rp(p); c = self.f & C_
                if q == 0:
                    res = a - b - c
                    self.f = ((res >> 8) & (S_ | Y_ | X_)) | (Z_ if (res & 0xFFFF) == 0 else 0) | (((a ^ b ^ res) >> 8) & H_) \
                        | (P_ if ((a ^ b) & (a ^ res) & 0x8000) else 0) | N_ | (C_ if res < 0 else 0)
                else:
                    res = a + b + c
                    self.f = ((res >> 8) & (S_ | Y_ | X_)) | (Z_ if (res & 0xFFFF) == 0 else 0) | (((a ^ b ^ res) >> 8) & H_) \
                        | (P_ if ((a ^ res) & (b ^ res) & 0x8000) else 0) | (C_ if res > 0xFFFF else 0)
                self.hl = res
                self.t += 15
            elif z == 3:
                a = self.fetch16()
                if q == 0:
                    self.ww(a, self.rp(p))
                else:
                    self.set_rp(p, self.rw(a))
                self.t += 20
            elif z == 4:
                a = self.a; self.a = 0; self.alu(2, a); self.t += 8
                # alu(2) computed 0 - a with A=0: restore semantic
            elif z == 5:
                self.pc = self.pop(); self.t += 14
            elif z == 6:
                self.t += 8
            else:
                if y == 0: self.i = self.a
                elif y == 2:
                    self.a = self.i
                    self.f = (self.f & C_) | (self.a & (S_ | Y_ | X_)) | (Z_ if self.a == 0 else 0)
                elif y == 1: self.rr = self.a
                elif y == 3: self.a = self.rr
                elif y == 4:
                    hv = self.rb(self.hl); a = self.a
                    nv = (hv >> 4) | ((a & 15) << 4)
                    self.a = (a & 0xF0) | (hv & 15); self.wb(self.hl, nv)
                    self.f = (self.f & C_) | (self.a & (S_ | Y_ | X_)) | (Z_ if self.a == 0 else 0) | PAR[self.a]
                elif y == 5:
                    hv = self.rb(self.hl); a = self.a
                    nv = ((hv << 4) | (a & 15)) & 255
                    self.a = (a & 0xF0) | (hv >> 4); self.wb(self.hl, nv)
                    self.f = (self.f & C_) | (self.a & (S_ | Y_ | X_)) | (Z_ if self.a == 0 else 0) | PAR[self.a]
                self.t += 9
            return
        if x == 2 and z <= 3 and y >= 4:
            rep = y >= 6
            dec = y & 1
            step = -1 if dec else 1
            while True:
                if z == 0:     # ldi/ldd
                    self.wb(self.de, self.rb(self.hl))
                    self.hl += step; self.de += step; self.bc -= 1
                    n = (self.a + self.rb((self.hl - step) & 0xFFFF)) & 255
                    self.f = (self.f & (S_ | Z_ | C_)) | (P_ if self.bc else 0)
                    self.t += 16
                    if rep and self.bc:
                        self.t += 5
                        continue
                    return
                elif z == 1:   # cpi/cpd
                    v = self.rb(self.hl); res = (self.a - v) & 255
                    self.hl += step; self.bc -= 1
                    self.f = (self.f & C_) | (res & S_) | (Z_ if res == 0 else 0) | (((self.a ^ v ^ res)) & H_) | (P_ if self.bc else 0) | N_
                    self.t += 16
                    if rep and self.bc and res != 0:
                        self.t += 5
                        continue
                    return
                else:
                    raise Z80Error('ED block io op %02X' % op)
        raise Z80Error('unsupported ED %02X at %04X' % (op, self.pc - 2))

    def op_idx(self, pre):
        reg = 'ix' if pre == 0xDD else 'iy'
        base = getattr(self, reg)
        op = self.fetch()
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        p, q = y >> 1, y & 1
        if op == 0xCB:
            addr = self.disp_addr(base)
            return self.op_cb(addr, True)
        if op == 0x21:
            setattr(self, reg, self.fetch16()); self.t += 14; return
        if op == 0x22:
            self.ww(self.fetch16(), base); self.t += 20; return
        if op == 0x2A:
            setattr(self, reg, self.rw(self.fetch16())); self.t += 20; return
        if op == 0x23:
            setattr(self, reg, (base + 1) & 0xFFFF); self.t += 10; return
        if op == 0x2B:
            setattr(self, reg, (base - 1) & 0xFFFF); self.t += 10; return
        if op in (0x09, 0x19, 0x29, 0x39):
            a = base; b = (self.bc, self.de, base, self.sp)[(op >> 4) & 3]
            res = a + b
            self.f = (self.f & (S_ | Z_ | P_)) | (((a ^ b ^ res) >> 8) & H_) | (C_ if res > 0xFFFF else 0)
            setattr(self, reg, res & 0xFFFF); self.t += 15; return
        if op == 0xE5:
            self.push(base); self.t += 15; return
        if op == 0xE1:
            setattr(self, reg, self.pop()); self.t += 14; return
        if op == 0xE9:
            self.pc = base; self.t += 8; return
        if op == 0xF9:
            self.sp = base; self.t += 10; return
        if op == 0xE3:
            v = self.rw(self.sp); self.ww(self.sp, base); setattr(self, reg, v); self.t += 23; return
        if op == 0x36:
            a = self.disp_addr(base); self.wb(a, self.fetch()); self.t += 19; return
        if op in (0x34, 0x35):
            a = self.disp_addr(base); v = self.rb(a)
            self.wb(a, self.inc8(v) if op == 0x34 else self.dec8(v)); self.t += 23; return
        if x == 1 and (z == 6 or y == 6) and op != 0x76:
            a = self.disp_addr(base)
            if z == 6:
                self.r[y] = self.rb(a)
            else:
                self.wb(a, self.r[z])
            self.t += 19; return
        if x == 2 and z == 6:
            a = self.disp_addr(base); self.alu(y, self.rb(a)); self.t += 19; return
        raise Z80Error('unsupported %s-op %02X at %04X' % (reg, op, self.pc - 2))

    def run(self, max_insns=10_000_000, until=None):
        n = 0
        while n < max_insns:
            if until is not None and self.pc == until:
                return True
            self.step()
            n += 1
        return False
