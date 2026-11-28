#!/usr/bin/env python3
"""z80asm.py - small two-pass Z80 text assembler (stdlib only).

Supports: org, equ, db/defb, dw/defw, ds/defs, labels (name:), local labels
(.name -> scoped to the previous global label), expressions (+ - * / % << >> & | ^ ~,
$hex 0xhex %bin 'c' "s" $ = current address, lo()/hi()), and the Z80
instruction set subset used by this project (documented opcodes incl. IX/IY basics).
"""
import re
import sys

R8 = {'b': 0, 'c': 1, 'd': 2, 'e': 3, 'h': 4, 'l': 5, 'a': 7}
R16 = {'bc': 0, 'de': 1, 'hl': 2, 'sp': 3}
R16AF = {'bc': 0, 'de': 1, 'hl': 2, 'af': 3}
CC = {'nz': 0, 'z': 1, 'nc': 2, 'c': 3, 'po': 4, 'pe': 5, 'p': 6, 'm': 7}
ALU = {'add': 0, 'adc': 1, 'sub': 2, 'sbc': 3, 'and': 4, 'xor': 5, 'or': 6, 'cp': 7}
ROT = {'rlc': 0, 'rrc': 1, 'rl': 2, 'rr': 3, 'sla': 4, 'sra': 5, 'sll': 6, 'srl': 7}
SIMPLE = {
    'nop': [0x00], 'halt': [0x76], 'rlca': [0x07], 'rrca': [0x0F], 'rla': [0x17], 'rra': [0x1F],
    'daa': [0x27], 'cpl': [0x2F], 'scf': [0x37], 'ccf': [0x3F], 'di': [0xF3], 'ei': [0xFB],
    'exx': [0xD9], 'neg': [0xED, 0x44], 'ldi': [0xED, 0xA0], 'ldir': [0xED, 0xB0],
    'ldd': [0xED, 0xA8], 'lddr': [0xED, 0xB8], 'cpi': [0xED, 0xA1], 'cpir': [0xED, 0xB1],
    'cpd': [0xED, 0xA9], 'cpdr': [0xED, 0xB9], 'reti': [0xED, 0x4D], 'retn': [0xED, 0x45],
    'rld': [0xED, 0x6F], 'rrd': [0xED, 0x67],
}


class AsmError(Exception):
    pass


class Asm:
    def __init__(self):
        self.syms = {}
        self.out = {}          # addr -> byte
        self.listing = []
        self.pc = 0
        self.scope = ''
        self.pass_no = 0
        self.lineno = 0
        self.cur = ''

    # ---------- expressions ----------
    def ev(self, s, allow_undef=None):
        s = s.strip()
        if allow_undef is None:
            allow_undef = (self.pass_no == 1)

        def chr_sub(m):
            return str(ord(m.group(1)))
        s2 = re.sub(r"'(.)'", chr_sub, s)
        s2 = re.sub(r"\$([0-9A-Fa-f]+)\b", lambda m: '0x' + m.group(1), s2)
        s2 = re.sub(r"%([01]+)\b", lambda m: '0b' + m.group(1), s2)
        s2 = re.sub(r"\$(?![0-9A-Fa-f])", str(self.pc), s2)
        s2 = s2.replace('/', '//')

        def name_sub(m):
            n = m.group(0)
            if n in ('lo', 'hi'):
                return n
            if re.fullmatch(r'0[xb][0-9A-Fa-f]+', n) or n.isdigit():
                return n
            key = n
            if n.startswith('.'):
                key = self.scope + n
            if key in self.syms:
                return str(self.syms[key])
            if allow_undef:
                return '0'
            raise AsmError("undefined symbol '%s'" % n)
        s2 = re.sub(r"\.?[A-Za-z_][A-Za-z_0-9]*|0[xb][0-9A-Fa-f]+|\d+", name_sub, s2)
        try:
            return int(eval(s2, {'__builtins__': {}}, {'lo': lambda v: v & 255, 'hi': lambda v: (v >> 8) & 255}))
        except Exception as e:
            raise AsmError("bad expression '%s' (%s)" % (s, e))

    # ---------- operand helpers ----------
    @staticmethod
    def split_ops(s):
        ops, cur, depth, q = [], '', 0, None
        for ch in s:
            if q:
                cur += ch
                if ch == q:
                    q = None
                continue
            if ch in '"\'':
                q = ch
                cur += ch
            elif ch == '(':
                depth += 1
                cur += ch
            elif ch == ')':
                depth -= 1
                cur += ch
            elif ch == ',' and depth == 0:
                ops.append(cur.strip())
                cur = ''
            else:
                cur += ch
        if cur.strip():
            ops.append(cur.strip())
        return ops

    def idx(self, op):
        m = re.fullmatch(r'\((ix|iy)\s*([+-].*)?\)', op, re.I)
        if not m:
            return None
        d = self.ev(m.group(2)) if m.group(2) else 0
        if not -128 <= d <= 127 and self.pass_no == 2:
            raise AsmError('index displacement out of range')
        return (0xDD if m.group(1).lower() == 'ix' else 0xFD, d & 255)

    def is_mem(self, op):
        return op.startswith('(') and op.endswith(')') and not self.idx(op) and op.lower() not in ('(hl)', '(bc)', '(de)', '(sp)', '(c)')

    def r8(self, op):
        """returns (prefix_bytes, code, trailing_disp_bytes) for r/(hl)/(ix+d)"""
        o = op.lower()
        if o in R8:
            return ([], R8[o], [])
        if o == '(hl)':
            return ([], 6, [])
        ix = self.idx(op)
        if ix:
            return ([ix[0]], 6, [ix[1]])
        return None

    # ---------- encode ----------
    def encode(self, mn, ops):
        mn = mn.lower()
        o = [x for x in ops]
        ol = [x.lower() for x in o]
        n = len(o)

        def imm8(e):
            v = self.ev(e)
            if self.pass_no == 2 and not -128 <= v <= 255:
                raise AsmError('8-bit value out of range: %s' % e)
            return [v & 255]

        def imm16(e):
            v = self.ev(e)
            return [v & 255, (v >> 8) & 255]

        if mn in SIMPLE and n == 0:
            return SIMPLE[mn]
        if mn == 'ex':
            if ol == ['de', 'hl']:
                return [0xEB]
            if ol == ['af', "af'"]:
                return [0x08]
            if ol == ['(sp)', 'hl']:
                return [0xE3]
            if ol == ['(sp)', 'ix']:
                return [0xDD, 0xE3]
            if ol == ['(sp)', 'iy']:
                return [0xFD, 0xE3]
        if mn == 'ld':
            d, s = o
            dl, sl = ol
            # 16-bit loads
            if dl in R16 and sl not in R8 and not self.is_mem(s) and sl not in ('(hl)', '(bc)', '(de)') and not self.idx(s) and sl != 'hl' and dl != 'sp' or (dl == 'sp' and sl not in ('hl', 'ix', 'iy') and not self.is_mem(s)):
                return [0x01 | R16[dl] << 4] + imm16(s)
            if dl == 'sp' and sl == 'hl':
                return [0xF9]
            if dl in ('ix', 'iy'):
                pre = 0xDD if dl == 'ix' else 0xFD
                if self.is_mem(s):
                    return [pre, 0x2A] + imm16(s[1:-1])
                return [pre, 0x21] + imm16(s)
            if sl in ('ix', 'iy') and self.is_mem(d):
                return [0xDD if sl == 'ix' else 0xFD, 0x22] + imm16(d[1:-1])
            if dl in R16 and self.is_mem(s):
                if dl == 'hl':
                    return [0x2A] + imm16(s[1:-1])
                return [0xED, 0x4B | R16[dl] << 4] + imm16(s[1:-1])
            if sl in R16 and self.is_mem(d):
                if sl == 'hl':
                    return [0x22] + imm16(d[1:-1])
                return [0xED, 0x43 | R16[sl] << 4] + imm16(d[1:-1])
            if dl == 'a' and sl in ('(bc)', '(de)'):
                return [0x0A if sl == '(bc)' else 0x1A]
            if sl == 'a' and dl in ('(bc)', '(de)'):
                return [0x02 if dl == '(bc)' else 0x12]
            if dl == 'a' and self.is_mem(s):
                return [0x3A] + imm16(s[1:-1])
            if sl == 'a' and self.is_mem(d):
                return [0x32] + imm16(d[1:-1])
            if dl == 'a' and sl == 'i':
                return [0xED, 0x57]
            if dl == 'i' and sl == 'a':
                return [0xED, 0x47]
            dd, ss = self.r8(d), self.r8(s)
            if dd and ss:
                if dd[1] == 6 and ss[1] == 6:
                    raise AsmError('ld (hl),(hl)')
                pre = dd[0] or ss[0]
                disp = dd[2] or ss[2]
                # with index: other operand must be plain register
                return pre + [0x40 | dd[1] << 3 | ss[1]] + disp
            if dd and not ss:
                return dd[0] + [0x06 | dd[1] << 3] + dd[2] + imm8(s)
        if mn in ALU or (mn in ('sub', 'and', 'xor', 'or', 'cp')):
            if mn in ('add', 'adc', 'sbc') and n == 2 and ol[0] in ('hl', 'ix', 'iy'):
                p = R16[ol[1]] if ol[1] in R16 else (2 if ol[1] == ol[0] else None)
                if ol[0] == 'hl':
                    if mn == 'add':
                        return [0x09 | p << 4]
                    return [0xED, (0x4A if mn == 'adc' else 0x42) | p << 4]
                pre = 0xDD if ol[0] == 'ix' else 0xFD
                if ol[1] == ol[0]:
                    p = 2
                return [pre, 0x09 | p << 4]
            if n == 2 and ol[0] == 'a':
                src = o[1]
            elif n == 1:
                src = o[0]
            else:
                raise AsmError('bad operands for ' + mn)
            op = ALU[mn]
            rr = self.r8(src)
            if rr:
                return rr[0] + [0x80 | op << 3 | rr[1]] + rr[2]
            return [0xC6 | op << 3] + imm8(src)
        if mn in ('inc', 'dec'):
            a = ol[0]
            if a in R16:
                return [(0x03 if mn == 'inc' else 0x0B) | R16[a] << 4]
            if a in ('ix', 'iy'):
                return [0xDD if a == 'ix' else 0xFD, 0x23 if mn == 'inc' else 0x2B]
            rr = self.r8(o[0])
            if rr:
                return rr[0] + [(0x04 if mn == 'inc' else 0x05) | rr[1] << 3] + rr[2]
        if mn in ('push', 'pop'):
            a = ol[0]
            if a in ('ix', 'iy'):
                return [0xDD if a == 'ix' else 0xFD, 0xE5 if mn == 'push' else 0xE1]
            return [(0xC5 if mn == 'push' else 0xC1) | R16AF[a] << 4]
        if mn == 'jp':
            if n == 1:
                if ol[0] == '(hl)':
                    return [0xE9]
                if ol[0] == '(ix)':
                    return [0xDD, 0xE9]
                if ol[0] == '(iy)':
                    return [0xFD, 0xE9]
                return [0xC3] + imm16(o[0])
            return [0xC2 | CC[ol[0]] << 3] + imm16(o[1])
        if mn == 'call':
            if n == 1:
                return [0xCD] + imm16(o[0])
            return [0xC4 | CC[ol[0]] << 3] + imm16(o[1])
        if mn == 'ret':
            if n == 0:
                return [0xC9]
            return [0xC0 | CC[ol[0]] << 3]
        if mn == 'rst':
            v = self.ev(o[0])
            return [0xC7 | (v & 0x38)]
        if mn in ('jr', 'djnz'):
            if mn == 'djnz':
                opc, tgt = 0x10, o[0]
            elif n == 1:
                opc, tgt = 0x18, o[0]
            else:
                opc, tgt = {'nz': 0x20, 'z': 0x28, 'nc': 0x30, 'c': 0x38}[ol[0]], o[1]
            t = self.ev(tgt)
            rel = t - (self.pc + 2)
            if self.pass_no == 2 and not -128 <= rel <= 127:
                raise AsmError('jr/djnz out of range (%d) to %s' % (rel, tgt))
            return [opc, rel & 255]
        if mn in ROT:
            rr = self.r8(o[0])
            if rr[0]:
                return rr[0] + [0xCB] + rr[2] + [ROT[mn] << 3 | rr[1]]
            return [0xCB, ROT[mn] << 3 | rr[1]]
        if mn in ('bit', 'res', 'set'):
            b = self.ev(o[0])
            rr = self.r8(o[1])
            base = {'bit': 0x40, 'res': 0x80, 'set': 0xC0}[mn]
            if rr[0]:
                return rr[0] + [0xCB] + rr[2] + [base | b << 3 | rr[1]]
            return [0xCB, base | b << 3 | rr[1]]
        if mn == 'in':
            if ol[0] == 'a' and self.is_mem(o[1]):
                return [0xDB] + imm8(o[1][1:-1])
            if ol[1] == '(c)':
                return [0xED, 0x40 | R8[ol[0]] << 3]
        if mn == 'out':
            if ol[1] == 'a' and self.is_mem(o[0]):
                return [0xD3] + imm8(o[0][1:-1])
            if ol[0] == '(c)':
                return [0xED, 0x41 | R8[ol[1]] << 3]
        if mn == 'im':
            return [0xED, {0: 0x46, 1: 0x56, 2: 0x5E}[self.ev(o[0])]]
        raise AsmError('cannot encode: %s %s' % (mn, ', '.join(o)))

    # ---------- driver ----------
    def data_bytes(self, mn, rest):
        out = []
        for item in self.split_ops(rest):
            if len(item) >= 2 and item[0] == '"' and item[-1] == '"':
                if mn in ('db', 'defb'):
                    out += [ord(c) for c in item[1:-1]]
                else:
                    raise AsmError('string in dw')
            elif mn in ('db', 'defb'):
                v = self.ev(item)
                if self.pass_no == 2 and not -128 <= v <= 255:
                    raise AsmError('db value out of range: ' + item)
                out.append(v & 255)
            else:
                v = self.ev(item)
                out += [v & 255, (v >> 8) & 255]
        return out

    def assemble(self, text, filename='<src>'):
        lines = text.split('\n')
        for self.pass_no in (1, 2):
            self.pc = 0
            self.scope = ''
            self.out = {}
            self.listing = []
            for self.lineno, raw in enumerate(lines, 1):
                self.cur = raw
                try:
                    self.line(raw)
                except AsmError as e:
                    raise AsmError('%s:%d: %s\n    %s' % (filename, self.lineno, e, raw.strip()))
        return self

    def line(self, raw):
        # strip comments (not inside quotes)
        s, q, res = raw, None, ''
        for ch in s:
            if q:
                res += ch
                if ch == q:
                    q = None
            elif ch in '"\'':
                # a lone apostrophe like  ex af,af'  must not open a string
                if ch == "'" and res.rstrip().lower().endswith('af,af'):
                    res += ch
                else:
                    q = ch
                    res += ch
            elif ch == ';':
                break
            else:
                res += ch
        s = res.strip()
        if not s:
            return
        m = re.match(r'^(\.?[A-Za-z_][A-Za-z_0-9]*)\s*:(.*)$', s)
        label = None
        if m:
            label, s = m.group(1), m.group(2).strip()
        else:
            m2 = re.match(r'^(\.?[A-Za-z_][A-Za-z_0-9]*)\s+equ\s+(.*)$', s, re.I)
            if m2:
                name = m2.group(1)
                self.syms[name] = self.ev(m2.group(2), allow_undef=True if self.pass_no == 1 else False)
                return
        if label:
            if not label.startswith('.'):
                self.scope = label
                key = label
            else:
                key = self.scope + label
            if self.pass_no == 1 and key in self.syms:
                raise AsmError('duplicate label ' + key)
            self.syms[key] = self.pc
        if not s:
            return
        parts = s.split(None, 1)
        mn = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ''
        if mn == 'org':
            self.pc = self.ev(rest, allow_undef=False)
            return
        if mn in ('db', 'defb', 'dw', 'defw'):
            b = self.data_bytes(mn, rest)
        elif mn in ('ds', 'defs'):
            ps = self.split_ops(rest)
            cnt = self.ev(ps[0], allow_undef=False)
            val = self.ev(ps[1]) if len(ps) > 1 else 0
            b = [val & 255] * cnt
        else:
            b = self.encode(mn, self.split_ops(rest))
        if self.pass_no == 2:
            for i, v in enumerate(b):
                self.out[self.pc + i] = v
            self.listing.append((self.pc, bytes(b), raw.strip()))
        self.pc += len(b)

    def image(self, lo=None, hi=None):
        if not self.out:
            return b''
        lo = min(self.out) if lo is None else lo
        hi = max(self.out) + 1 if hi is None else hi
        return bytes(self.out.get(a, 0) for a in range(lo, hi))


if __name__ == '__main__':
    a = Asm().assemble(open(sys.argv[1]).read(), sys.argv[1])
    open(sys.argv[2], 'wb').write(a.image())
    print('%d bytes, org $%04X' % (len(a.image()), min(a.out)))
