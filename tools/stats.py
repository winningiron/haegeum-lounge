# -*- coding: utf-8 -*-
"""200곡 조판 통계를 실측한다 (README·화면 안내 문구의 수치 근거).

build_piece() 가 만든 MusicXML 을 그대로 세므로 악보에 실제로 찍히는 값이다.
  - 박자 포함 곡 수(중복 포함): 곡의 sections 에 나온 박자를 하나씩 모두 센다
  - 조표별 곡 수(첫 조표) · 곡 중 조바꿈 횟수
  - 윗모르덴트(inverted-mordent) · 아랫모르덴트(mordent) · 트릴(trill-mark)
  - 트릴과 모르덴트가 같은 음에 겹친 건수
  - 슬러 개수(곡 슬러 number=1 시작점)
  - 박 묶음(5/8·7/8·12/8) 마디 수: 기본 묶음과 변형 묶음(grouping_plan)
usage: python3 tools/stats.py [곡번호 ...]
"""
import sys, os, re, collections
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scores as g
from pieces import PIECES

TAGS = {
    'upper': 'inverted-mordent',
    'lower': 'mordent',
    'trill': 'trill-mark',
}


def count(cfg):
    br = g.line_breaks(cfg)
    xml, b, mxs = g.build_piece(cfg, breaks_at=br)
    res = dict(inverted_mordent=xml.count('<inverted-mordent'),
               mordent=xml.count('<mordent '),
               trill=xml.count('<trill-mark'),
               slur=xml.count('<slur type="start"'))
    # 같은 음에 트릴과 모르덴트가 겹친 수
    both = 0
    for m in re.finditer(r'<ornaments>(.*?)</ornaments>', xml, re.S):
        body = m.group(1)
        if 'trill-mark' in body and ('inverted-mordent' in body or '<mordent ' in body):
            both += 1
    res['both'] = both
    return res


def main(only=None):
    tot = collections.Counter()
    meters = collections.Counter()
    keys = collections.Counter()
    groups = collections.Counter()      # (박자, 묶음) -> 마디 수
    group_pieces = collections.defaultdict(set)
    keych = 0
    per = []
    for cfg in PIECES:
        if only and cfg['no'] not in only:
            continue
        r = count(cfg)
        r['no'] = cfg['no']
        per.append(r)
        tot.update({k: v for k, v in r.items() if k != 'no'})
        # 박자 포함 곡 수(중복 포함) — 구간마다 한 번씩
        for _n, meter in cfg['sections']:
            meters[g.METER_LABEL[meter]] += 1
        keys[g.KEY_LABEL[cfg['key']]] += 1
        keych += len(cfg.get('key_changes') or {})
        # 박 묶음: 마디마다 실제로 쓰인 묶음
        for _m, gs in g.grouping_plan(cfg).items():
            meter = g.sections_meter(cfg['sections'], _m)
            groups[(g.METER_LABEL[meter], tuple(gs))] += 1
            group_pieces[(g.METER_LABEL[meter], tuple(gs))].add(cfg['no'])
    print('meter pieces(dup):', ' · '.join(f'{k} {meters[k]}' for k in
          ['4/4', '6/8', '5/8', '3/4', '7/8', '12/8', '9/8', '2/4']),
          '| sum', sum(meters.values()))
    print('keys:', ' · '.join(f'{k} {keys[k]}' for k in
          ['E♭', 'A♭', 'B♭', 'D♭', 'F', 'G♭', 'G', 'D']), '| key changes', keych)
    print('inverted-mordent', tot['inverted_mordent'], '· mordent', tot['mordent'],
          '· trill', tot['trill'], '· both', tot['both'], '· slur', tot['slur'])
    bad = [p for p in per if p['both']]
    if bad:
        print('same-note trill+mordent:', len(bad), 'pieces', [p['no'] for p in bad][:40])
    if groups:
        print('mixed groupings (변형 박 묶음):',
              ' · '.join(f"{m} {'+'.join(map(str, gs))} {groups[(m, gs)]}마디/{len(group_pieces[(m, gs)])}곡"
                        for (m, gs) in sorted(groups, key=lambda k: (k[0], k[1]))))


if __name__ == '__main__':
    main([int(x) for x in sys.argv[1:]] or None)
