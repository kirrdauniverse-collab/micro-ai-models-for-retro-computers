import os as _os
RT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, os; sys.path.insert(0,RT+'/tests')
import ref_gen as R
for p in ['what is 6 plus 6?', 'is it raining?', 'tell me a joke.', 'what time is it?', 'i am sad.']:
    print(repr(p), '->', repr(R.gen(p, 40)))
