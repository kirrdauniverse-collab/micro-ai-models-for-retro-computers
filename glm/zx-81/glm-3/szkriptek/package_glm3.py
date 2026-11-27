#!/usr/bin/env python3
"""GLM3 konyvtar felepitese a sandbox anyagaibol a GitHub-klonban
(repos/zx81-ai-micro). Idempotens: mindig ujraepiti a GLM3/-et.

Futtatas:
  python3 scripts/package_glm3.py            # masolas + kazetta-MD5 ellenorzes
  python3 scripts/package_glm3.py --manifest # TELJES_LELTAR.txt ujrageneralasa
                                             # (a README/HIBA dokumentumok UTAN futtando)
"""
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path('/home/z/my-project')
REPO = ROOT / 'repos' / 'zx81-ai-micro'
GLM3 = REPO / 'GLM3'
DL = ROOT / 'download'
GLMD = ROOT / 'GLM'
SCR = ROOT / 'scripts'

# A bizonyitott kazetta MD5-ok — a masolas utani bitegyezes-ellenorzeshez
KAZETTAK = {
    'GLM_PicoAI_v0.6.5_kazetta.T81': '1162414c907f7a0b13c5cc2b4999c0de',
    'GLM_PicoAI_v0.7.1_kazetta.T81': '160b23b5c258b428bd37d021cbc96f3d',
    'GLM_PicoAI_v0.7.2_kazetta.T81': '8f7025f1a6fd25b7e2ddc326a0df20e9',
    'GLM_PicoAI_v0.7.3_kazetta.T81': 'fae288550aa51884df6560f7c260ef8b',
    'GLM_PicoAI_v0.8.0_kazetta.T81': 'd7f154b6130871c801c05a896ce71d18',
    'GLM_PicoAI_v0.8.1_kazetta.T81': 'abbf634478e97f7c0b44ebfd852c6a5b',
    'GLM_PicoAI_v0.9.2_kazetta.T81': '6f5fc138e66e2ccdd52b982fffdb9003',
}


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def copy_tree(src: Path, dst: Path, skip=('__pycache__',)):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in skip:
            continue
        if item.is_dir():
            copy_tree(item, dst / item.name, skip)
        else:
            shutil.copy2(item, dst / item.name)


def main():
    if '--manifest' in sys.argv:
        write_manifest()
        return

    if GLM3.exists():
        shutil.rmtree(GLM3)

    kaz = GLM3 / 'kazettak'
    kaz.mkdir(parents=True)

    # 1) kazettak bitegyezes-ellenorzessel
    for name, want in KAZETTAK.items():
        src = DL / name
        if not src.exists():
            raise SystemExit(f'HIBA: hianyzik {src}')
        shutil.copy2(src, kaz / name)
        got = md5(kaz / name)
        if got != want:
            raise SystemExit(f'HIBA: MD5-elteres {name}: {got} != {want}')
    print('kazettak: 7 db, MD5 bitegyezik')

    # 2) elozmenyek (v0.7.0 elotti nevtelen kiadasok)
    copy_tree(DL / 'elozmenyek_v0.7.0_elott', kaz / 'elozmenyek_v0.7.0_elott')

    # 3) dokumentaciok + valtozasnaplok + forrascsomagok
    (GLM3 / 'dokumentacio').mkdir()
    (GLM3 / 'forraskod_csomagok').mkdir()
    doc_suffixes = ('dokumentacio.txt', 'dokumentacio.docx', 'dokumentacio.pdf',
                    'valtozasnaplo.txt', 'valtozas_attekintes.txt')
    for p in sorted(DL.iterdir()):
        n = p.name
        if not n.startswith('GLM_PicoAI_'):
            continue
        if n.endswith(doc_suffixes):
            shutil.copy2(p, GLM3 / 'dokumentacio' / n)
        elif n.endswith('_forraskod_csomag.zip'):
            shutil.copy2(p, GLM3 / 'forraskod_csomagok' / n)

    # 4) allapot (menetnaplok)
    allst = GLM3 / 'allapot'
    allst.mkdir()
    for n in ('STATE.md', 'STATE_v0.7.1_backup.md', 'PROJECTLOG.md'):
        shutil.copy2(GLMD / n, allst / n)

    # 5) szkriptek (epito/diagnosztika keszlet)
    copy_tree(SCR, GLM3 / 'szkriptek')

    # 6) motor, referenciak, regi repo eszkozok (node_modules es .git NELKUL), toolchain
    copy_tree(GLMD / 'v090', GLM3 / 'motor_v090')
    copy_tree(GLMD / 'refs', GLM3 / 'refs')
    reposz = GLM3 / 'eszkozok_regi_repo'
    for n in ('tools', 'engine', 'dist', 'docs', 'data', 'tests',
              'README.md', 'package.json', 'bun.lock', 'LICENSE', 'publish.sh'):
        s = GLMD / 'repo' / n
        if s.is_dir():
            copy_tree(s, reposz / n)
        elif s.exists():
            shutil.copy2(s, reposz / n)
    tool = GLM3 / 'toolchain'
    tool.mkdir()
    shutil.copy2(DL / 'GLM_z88dk_2.5_zx81_toolchain.tar.gz',
                 tool / 'GLM_z88dk_2.5_zx81_toolchain.tar.gz')

    # 7) kazetta-MD5 kartya
    lines = ['# Kazetta MD5-kartya (GLM3/kazettak)', '# nev  meret_bajt  md5', '']
    for name in sorted(KAZETTAK):
        p = kaz / name
        lines.append(f'{name}  {p.stat().st_size}  {md5(p)}')
    (kaz / 'MD5SUMS.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('MASOLAS KESZ')
    summarize()


def summarize():
    n_files = 0
    total = 0
    print(f'{"konyvtar":26s} {"fajlok":>7s} {"meret":>12s}')
    for d in sorted(GLM3.iterdir()):
        if d.is_file():
            c, s = 1, d.stat().st_size
            name = d.name
        else:
            files = [x for x in d.rglob('*') if x.is_file()]
            c, s = len(files), sum(x.stat().st_size for x in files)
            name = d.name + '/'
        print(f'{name:26s} {c:7d} {s:12d}')
        n_files += c
        total += s
    print(f'{"OSSZ":26s} {n_files:7d} {total:12d}  ({total / 1e6:.1f} MB)')


def write_manifest():
    lines = ['# GLM3 TELJES LELTAR (package_glm3.py --manifest)',
             '# meret_bajt  md5  relativ_ut', '']
    files = sorted(p for p in GLM3.rglob('*')
                   if p.is_file() and p.name != 'TELJES_LELTAR.txt')
    total = 0
    for p in files:
        s = p.stat().st_size
        total += s
        lines.append(f'{s:10d}  {md5(p)}  {p.relative_to(GLM3)}')
    lines.append(f'# OSSZ: {len(files)} fajl, {total} bajt')
    (GLM3 / 'TELJES_LELTAR.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'LELTAR: {len(files)} fajl, {total} bajt')


if __name__ == '__main__':
    main()
