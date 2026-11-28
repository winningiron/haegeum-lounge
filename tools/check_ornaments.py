# -*- coding: utf-8 -*-
"""꾸밈표 검증 — 모르덴트 방향과 트릴·모르덴트 겹침을 MusicXML 에서 직접 확인한다.

`tools/gen_scores.py` 가 만든 MusicXML 을 곡마다 다시 읽어,
  1) 윗모르덴트(inverted-mordent)는 앞 음이 같거나 낮은 자리,
     아랫모르덴트(mordent)는 앞 음이 높은 자리에서만 쓰였는지 (앞 음이 없으면 윗모르덴트)
  2) 한 음에 트릴과 모르덴트가 함께 붙지 않았는지
를 센다. 앞 음은 같은 마디 안에서 쉼표·장식음을 건너뛴 직전 음표다.

usage: python3 tools/check_ornaments.py [곡번호 ...]
"""
import sys, os
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scores as g
from pieces import PIECES

DIA = g.DIA


def step_of(step, octave):
    return int(octave) * 7 + DIA[step]


def scan(cfg):
    xml, _b, _mxs = g.build_piece(cfg, breaks_at=g.line_breaks(cfg))
    root = ET.fromstring(xml)
    # 기초 후반(mordent_measures)은 윗·아랫모르덴트를 일부러 번갈아 넣어 두 모양을 익히므로
    # 앞 음 방향 규칙을 적용하지 않고 개수만 센다.
    melodic_rule = not cfg.get('mordent_measures')
    upper = lower = trill = bad_dir = both = 0
    for meas in root.iter('measure'):
        prev = None
        for note in meas.findall('note'):
            if note.find('rest') is not None:
                continue
            pitch = note.find('pitch')
            step = step_of(pitch.find('step').text, pitch.find('octave').text)
            grace = note.find('grace') is not None
            orn = note.find('notations/ornaments')
            if orn is not None:
                has_up = orn.find('inverted-mordent') is not None
                has_low = orn.find('mordent') is not None
                has_trill = orn.find('trill-mark') is not None
                trill += has_trill
                upper += has_up
                lower += has_low
                if has_trill and (has_up or has_low):
                    both += 1
                if melodic_rule:
                    if has_low and (prev is None or prev <= step):
                        bad_dir += 1
                    if has_up and prev is not None and prev > step:
                        bad_dir += 1
            if not grace:
                prev = step
    return dict(upper=upper, lower=lower, trill=trill, bad=bad_dir, both=both)


def main(only=None):
    tot = dict(upper=0, lower=0, trill=0, bad=0, both=0)
    for cfg in PIECES:
        if only and cfg['no'] not in only:
            continue
        r = scan(cfg)
        for k in tot:
            tot[k] += r[k]
        if r['bad'] or r['both']:
            print(f"#{cfg['no']}: 방향 어긋남 {r['bad']} · 겹침 {r['both']}")
    print(f"윗모르덴트 {tot['upper']} · 아랫모르덴트 {tot['lower']} · 트릴 {tot['trill']} "
          f"· 방향 어긋남 {tot['bad']} · 트릴+모르덴트 겹침 {tot['both']}")


if __name__ == '__main__':
    main([int(x) for x in sys.argv[1:]] or None)
