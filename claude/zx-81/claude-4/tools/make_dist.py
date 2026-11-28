# Build the tape images: RTCHAT (base) + topic blocks -> dist/*_vX.Y.Z.P and dist/retro_tinyllm_16k_vX.Y.Z.t81
import os, sys
RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RT + '/tools')
import build_image as B
VER = open(RT + '/VERSION').read().strip()
TAG = 'Claude_Haiku_5.5'                 # model name in every file name
VT = 'v%s_%s' % (VER, TAG)
lut = RT + '/ref/engine/rt_lut.h'
spec = [('RTLOAD', 'base_f.bin', 0), ('RTCHAT', 'base_f.bin', 0), ('WEATHER', 'topic_weather.bin', 1),
        ('ANIMALS', 'topic_animals.bin', 2), ('JOKES', 'topic_jokes.bin', 3),
        ('NUMBERS', 'topic_numbers.bin', 4)]
blocks = []
for name, model, tid in spec:
    mem, end = B.assemble(RT + '/models/' + model, lut, tid)
    if name == 'RTLOAD': mem[0x61DA] = 1      # LDR_FLAG: loader mode (asks data, then stops)
    img = B.p_image(mem)
    assert len(img) == 15889 and img[0] == 0 and img[-1] == 0x80
    open(RT + '/dist/%s_%s.P' % (name, VT), 'wb').write(img)
    blocks.append((name, img))
    print(name, 'code end %04x' % end, 'topic id', mem[0x5F6A])
t = B.eo81(blocks)
out = RT + '/dist/retro_tinyllm_16k_%s.t81' % VT
open(out, 'wb').write(t)
d = t; p = 4; names = []
while p < len(d):
    name = d[p:p+32].rstrip(b'\0').decode(); n = int(d[p+32:p+48].rstrip(b'\0')); data = d[p+48:p+48+n]
    names.append((name, n, data[0])); p += 48 + n
print('t81', len(t), 'bytes;', names, 'exact EOF', p == len(d), '->', out)
