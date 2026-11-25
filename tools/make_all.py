# -*- coding: utf-8 -*-
import os, json, sys, time
from PIL import Image
import gen_scores as g
from pieces import PIECES

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'haegeum-lounge'))
SCORES = os.path.join(REPO, 'scores')
THUMBS = os.path.join(REPO, 'scores', 'thumb')
os.makedirs(SCORES, exist_ok=True)
os.makedirs(THUMBS, exist_ok=True)

def meters_label(sections):
    labels = []
    for count, meter in sections:
        l = g.METER_LABEL[meter]
        if not labels or labels[-1] != l:
            labels.append(l)
    return labels

def main(only=None):
    out = []
    t0 = time.time()
    for cfg in PIECES:
        if only and cfg['no'] not in only:
            continue
        xml, b, mxs = g.build_piece(cfg)
        g.validate_xml(xml, cfg)
        png, pdf, size = g.render(xml, cfg['no'], SCORES)
        im = Image.open(png)
        th = im.copy()
        th.thumbnail((620, 1000), Image.LANCZOS)
        th.save(os.path.join(THUMBS, f"{cfg['no']:03d}.jpg"), quality=82, optimize=True)
        meta = dict(no=cfg['no'], level=cfg['level'], key=g.KEY_LABEL[cfg['key']],
                    fifths=g.KEY_FIFTHS[cfg['key']], title=cfg['title'],
                    meters=meters_label(cfg['sections']),
                    tempos=[cfg['tempos'][k] for k in sorted(cfg['tempos'])],
                    bars=32, tags=cfg.get('tags', []),
                    image=f"scores/{cfg['no']:03d}.png",
                    pdf=f"scores/{cfg['no']:03d}.pdf",
                    thumb=f"scores/thumb/{cfg['no']:03d}.jpg")
        out.append(meta)
        print(f"#{cfg['no']:3d} {cfg['level']} {meta['key']:2s} {'/'.join(meta['meters']):18s} "
              f"png {os.path.getsize(png)//1024}KB pdf {os.path.getsize(pdf)//1024}KB")
    with open(os.path.join(REPO, 'pieces.json'), 'w', encoding='utf-8') as f:
        # 기존 파일이 있으면 병합
        old = []
        if os.path.exists(os.path.join(REPO, 'pieces.json')):
            try:
                old = json.load(open(os.path.join(REPO, 'pieces.json'), encoding='utf-8'))
            except Exception:
                old = []
        merged = {p['no']: p for p in old}
        for p in out:
            merged[p['no']] = p
        json.dump([merged[k] for k in sorted(merged)], f, ensure_ascii=False, indent=1)
    print('elapsed', round(time.time() - t0, 1), 's')

if __name__ == '__main__':
    only = [int(x) for x in sys.argv[1:]] or None
    main(only)
