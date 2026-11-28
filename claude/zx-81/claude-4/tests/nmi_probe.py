import sys; sys.path.insert(0, '/home/claude/rt16/release/tests')
import nmi_run
from run_app import setup
from z80emu import Z80
mem, syms = setup()
print({k: hex(syms[k]) for k in ('GK_W','GK_T','BOOT') if k in syms})
