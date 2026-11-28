# -*- coding: utf-8 -*-
"""박 묶음(beat grouping) 검증 — 악보의 빔·리듬 분할·슬러 시작·타임라인이
그 마디의 8분음표 묶음과 정확히 맞는지 200곡 전수 확인한다.

검사 항목 (마디마다)
  1) 음표·쉼표 길이 합 = 박자 총합 (4/4=48 … 12/8=72)
  2) 그룹 경계를 가로지르는 음이 없다 (2+3 묶음이면 2/8 지점에서 반드시 끊긴다)
  3) 1겹 빔 묶음이 그룹 경계를 넘지 않는다 (빔 하나 = 그룹 안쪽)
  4) 곡 슬러는 그룹 첫 음(빔 묶음의 첫 음)에서만 시작한다
  5) 타임라인 data/tl/NNN.json 의 bar.b(박 시작) = 그룹 경계,
     bar.g = 그룹 배열 (5/8·7/8·12/8·6/8·9/8 전 마디)

usage: python3 tools/check_grouping.py [곡번호 ...]
"""
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scores as g
from pieces import PIECES

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_piece(cfg, use_timeline=True):
    xml, b, mxs = g.build_piece(cfg, breaks_at=g.line_breaks(cfg))
    tl = None
    path = os.path.join(REPO, 'data', 'tl', f"{cfg['no']:03d}.json")
    if use_timeline and os.path.exists(path):
        tl = json.load(open(path, encoding='utf-8'))
    bad = []
    used = {}                                  # (레벨, 박자, 묶음) -> 마디 수
    for mx in mxs:
        meter, groups = mx['meter'], mx.get('groups')
        bounds = g.beat_bounds(meter, groups)
        want = g.METER_TOTAL[meter]
        starts, t = [], 0
        for it in mx['items']:
            if it.get('grace'):
                starts.append(None)
                continue
            starts.append(t)
            t += it['dur']
        if t != want:
            bad.append(f"m{mx['number']} 길이 {t} != {want}")
        # 2) 그룹 경계를 가로지르는 음 — 8분음표 묶음이 있는 박자만 해당한다
        #    (4/4·3/4·2/4 는 2분음표가 박을 넘는 것이 정상이므로 검사하지 않는다)
        if meter in g.DEFAULT_GROUPS:
            for i, st in enumerate(starts):
                if st is None:
                    continue
                end = st + mx['items'][i]['dur']
                if any(st < x < end for x in bounds[1:-1]):
                    bad.append(f"m{mx['number']} 음이 그룹 경계를 넘음 ({st}+{mx['items'][i]['dur']})")
        # 3) 빔 묶음이 그룹 경계를 넘는지
        beam_start = None
        for i, st in enumerate(starts):
            if st is None:
                continue
            tags = [v for n, v in (mx['items'][i].get('beams') or []) if n == 1]
            if 'begin' in tags:
                beam_start = st
            if 'end' in tags and beam_start is not None:
                end = st + mx['items'][i]['dur']
                if any(beam_start < x < end for x in bounds[1:-1]):
                    bad.append(f"m{mx['number']} 빔이 그룹 경계를 넘음 ({beam_start}~{end})")
                beam_start = None
        # 4) 슬러 시작 자리
        for i, it in enumerate(mx['items']):
            if it.get('grace') or 'start' not in (it.get('slur') or []):
                continue
            if starts[i] not in bounds[:-1]:
                bad.append(f"m{mx['number']} 슬러가 그룹 첫 음이 아닌 곳에서 시작 ({starts[i]})")
                continue
            tags = [v for n, v in (it.get('beams') or []) if n == 1]
            if 'continue' in tags or 'end' in tags:
                bad.append(f"m{mx['number']} 슬러가 빔 중간에서 시작 ({starts[i]})")
        if groups:
            used[(cfg['level'], meter, tuple(groups))] = used.get((cfg['level'], meter, tuple(groups)), 0) + 1
        else:
            key = (cfg['level'], meter, g.DEFAULT_GROUPS.get(meter))
            used[key] = used.get(key, 0) + 1
        # 5) 타임라인 대조
        if tl:
            bar = tl['bars'][mx['number'] - 1]
            if bar['b'] != bounds[:-1]:
                bad.append(f"m{mx['number']} 타임라인 박 {bar['b']} != {bounds[:-1]}")
            gs = bar.get('g')
            want_g = list(groups) if groups else (list(g.DEFAULT_GROUPS[meter])
                                                 if meter in g.DEFAULT_GROUPS else None)
            if gs != want_g:
                bad.append(f"m{mx['number']} 타임라인 g {gs} != {want_g}")
    return bad, used


def main(only=None):
    bad_total = 0
    used = {}
    for cfg in PIECES:
        if only and cfg['no'] not in only:
            continue
        bad, u = check_piece(cfg)
        for k, v in u.items():
            used[k] = used.get(k, 0) + v
        if bad:
            bad_total += len(bad)
            print(f"#{cfg['no']} 묶음 위반 {len(bad)}건", bad[:4])
    print('--- 변형 묶음 사용 (레벨 · 박자 · 묶음 : 마디 수) ---')
    for (lv, meter, gs), n in sorted(used.items(), key=lambda x: (x[0][1], x[0][2] or ())):
        tag = '기본' if gs == g.DEFAULT_GROUPS.get(meter) else '변형'
        print(f"  {lv} {g.METER_LABEL[meter]:5s} {'+'.join(map(str, gs)) if gs else '-':12s} {tag}  {n}마디")
    print(f'grouping violations {bad_total}')
    return 1 if bad_total else 0


if __name__ == '__main__':
    sys.exit(main([int(x) for x in sys.argv[1:]] or None))
