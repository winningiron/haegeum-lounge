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

ASSET_VER = '9'   # 악보를 다시 조판할 때 올린다 (브라우저 캐시 무효화)


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
        problems = g.check_line_plan(cfg)
        if problems:
            raise RuntimeError(f"#{cfg['no']}: " + '; '.join(problems))
        br = g.line_breaks(cfg)
        total = g.piece_total(cfg)
        xml, b, mxs = g.build_piece(cfg, breaks_at=br)
        g.validate_xml(xml, cfg)
        expect = g.line_counts(br, total)
        counts = g.system_measure_counts(xml, g.LAYOUT)
        if counts != expect:
            raise RuntimeError(f"#{cfg['no']}: 줄 마디 수 {counts} != 계획 {expect}")
        if len(counts) != g.SYSTEMS_PER_PAGE:
            raise RuntimeError(f"#{cfg['no']}: 줄이 {len(counts)}개")
        png, pdf, size = g.render(xml, cfg['no'], SCORES,
                                  layout=dict(breaks='encoded'), total=total)
        im = Image.open(png)
        th = im.copy()
        th.thumbnail((560, 800), Image.LANCZOS)
        th.save(os.path.join(THUMBS, f"{cfg['no']:03d}.jpg"), quality=82, optimize=True)
        meta = dict(no=cfg['no'], level=cfg['level'], key=g.KEY_LABEL[cfg['key']],
                    fifths=g.KEY_FIFTHS[cfg['key']], title=cfg['title'],
                    meters=meters_label(cfg['sections']),
                    tempos=[cfg['tempos'][k] for k in sorted(cfg['tempos'])],
                    bars=total, lines=counts,
                    midline=bool(cfg.get('midline')),
                    focus=cfg.get('focus', ''),
                    tags=cfg.get('tags', []),
                    image=f"scores/{cfg['no']:03d}.png?v={ASSET_VER}",
                    pdf=f"scores/{cfg['no']:03d}.pdf?v={ASSET_VER}",
                    thumb=f"scores/thumb/{cfg['no']:03d}.jpg?v={ASSET_VER}")
        out.append(meta)
        print(f"#{cfg['no']:3d} {cfg['level']} {meta['key']:2s} {'/'.join(meta['meters']):18s} "
              f"{'x'.join(map(str, counts))} "
              f"png {os.path.getsize(png)//1024}KB pdf {os.path.getsize(pdf)//1024}KB")
    json_path = os.path.join(REPO, 'pieces.json')
    old = []
    if os.path.exists(json_path):
        try:
            old = json.load(open(json_path, encoding='utf-8'))
        except Exception:
            old = []
    merged = {p['no']: p for p in old}
    for p in out:
        merged[p['no']] = p
    rows = [merged[k] for k in sorted(merged)]
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    js_path = os.path.join(REPO, 'data', 'pieces.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write('/* 자동 생성: tools/make_all.py */\nwindow.PIECES = ')
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.write(';\n')
    print('elapsed', round(time.time() - t0, 1), 's')

if __name__ == '__main__':
    only = [int(x) for x in sys.argv[1:]] or None
    main(only)
