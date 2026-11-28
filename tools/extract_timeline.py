#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""70곡의 연주 타임라인 + 악보 마디 좌표를 data/tl/*.json 으로 뽑는다.

음표·쉼표·붙임줄(tie)·장식음(grace)·템포·박자는 tools/gen_scores.py 의 build_piece()
결과(마디별 items)에서 그대로 가져온다. 악보 PNG/PDF 는 읽기만 하고 덮어쓰지 않는다.

마디 좌표:
  1) 배포된 scores/NNN.png 에서 오선 5줄을 찾아 7단의 위/아래(y)와 그 줄의 왼·오른 끝(x)을 잰다.
  2) 조판에 쓴 SVG(tools/gen_scores.py 와 같은 경로로 다시 만든 것 — PNG 와 픽셀 단위로 같다)에서
     단 안의 마디별 가로 위치를 문서 단위로 얻는다.
  3) 단마다 1)의 왼·오른 끝에 맞춰 선형으로 환산한다 (세로는 오선 위치를 그대로 사용).
결과는 이미지 크기로 나눈 비율(fx, fy, fw, fh)이라 화면 배율과 무관하다.
"""
import os, sys, json, re
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scores as g
from pieces import PIECES

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'data', 'tl')
NS = '{http://www.w3.org/2000/svg}'
TICKS_PER_QUARTER = 12
COMPOUND = ((6, 8), (9, 8), (12, 8))


# ------------------------------------------------------------------ SVG
def svg_systems(cfg):
    """마디별 (x0, x1) 문서 단위 + 오선 y. render() 안의 SVG 생성 부분과 같은 경로."""
    br = g.line_breaks(cfg)
    total = g.piece_total(cfg)
    xml, builder, mxs = g.build_piece(cfg, breaks_at=br)
    import verovio
    tk = verovio.toolkit()
    opts = dict(g.LAYOUT)
    opts.update(dict(breaks='encoded'))
    tk.setOptions(opts)
    tk.loadData(xml)
    svg = tk.renderToSVG(1)
    if svg.count('class="measure"') != total:
        raise RuntimeError(f"#{cfg['no']}: 마디 수 불일치")
    svg = g.spread_systems(svg, opts['pageHeight'])
    svg = re.sub(r'<rect class="page-margin"[^>]*/>', '', svg)

    root = ET.fromstring(svg)
    ds = [c for c in root if c.attrib.get('class') == 'definition-scale'][0]
    pm = [c for c in ds.iter(NS + 'g') if c.attrib.get('class') == 'page-margin'][0]
    out = []
    for sysg in [c for c in pm.iter(NS + 'g') if c.attrib.get('class') == 'system']:
        measures, ys = [], []
        for m in [c for c in sysg.iter(NS + 'g') if c.attrib.get('class') == 'measure']:
            xs, yv = [], []
            for st in [c for c in m if c.attrib.get('class') == 'staff']:
                for p in st.iter(NS + 'path'):
                    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', p.attrib.get('d', ''))]
                    if len(nums) >= 4:
                        xs.extend([nums[0], nums[2]])
                        yv.extend([nums[1], nums[3]])
            if xs:
                measures.append((min(xs), max(xs)))
                ys.extend(yv)
        # 마디줄 폭(2~10단위)이 겹치지 않게 이어 붙인다
        for i in range(len(measures) - 1):
            a = measures[i]
            b = measures[i + 1]
            if b[0] < a[1] - 20:
                measures[i] = (a[0], max(a[1], b[0]))
        out.append(dict(measures=measures, y0=min(ys), y1=max(ys)))
    return out, mxs, total


# ------------------------------------------------------------------ PNG
def staff_rows(dark):
    h, w = dark.shape
    runs = []
    for y in range(h):
        row = dark[y]
        idx = np.flatnonzero(np.diff(np.concatenate(([0], row.view(np.int8), [0]))))
        best = (idx[1::2] - idx[0::2]).max() if len(idx) else 0
        if best > w * 0.55:
            if runs and y - runs[-1] <= 2:
                continue
            runs.append(y)
    systems, cur = [], []
    for y in runs:
        if cur and y - cur[-1] > 26:
            systems.append(cur)
            cur = []
        cur.append(y)
    if cur:
        systems.append(cur)
    out = []
    for s in systems:
        if len(s) >= 5:
            out.append((s[0], s[4]))
        elif len(s) == 4:
            out.append((s[0], s[0] + 48))
    return out


def png_systems(no):
    im = Image.open(os.path.join(REPO, 'scores', f'{no:03d}.png')).convert('L')
    W, H = im.size
    dark = np.array(im) < 160
    rows = staff_rows(dark)
    if len(rows) != 7:
        raise RuntimeError(f'#{no}: 단 {len(rows)}개 (7개여야)')
    out = []
    for (y0, y1) in rows:
        xs = np.flatnonzero(dark[y0])
        out.append(dict(y0=int(y0), y1=int(y1), x0=int(xs[0]), x1=int(xs[-1])))
    return out, W, H


def measure_boxes(cfg, svg_sys, png_sys, W, H, expect):
    boxes, sysinfo = [], []
    if len(svg_sys) != len(png_sys) != 7:
        raise RuntimeError(f"#{cfg['no']}: 단 수 불일치")
    for si, (sv, pn) in enumerate(zip(svg_sys, png_sys)):
        ms = sv['measures']
        if len(ms) != expect[si]:
            raise RuntimeError(f"#{cfg['no']}: {si + 1}단 마디 {len(ms)}개 (계획 {expect[si]})")
        d0, d1 = ms[0][0], ms[-1][1]
        scale = (pn['x1'] - pn['x0']) / (d1 - d0)
        pad_top, pad_bot = 9, 10
        sysinfo.append(dict(y0=pn['y0'] - pad_top, y1=pn['y1'] + pad_bot))
        for (a, b) in ms:
            x0 = pn['x0'] + (a - d0) * scale
            x1 = pn['x0'] + (b - d0) * scale
            boxes.append(dict(s=si,
                              x=x0 / W, w=(x1 - x0) / W,
                              y=(pn['y0'] - pad_top) / H,
                              h=(pn['y1'] + pad_bot - pn['y0'] + pad_top) / H))
    return boxes, sysinfo


# ------------------------------------------------------------------ 타임라인
def midi_of(p):
    return 12 * (p[1] + 1) + g.LETTER_SEMI[p[0]] + p[2]


def build_timeline(cfg, total, mxs, boxes, systems, page_h):
    tempos = cfg['tempos']
    cur_bpm = None
    t = 0.0
    bars, notes = [], []
    pending = None
    if len(boxes) != total:
        raise RuntimeError(f"#{cfg['no']}: 좌표 {len(boxes)} != 마디 {total}")

    for i, mx in enumerate(mxs):
        n = mx['number']
        meter = mx['meter']
        if n in tempos:
            cur_bpm = tempos[n]
        qpm = cur_bpm * (1.5 if meter in COMPOUND else 1.0)
        sec_per_tick = 60.0 / (qpm * TICKS_PER_QUARTER)
        quarters = meter[0] * 4.0 / meter[1]
        dur = quarters * 60.0 / qpm

        box = boxes[i]
        bars.append(dict(n=n, t=round(t, 4), d=round(dur, 4), q=round(qpm, 3),
                         b=g.beat_bounds(meter)[:-1], s=box['s'],
                         x=round(box['x'], 5), y=round(box['y'], 5),
                         w=round(box['w'], 5), h=round(box['h'], 5)))

        pos, tick = [], 0
        for it in mx['items']:
            pos.append((tick, it))
            tick += it['dur'] or 0

        # 장식음 묶음: 본음 박 직전에 짧게 선행 타격 (본음 박은 그대로)
        gi = 0
        while gi < len(pos):
            off, it = pos[gi]
            if not it.get('grace'):
                gi += 1
                continue
            gj = gi
            group = []
            while gj < len(pos) and pos[gj][1].get('grace'):
                group.append(pos[gj][1])
                gj += 1
            main = pos[gj][1] if gj < len(pos) else None
            main_off = pos[gj][0] if gj < len(pos) else off
            if main is not None and not main.get('rest'):
                lead = min(0.085, 0.22 * ((main.get('dur') or 12) * sec_per_tick))
                for k, gr in enumerate(group):
                    tt = max(0.0, t + main_off * sec_per_tick - lead * (len(group) - k))
                    notes.append(dict(t=int(round(tt * 1000)), d=int(round(lead * 1000)),
                                      midi=midi_of(gr['pitch']), m=n, v=1, last=n))
            gi = gj

        for off, it in pos:
            if it.get('grace') or it['rest']:
                continue
            pitch = midi_of(it['pitch'])
            dur_t = it['dur'] * sec_per_tick
            tie = it.get('tie') or []
            if 'stop' in tie and pending is not None and pending['midi'] == pitch:
                pending['d'] += dur_t          # 마디줄을 넘는 붙임줄: 길이만 이어 붙인다
                pending['last'] = n
                if 'start' not in tie:
                    notes.append(pending)
                    pending = None
                continue
            rec = dict(t=int(round((t + off * sec_per_tick) * 1000)),
                       d=int(round(dur_t * 1000)), midi=pitch, m=n,
                       v=3 if off == 0 else 2, last=n)
            if 'start' in tie:
                pending = rec                  # 마디 루프 밖에서 유지
            else:
                notes.append(rec)
                pending = None

        t += dur

    if pending is not None:
        notes.append(pending)
    notes.sort(key=lambda r: (r['t'], -r['d']))

    return dict(
        no=cfg['no'], level=cfg['level'], title=cfg['title'],
        key=g.KEY_LABEL[cfg['key']], meters=[g.METER_LABEL[mm] for _, mm in cfg['sections']],
        bpm=tempos[min(tempos)], total=total, dur=round(t, 3),
        systems=[dict(y0=round(s['y0'] / page_h, 5), y1=round(s['y1'] / page_h, 5))
                 for s in systems],
        bars=bars, notes=[[r['t'], r['d'], r['midi'], r['m'], r['v'], r['last']] for r in notes],
    )


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    t0 = __import__('time').time()
    fails = []
    for cfg in PIECES:
        if only and cfg['no'] not in only:
            continue
        br = g.line_breaks(cfg)
        total = g.piece_total(cfg)
        expect = g.line_counts(br, total)
        svg_sys, mxs, total = svg_systems(cfg)
        try:
            png_sys, W, H = png_systems(cfg['no'])
            boxes, systems = measure_boxes(cfg, svg_sys, png_sys, W, H, expect)
        except RuntimeError as e:
            fails.append(str(e))
            print('FAIL', e)
            continue
        tl = build_timeline(cfg, total, mxs, boxes, systems, H)
        path = os.path.join(OUT, f"{cfg['no']:03d}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(tl, f, ensure_ascii=False, separators=(',', ':'))
        assert len(tl['bars']) == total
        assert all(0 <= b['x'] <= 1 and 0 <= b['y'] <= 1 for b in tl['bars'])
        assert all(b['w'] > 0 and b['h'] > 0 for b in tl['bars'])
        print(f"#{cfg['no']:3d} {cfg['level']:2s} {total:2d}마디 {len(tl['notes']):3d}음 "
              f"{tl['dur']:6.1f}s {os.path.getsize(path)//1024}KB")
    print('elapsed', round(__import__('time').time() - t0, 1), 's', 'fails', len(fails))


if __name__ == '__main__':
    main([int(x) for x in sys.argv[1:]] or None)
