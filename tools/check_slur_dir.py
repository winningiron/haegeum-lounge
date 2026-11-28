# -*- coding: utf-8 -*-
"""슬러가 기둥(꼬리) 반대쪽에 그려졌는지 조판 SVG 에서 확인한다 (200곡 전수 검증).

곡 슬러(number 1)마다
  1) XML 이 적은 placement,
  2) Verovio 가 실제로 그린 쪽(곡선이 불룩한 쪽),
  3) 그 슬러가 덮는 음표들의 실제 기둥 방향
을 비교한다. 기둥이 위면 슬러는 아래(below), 기둥이 아래면 위(above)여야 한다.

음표 ↔ item 대응은 문서 순서로 맞춘다 (쉼표는 양쪽에서 뺀다. 장식음은 양쪽에 모두 있다).
usage: python3 tools/check_slur_dir.py [곡번호 ...]
"""
import sys, os, re, statistics
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verovio
import gen_scores as g
from pieces import PIECES

NS = '{http://www.w3.org/2000/svg}'


def nums(s):
    return [float(v) for v in re.findall(r'-?\d+\.?\d*', s)]


def svg_of(cfg):
    br = g.line_breaks(cfg)
    xml, b, mxs = g.build_piece(cfg, breaks_at=br)
    tk = verovio.toolkit()
    opts = dict(g.LAYOUT)
    opts.update(dict(breaks='encoded'))
    tk.setOptions(opts)
    tk.loadData(xml)
    svg = tk.renderToSVG(1)
    svg = g.spread_systems(svg, opts['pageHeight'])
    svg = re.sub(r'<rect class="page-margin"[^>]*/>', '', svg)
    return svg, xml, mxs


def parse_measure(meas):
    notes, slurs = [], []
    for el in meas.iter(NS + 'g'):
        cls = (el.attrib.get('class') or '').split()
        if cls[:1] == ['note']:
            head = stem = x = None
            for ch in el:
                c2 = (ch.attrib.get('class') or '').split()
                if c2[:1] == ['notehead']:
                    for u in ch.iter(NS + 'use'):
                        n = nums(u.attrib.get('transform', ''))
                        if len(n) >= 2:
                            head, x = n[1], n[0]
                if c2[:1] == ['stem']:
                    for p in ch.iter(NS + 'path'):
                        d = nums(p.attrib.get('d', ''))
                        if len(d) >= 4:
                            stem = 'down' if d[3] > d[1] else 'up'
            notes.append(dict(x=x, y=head, stem=stem))
        if cls[:1] == ['slur']:
            for p in el.iter(NS + 'path'):
                d = nums(p.attrib.get('d', ''))
                if len(d) >= 8:
                    ys = d[1::2]
                    slurs.append(dict(x0=min(d[0::2]), x1=max(d[0::2]),
                                      bulge=(d[3] + d[5]) / 2.0))
    return notes, slurs


def analyse(cfg):
    svg, xml, mxs = svg_of(cfg)
    root = ET.fromstring(svg)
    out = []
    mi = 0
    for meas in root.iter(NS + 'g'):
        if 'measure' not in (meas.attrib.get('class') or '').split():
            continue
        items = mxs[mi]['items']
        notes, slurs = parse_measure(meas)
        mi += 1
        idx = [i for i, x in enumerate(items) if not x['rest']]
        if len(idx) != len(notes):
            out.append(dict(ok=False, why='note-count', m=mi,
                            n_svg=len(notes), n_item=len(idx)))
            continue
        pos = dict(zip(idx, notes))
        # 곡 슬러 구간
        i = 0
        while i < len(items):
            if 'start' in (items[i].get('slur') or []):
                j = i + 1
                while j < len(items) and 'stop' not in (items[j].get('slur') or []):
                    j += 1
                if j >= len(items):
                    break
                cover = [pos[k] for k in range(i, j + 1)
                         if k in pos and not items[k].get('grace')]
                n0, n1 = pos.get(i), pos.get(j)
                if cover and n0 and n1:
                    s = min(slurs, key=lambda q: abs(q['x0'] - n0['x']) + abs(q['x1'] - n1['x']),
                            default=None) if slurs else None
                    stems = [c['stem'] for c in cover if c['stem']]
                    if s and stems:
                        heads = statistics.mean(c['y'] for c in cover)
                        side = 'below' if s['bulge'] > heads else 'above'
                        ups = stems.count('up')
                        downs = stems.count('down')
                        want = 'below' if ups >= downs else 'above'   # 같으면 첫 음 쪽(아래)을 따른다
                        out.append(dict(ok=(side == want), why='dir', side=side, want=want,
                                        up=ups, down=downs, m=mi))
                i = j
            i += 1
    return out


if __name__ == '__main__':
    only = [int(x) for x in sys.argv[1:]] or None
    bad = tot = 0
    for cfg in PIECES:
        if only and cfg['no'] not in only:
            continue
        res = analyse(cfg)
        b = [r for r in res if not r['ok']]
        tot += len(res)
        bad += len(b)
        if b:
            print(f"#{cfg['no']} 슬러 {len(res)}개 중 {len(b)}개 어긋남",
                  b[:3])
    print(f'slurs {tot}, mismatch {bad}')
