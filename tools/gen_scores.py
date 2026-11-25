#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
해금 초견 웹 라운지 - 시범 30곡 악보 생성기
Verovio(Leland) + resvg_py + PyMuPDF, work/make_haegeum_v6_sample42.py 의 조판 규칙을 그대로 따른다.
"""
import os, io, re, json, random, sys
import xml.etree.ElementTree as ET

import verovio, resvg_py, fitz
from PIL import Image, ImageDraw, ImageFont

DIV = 12
FONT_KR = "/usr/share/fonts/pickle-hwp/NotoSansCJKkr-Regular.otf"

# ----------------------------------------------------------------------------
# 기본 자료
# ----------------------------------------------------------------------------
LETTER_SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
IDX_LETTER = 'CDEFGAB'
FLAT_ORDER = 'BEADGCF'
SHARP_ORDER = 'FCGDAEB'

KEY_FIFTHS = {'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5}
KEY_LABEL = {'F': 'F', 'Bb': 'B♭', 'Eb': 'E♭', 'Ab': 'A♭', 'Db': 'D♭'}


def key_alters(fifths):
    d = {c: 0 for c in 'CDEFGAB'}
    if fifths < 0:
        for c in FLAT_ORDER[:-fifths]:
            d[c] = -1
    elif fifths > 0:
        for c in SHARP_ORDER[:fifths]:
            d[c] = 1
    return d


def midi_of(letter, octv, alter):
    return 12 * (octv + 1) + LETTER_SEMI[letter] + alter


LOW_MIDI, HIGH_MIDI = 57, 84          # A3 ~ C6


def tonic_pc(fifths):
    return (7 * fifths) % 12


# ----------------------------------------------------------------------------
# 리듬 어휘
# ----------------------------------------------------------------------------
BASIS = {
    'w':  dict(dur=48, ntype='whole'),
    'dh': dict(dur=36, ntype='half', dot=True),
    'h':  dict(dur=24, ntype='half'),
    'dq': dict(dur=18, ntype='quarter', dot=True),
    'q':  dict(dur=12, ntype='quarter'),
    'de': dict(dur=9, ntype='eighth', dot=True),
    'e':  dict(dur=6, ntype='eighth'),
    's':  dict(dur=3, ntype='16th'),
    'te': dict(dur=4, ntype='eighth', tuplet=True),
    'tq': dict(dur=8, ntype='quarter', tuplet=True),
    'rq': dict(dur=12, ntype='quarter', rest=True),
    'rh': dict(dur=24, ntype='half', rest=True),
    'rdq': dict(dur=18, ntype='quarter', rest=True, dot=True),
    're': dict(dur=6, ntype='eighth', rest=True),
    'rs': dict(dur=3, ntype='16th', rest=True),
}

METER_TOTAL = {(4, 4): 48, (3, 4): 36, (2, 4): 24,
               (12, 8): 72, (9, 8): 54, (6, 8): 36,
               (5, 8): 30, (7, 8): 42}
METER_LABEL = {(4, 4): '4/4', (3, 4): '3/4', (2, 4): '2/4',
               (12, 8): '12/8', (9, 8): '9/8', (6, 8): '6/8',
               (5, 8): '5/8', (7, 8): '7/8'}


def tokens(txt):
    return txt.split()


def expand(txt):
    """패턴 문자열 -> 리듬 아이템 목록 (피치 없음)."""
    items = []
    tup_run = []
    for tk in tokens(txt):
        b = dict(BASIS[tk])
        it = dict(dur=b['dur'], ntype=b['ntype'], dot=b.get('dot', False),
                  rest=b.get('rest', False), tuplet_base=b.get('tuplet', False))
        items.append(it)
        if it['tuplet_base']:
            tup_run.append(it)
        else:
            tup_run = []
        # tuplet 그룹 마감: 다음 토큰이 없거나 튜플이 아니면
    # tuplet 표시 부여
    i = 0
    while i < len(items):
        if items[i]['tuplet_base']:
            j = i
            while j + 1 < len(items) and items[j + 1]['tuplet_base']:
                j += 1
            for k in range(i, j + 1):
                items[k]['tuplet'] = 'start' if k == i else ('stop' if k == j else 'mid')
            i = j + 1
        else:
            i += 1
    total = sum(it['dur'] for it in items)
    return items, total


# 패턴 풀: (패턴, 태그)
POOLS = {
    (4, 4): [
        ("q q q q", ""),
        ("e e q q q", ""),
        ("e e q e e q", ""),
        ("q de s q q", "dot16"),
        ("de s e e q q", "dot16"),
        ("q rq q q", "rest_mid"),
        ("q rs s e q q", "rest_mid"),
        ("s s s s e e q q", "run"),
        ("e e e e e e e e", "run"),
        ("q e e e e q", ""),
        ("h q q", "long"),
        ("e e q h", "long"),
        ("q q e e q", ""),
        ("e re q q q", "rest_mid"),
        ("e s s q e e q", ""),
        ("tq tq tq q q", "trip"),
        ("q te te te q q", "trip"),
        ("q q te te te q", "trip"),
        ("rq q e e q", "rest_start"),
    ],
    (3, 4): [
        ("q q q", ""),
        ("e e q q", ""),
        ("q e e q", ""),
        ("de s q q", "dot16"),
        ("q rq q", "rest_mid"),
        ("e re q q", "rest_mid"),
        ("h q", "long"),
        ("q h", "long"),
        ("s s s s e e q", "run"),
        ("e e e e q", "run"),
        ("te te te q q", "trip"),
        ("q te te te q", "trip"),
        ("q de s q", "dot16"),
        ("e e e e e e", "run"),
        ("rq q q", "rest_start"),
        ("e e q rq", "rest_mid"),
    ],
    (2, 4): [
        ("q q", ""),
        ("e e q", ""),
        ("q e e", ""),
        ("de s q", "dot16"),
        ("s s s s q", "run"),
        ("e e e e", "run"),
        ("rq q", "rest_start"),
        ("e re q", "rest_mid"),
        ("te te te q", "trip"),
        ("rs s e q", "rest_mid"),
        ("q rq", "rest_mid"),
    ],
    (12, 8): [
        ("dq dq dq dq", ""),
        ("q e q e q e q e", ""),
        ("e e e e e e e e e e e e", "run"),
        ("dq e e e dq dq", ""),
        ("q e e e e dq dq", ""),
        ("dq re e e dq dq", "rest_mid"),
        ("de s e dq dq dq", "dot16"),
        ("dq rq e dq dq", "rest_mid"),
        ("e e e q e dq dq", ""),
    ],
    (6, 8): [
        ("dq dq", ""),
        ("q e q e", ""),
        ("e e e e e e", "run"),
        ("q e e e e", ""),
        ("e e e q e", ""),
        ("de s e dq", "dot16"),
        ("dq re e e", "rest_mid"),
        ("q re e e e", "rest_mid"),
        ("e re e dq", "rest_mid"),
        ("dq e re e", "rest_mid"),
        ("q e dq", ""),
        ("q e e e e", ""),
    ],
    (9, 8): [
        ("dq dq dq", ""),
        ("q e q e q e", ""),
        ("e e e e e e e e e", "run"),
        ("de s e dq dq", "dot16"),
        ("dq rq e dq", "rest_mid"),
        ("dq e re e dq", "rest_mid"),
        ("e e e e e e dq", ""),
        ("dq dq q e", ""),
        ("q e dq dq", ""),
        ("q e q e dq", ""),
    ],
    (5, 8): [
        ("dq q", ""),
        ("q dq", ""),
        ("e e e q", ""),
        ("q e e e", ""),
        ("e e e e e", "run"),
        ("de s e q", "dot16"),
        ("de s dq", "dot16"),
        ("rq dq", "rest_start"),
    ],
    (7, 8): [
        ("dq q q", ""),
        ("q q dq", ""),
        ("e e e q q", ""),
        ("q q e e e", ""),
        ("e e e e e e e", "run"),
        ("de s e q q", "dot16"),
        ("q de s dq", "dot16"),
        ("q rq dq", "rest_mid"),
        ("dq rq q", "rest_mid"),
    ],
}

for _meter, _pool in POOLS.items():
    for _txt, _tag in _pool:
        _items, _tot = expand(_txt)
        assert _tot == METER_TOTAL[_meter], (_meter, _txt, _tot)

CADENCE = {(4, 4): "q q h", (3, 4): "q h", (2, 4): "q q",
           (12, 8): "dq dq dq dq", (9, 8): "dq dq dq",
           (6, 8): "dq dq", (5, 8): "dq q", (7, 8): "dq q q"}


def beat_bounds(meter):
    b, bt = meter
    if bt == 4:
        return [i * 12 for i in range(b + 1)]
    if bt == 8:
        if b % 3 == 0 and b >= 6:
            return [i * 18 for i in range(b // 3 + 1)]
        if b == 5:
            return [0, 18, 30]
        if b == 7:
            return [0, 18, 30, 42]
    raise ValueError(meter)


# ----------------------------------------------------------------------------
# MusicXML 직렬화
# ----------------------------------------------------------------------------
def note_xml(p, dur, ntype, dot=False, rest=False, beams=None, slurs=None, ties=None,
             acc=None, mordent=False, trill=False, stacc=False, accent=False,
             tenuto=False, grace=False, grace_slash=True, tuplet=None, fermata=False):
    out = ["      <note>"]
    if grace:
        out.append('        <grace slash="yes"/>' if grace_slash else '        <grace/>')
    if rest:
        out.append("        <rest/>")
    else:
        letter, octv, alter = p
        out.append("        <pitch>")
        out.append(f"          <step>{letter}</step>")
        if alter != 0:
            out.append(f"          <alter>{alter}</alter>")
        out.append(f"          <octave>{octv}</octave>")
        out.append("        </pitch>")
    if not grace:
        out.append(f"        <duration>{dur}</duration>")
    if ties:
        for t in ties:
            out.append(f'        <tie type="{t}"/>')
    out.append(f"        <type>{ntype}</type>")
    if dot:
        out.append("        <dot/>")
    if acc:
        out.append(f"        <accidental>{acc}</accidental>")
    if tuplet:
        out.append("        <time-modification><actual-notes>3</actual-notes>"
                   "<normal-notes>2</normal-notes></time-modification>")
    if beams:
        for num, val in beams:
            out.append(f'        <beam number="{num}">{val}</beam>')
    nots = []
    if ties:
        for t in ties:
            nots.append(f'          <tied type="{t}"/>')
    if slurs:
        for typ, num in slurs:
            nots.append(f'          <slur type="{typ}" placement="above" number="{num}"/>')
    if tuplet in ('start', 'stop'):
        nots.append(f'          <tuplet type="{tuplet}"/>')
    arts = []
    if stacc:
        arts.append("            <staccato/>")
    if accent:
        arts.append("            <accent/>")
    if tenuto:
        arts.append("            <tenuto/>")
    if arts:
        nots.append("          <articulations>\n" + "\n".join(arts) + "\n          </articulations>")
    if fermata:
        nots.append("          <fermata/>")
    orns = []
    if mordent:
        orns.append("<inverted-mordent/>")
    if trill:
        orns.append("<trill-mark/>")
    if orns:
        nots.append("          <ornaments>" + "".join(orns) + "</ornaments>")
    if nots:
        out.append("        <notations>\n" + "\n".join(nots) + "\n        </notations>")
    out.append("      </note>")
    return "\n".join(out)


def dyn(d):
    return (f'      <direction placement="below"><direction-type><dynamics><{d}/>'
            f'</dynamics></direction-type></direction>')


def words_below(w, italic=True):
    st = ' font-style="italic"' if italic else ''
    return (f'      <direction placement="below"><direction-type>'
            f'<words{st} font-size="9">{w}</words></direction-type></direction>')


def tempo_xml(unit, bpm):
    sym = "♩." if unit == "dotted-quarter" else "♩"
    return (f'      <direction placement="above"><direction-type>'
            f'<words font-family="Noto Sans CJK KR, DejaVu Sans, sans-serif" '
            f'font-size="11" font-weight="bold">{sym} = {bpm}</words>'
            f'</direction-type></direction>')


def wedge(w):
    return (f'      <direction placement="below"><direction-type>'
            f'<wedge type="{w}"/></direction-type></direction>')


# ----------------------------------------------------------------------------
# 선율 엔진
# ----------------------------------------------------------------------------
class Melody:
    def __init__(self, fifths, level, rng):
        self.fifths = fifths
        self.alters = key_alters(fifths)
        self.level = level
        self.rng = rng
        self.dpos = 33          # A4 부근
        self.last_dir = 0
        self.same_dir = 0
        self.last_interval = 0
        self.tpc = tonic_pc(fifths)
        self.chord_pcs = [(self.tpc + x) % 12 for x in (0, 4, 7)]
        self.dom_pcs = [(self.tpc + 7 + x) % 12 for x in (0, 4, 7)]

    def pitch_of(self, dpos):
        letter = IDX_LETTER[dpos % 7]
        octv = dpos // 7
        return (letter, octv, self.alters[letter])

    def midi(self, dpos):
        p = self.pitch_of(dpos)
        return midi_of(*p)

    def in_range(self, dpos):
        return LOW_MIDI <= self.midi(dpos) <= HIGH_MIDI

    def choose_interval(self):
        r = self.rng
        lv = self.level
        if lv == '기초':
            table = [(1, 0.42), (2, 0.30), (3, 0.18), (4, 0.10)]
        elif lv == '중급':
            table = [(1, 0.34), (2, 0.26), (3, 0.20), (4, 0.12), (5, 0.08)]
        else:
            table = [(1, 0.24), (2, 0.20), (3, 0.20), (4, 0.16), (5, 0.10), (6, 0.06), (7, 0.04)]
        x = r.random()
        acc = 0
        for span, w in table:
            acc += w
            if x <= acc:
                return span
        return table[-1][0]

    def next_pitch(self, force_dir=None, chord_end=False, fast=False):
        r = self.rng
        span = self.choose_interval()
        # 방향
        if force_dir is not None:
            d = force_dir
        else:
            if self.level == '고급':
                p_rev = 0.46
                if self.same_dir >= 2:
                    p_rev = 0.8
                d = -self.last_dir if (self.last_dir and r.random() < p_rev) else (self.last_dir or r.choice([-1, 1]))
                if not self.last_dir:
                    d = r.choice([-1, 1])
            elif self.level == '중급':
                p_rev = 0.38
                if self.same_dir >= 3:
                    p_rev = 0.85
                d = -self.last_dir if (self.last_dir and r.random() < p_rev) else (self.last_dir or r.choice([-1, 1]))
                if not self.last_dir:
                    d = r.choice([-1, 1])
            else:
                p_rev = 0.34
                if self.same_dir >= 3:
                    p_rev = 0.9
                d = -self.last_dir if (self.last_dir and r.random() < p_rev) else (self.last_dir or 1)
                if not self.last_dir:
                    d = 1
        # 큰 도약 뒤 반대방향 순차 (기초/중급)
        if self.level != '고급' and abs(self.last_interval) >= 4 and self.last_dir:
            if r.random() < 0.75:
                d, span = -self.last_dir, r.choice([1, 2])
        # 음역 중앙으로 회귀 (A4 부근)
        if self.dpos >= 37:
            d = -1 if r.random() < 0.55 else d
        elif self.dpos <= 30:
            d = 1 if r.random() < 0.55 else d
        elif r.random() < 0.15:
            d = 1 if self.dpos < 33 else -1
        cand = self.dpos + d * span
        # 음역 밖이면 반사
        tries = 0
        while not self.in_range(cand) and tries < 6:
            d = -d
            cand = self.dpos + d * span
            tries += 1
        if not self.in_range(cand):
            cand = self.dpos + (1 if self.dpos < 33 else -1)
        if chord_end:
            cand = self.snap_chord(cand)
        # 같은 음 반복 최소화
        if cand == self.dpos and r.random() < 0.9:
            cand = cand + (1 if d > 0 else -1)
            if not self.in_range(cand):
                cand = self.dpos - (1 if d > 0 else -1)
        if cand != self.dpos:
            nd = 1 if cand > self.dpos else -1
            if nd == self.last_dir:
                self.same_dir += 1
            else:
                self.same_dir = 1
            self.last_dir = nd
            self.last_interval = abs(cand - self.dpos)
        self.dpos = cand
        return cand

    def snap_chord(self, dpos):
        pcs = self.chord_pcs if self.rng.random() < 0.7 else self.dom_pcs
        for delta in (0, 1, -1, 2, -2):
            c = dpos + delta
            if self.in_range(c):
                p = self.pitch_of(c)
                if midi_of(*p) % 12 in pcs:
                    return c
        return dpos

    def phrase_start(self):
        r = self.rng
        target = r.choice([31, 32, 33, 34, 35, 36])
        if self.in_range(target):
            self.dpos = target
        self.last_dir = 0
        self.same_dir = 0
        self.last_interval = 0

    def tonic_near(self):
        # 토닉 음 중 현재 위치에서 가장 가까운 것
        best = None
        for c in range(LOW_MIDI, HIGH_MIDI + 1):
            # dpos 로 변환
            pass
        for dpos in range(26, 43):
            if not self.in_range(dpos):
                continue
            p = self.pitch_of(dpos)
            if midi_of(*p) % 12 == self.tpc:
                if best is None or abs(dpos - self.dpos) < abs(best - self.dpos):
                    best = dpos
        return best if best is not None else self.dpos


# ----------------------------------------------------------------------------
# 한 곡 조성
# ----------------------------------------------------------------------------
class PieceBuilder:
    def __init__(self, cfg):
        self.cfg = cfg
        self.rng = random.Random(cfg['seed'])
        self.fifths = KEY_FIFTHS[cfg['key']]
        self.mel = Melody(self.fifths, cfg['level'], self.rng)
        self.measures = []
        self.features = set()
        self.prev_pattern = None
        self.pending_tie = None
        self.tie_src = None
        self.last_dyn = None
        self.wedge_open = False

    # --- 리듬 선택 -------------------------------------------------------
    def pick_pattern(self, meter, pref_tags, cadence=False):
        if cadence:
            return CADENCE[meter]
        pool = POOLS[meter]
        cands = [p for p in pool if p[1] in pref_tags]
        if not cands:
            cands = pool
        # 직전 패턴 반복 회피
        cands2 = [p for p in cands if p[0] != self.prev_pattern] or cands
        txt = self.rng.choice(cands2)[0]
        self.prev_pattern = txt
        return txt

    def tags_for(self, level, idx_in_section):
        i = idx_in_section
        if level == '기초':
            if i in (2, 6):
                return ["rest_mid"]
            if i in (1, 3, 5):
                return ["", "dot16"]
            return ["", "long"]
        if level == '중급':
            if i in (1, 5):
                return ["rest_mid"]
            if i in (2, 6):
                return ["dot16"]
            if i == 3:
                return ["trip", "run"]
            return ["", "run"]
        # 고급
        if i in (0, 2, 4, 6):
            return ["rest_mid", "rest_mid", "rest_start"]
        if i in (1, 5):
            return ["dot16"]
        if i == 3:
            return ["run", "rest_mid"]
        return ["", "dot16"]

    # --- 한 마디 ---------------------------------------------------------
    def make_measure(self, meter, pattern_txt, mnum, is_phrase_end, is_final, tie_ok_next=True):
        items, total = expand(pattern_txt)
        assert total == METER_TOTAL[meter], (meter, pattern_txt, total)
        lv = self.cfg['level']
        r = self.rng

        # --- 피치 배정 ---
        note_items = [it for it in items if not it['rest']]
        # 마디 첫 음이 이전 마디에서 타이로 이어지면 처리
        if self.pending_tie:
            first = items[0] if items else None
            if first is not None and not first['rest'] and not first.get('grace'):
                first['tie'] = ['stop']
                first['pitch'] = self.pending_tie
            elif self.tie_src is not None:
                # 쉼표로 시작하면 타이를 취소
                self.tie_src.pop('tie', None)
            self.pending_tie = None
            self.tie_src = None
        for idx_it, it in enumerate(items):
            if it['rest']:
                it['pitch'] = None
                continue
            if 'pitch' in it:
                continue
            chord_end = (is_final and it is note_items[-1]) or \
                        (is_phrase_end and it is note_items[-1])
            dpos = self.mel.next_pitch(chord_end=chord_end)
            it['dpos'] = dpos
            it['pitch'] = self.mel.pitch_of(dpos)
            it['alter'] = it['pitch'][2]

        # 마지막 음은 토닉으로 (최종 마디)
        if is_final and note_items:
            last = note_items[-1]
            self.mel.dpos = self.mel.tonic_near()
            last['dpos'] = self.mel.dpos
            last['pitch'] = self.mel.pitch_of(self.mel.dpos)

        # --- 임시표 ---
        p_chrom = {'기초': 0.03, '중급': 0.09, '고급': 0.14}[lv]
        # 조성의 으뜸음 letter
        t_pc = tonic_pc(self.fifths)
        _ka = key_alters(self.fifths)
        tonic_letter = [L for L in 'CDEFGAB' if (LETTER_SEMI[L] + _ka[L]) % 12 == t_pc][0]
        ti = IDX_LETTER.index(tonic_letter)
        deg_letters = {3: IDX_LETTER[(ti + 2) % 7], 4: IDX_LETTER[(ti + 3) % 7],
                       7: IDX_LETTER[(ti + 6) % 7], 5: IDX_LETTER[(ti + 4) % 7]}
        chrom_choices = {deg_letters[3]: -1, deg_letters[4]: +1,
                         deg_letters[7]: -1, deg_letters[5]: +1}
        accidentals = {}
        keyacc = key_alters(self.fifths)
        for it in note_items:
            letter, octv, base_alter = it['pitch']
            alt = base_alter
            if letter in chrom_choices and r.random() < p_chrom and 'stop' not in (it.get('tie') or []):
                cand_alt = base_alter + chrom_choices[letter]
                if cand_alt in (-2, -1, 0, 1) and LOW_MIDI <= midi_of(letter, octv, cand_alt) <= HIGH_MIDI:
                    alt = cand_alt
                    self.features.add('임시표')
            it['pitch'] = (letter, octv, alt)
            cur = accidentals.get((letter, octv), keyacc[letter])
            if alt != cur:
                it['acc'] = {-2: 'flat', -1: 'flat', 0: 'natural', 1: 'sharp'}[alt]
                accidentals[(letter, octv)] = alt

        # --- 장식음 ---
        self.add_graces(items, lv)

        # --- 아티큘레이션 / 꾸밈음 ---
        for it in note_items:
            if it.get('grace'):
                continue
            if lv == '기초':
                if it['ntype'] == 'eighth' and r.random() < 0.12:
                    it['stacc'] = True
            else:
                if it['ntype'] == 'eighth' and r.random() < 0.16:
                    it['stacc'] = True
                elif it['dur'] >= 12 and r.random() < 0.07:
                    it['accent'] = True
                elif it['dur'] >= 12 and r.random() < 0.06:
                    it['tenuto'] = True
            # 농현/트릴
            if it['dur'] >= 12 and not it.get('acc_note'):
                if lv in ('중급',) and r.random() < 0.16:
                    it['mordent'] = True
                    self.features.add('농현')
                elif lv == '고급' and r.random() < 0.16:
                    it['mordent'] = True
                    self.features.add('농현')
            if lv == '고급' and it['dur'] >= 18 and r.random() < 0.30:
                it['trill'] = True
                self.features.add('트릴')

        # --- 슬러 ---
        self.add_slurs(items, lv)

        # --- 마디 사이 타이 ---
        if not self.cfg.get('no_tie') and note_items and not is_final and tie_ok_next:
            last = items[-1]
            if (not last['rest']) and (not last.get('grace')) and last['dur'] >= 6 and r.random() < 0.13:
                # 다음 마디 첫 음에 이어 붙임
                last['tie'] = ['start']
                self.pending_tie = last['pitch']
                self.tie_src = last

        # --- 빔 ---
        apply_beams(items, meter)
        return items

    def add_graces(self, items, lv):
        r = self.rng
        if lv == '기초':
            p_slot, sizes = 0.28, [1]
        elif lv == '중급':
            p_slot, sizes = 0.40, [1, 2]
        else:
            p_slot, sizes = 0.55, [2, 3]
        meter_total = sum(it['dur'] for it in items)
        beats = set()
        # 마디 박 경계: 4분/8분 계열 모두 12 또는 18 단위
        t = 0
        beat_unit = 12 if meter_total % 12 == 0 and meter_total in (24, 36, 48) else 18
        while t < meter_total:
            beats.add(t)
            t += beat_unit
        # 각 음의 시작 시간
        starts = []
        t = 0
        for it in items:
            starts.append(t)
            if not it.get('grace'):
                t += it['dur']
        cands = []
        first_note_idx = None
        for i, it in enumerate(items):
            if it['rest']:
                continue
            if first_note_idx is None:
                first_note_idx = i
                continue
            if i == first_note_idx:
                continue
            if it['dur'] >= 6 and starts[i] in beats:
                cands.append(i)
        if not cands:
            return
        if r.random() > p_slot:
            return
        pos = r.choice(cands)
        target = items[pos]
        size = r.choice(sizes)
        base = target['dpos']
        gs = []
        direction = 1 if lv == '기초' else r.choice([1, -1])
        for k in range(size, 0, -1):
            gd = base + direction * k
            if not self.mel.in_range(gd):
                gd = base - direction * k
            if not self.mel.in_range(gd):
                gd = base
            gs.append(gd)
        if lv == '기초':
            gs = gs[-1:]
        size = len(gs)
        for j, gd in enumerate(gs):
            gi = dict(dur=0, ntype=('eighth' if size == 1 else '16th'),
                      rest=False, grace=True, dpos=gd,
                      pitch=self.mel.pitch_of(gd),
                      grace_slash=(size == 1))
            items.insert(pos + j, gi)
        # 2~3음 장식음 무리는 16분 겹빔으로 잇는다 (1음은 사선 깃발 그대로)
        if size >= 2:
            for j in range(size):
                val = 'begin' if j == 0 else ('end' if j == size - 1 else 'continue')
                items[pos + j]['beams'] = [(1, val), (2, val)]
        self.features.add('장식음')

    def add_slurs(self, items, lv):
        r = self.rng
        plain = [i for i, it in enumerate(items) if not it['rest'] and not it.get('grace')]
        if len(plain) < 3:
            return
        p = {'기초': 0.55, '중급': 0.65, '고급': 0.5}[lv]
        if r.random() > p:
            return
        start_idx = plain[r.randrange(1, len(plain) - 1)]
        length = r.choice([2, 2, 3, 3, 4]) if lv != '기초' else r.choice([2, 2, 3])
        group = [i for i in plain if i >= start_idx][:length]
        if len(group) < 2:
            return
        items[group[0]]['slur'] = ['start']
        items[group[-1]]['slur'] = ['stop']
        # 장식음이 붙은 음이면 장식음에도 슬러 (number 2 는 쓰지 않고 생략)
        for i in group:
            if items[i].get('grace'):
                items[i]['slur'] = None


def apply_beams(items, meter):
    # 시간 계산 (장식음 제외)
    t = 0
    starts = []
    for it in items:
        if it.get('grace'):
            starts.append(None)
            continue
        starts.append(t)
        t += it['dur']
    bounds = beat_bounds(meter)
    total = t

    def bindex(t0):
        for i in range(len(bounds) - 1):
            if bounds[i] <= t0 < bounds[i + 1]:
                return i
        return len(bounds) - 2

    beamable = []
    for i, it in enumerate(items):
        if it.get('grace') or it['rest']:
            continue
        if it['ntype'] in ('eighth', '16th'):
            beamable.append(i)

    def rest_between(a, b):
        for k in range(a + 1, b):
            it = items[k]
            if it['rest']:
                return True
        return False

    groups = []
    cur = []
    for i in beamable:
        if cur and (bindex(starts[i]) != bindex(starts[cur[-1]]) or rest_between(cur[-1], i)):
            groups.append(cur)
            cur = []
        cur.append(i)
    if cur:
        groups.append(cur)

    for g in groups:
        if len(g) < 2:
            continue
        for pos, i in enumerate(g):
            val = 'begin' if pos == 0 else ('end' if pos == len(g) - 1 else 'continue')
            items[i].setdefault('beams', []).append((1, val))
        sub = [i for i in g if items[i]['ntype'] == '16th']
        runs = []
        cur = []
        for i in sub:
            if cur and i != cur[-1] + 1:
                runs.append(cur)
                cur = []
            cur.append(i)
        if cur:
            runs.append(cur)
        for run in runs:
            if len(run) == 1:
                items[run[0]]['beams'].append((2, 'backward hook'))
            else:
                for pos, i in enumerate(run):
                    val = 'begin' if pos == 0 else ('end' if pos == len(run) - 1 else 'continue')
                    items[i]['beams'].append((2, val))


# ----------------------------------------------------------------------------
# 곡 구성
# ----------------------------------------------------------------------------
def build_piece(cfg, per_system=4, breaks_at=None):
    b = PieceBuilder(cfg)
    sections = cfg['sections']            # [(마디수, meter), ...]
    assert sum(s[0] for s in sections) == 32
    key_changes = cfg.get('key_changes', {})   # {마디번호: key}
    tempos = cfg.get('tempos', {1: 80})

    dyn_plan = cfg.get('dynamics', {})
    measure_xmls = []
    meta_meters = []

    # 1) 마디별 리듬 패턴을 먼저 정한다 (타이 여부를 다음 마디로 판단하기 위해)
    plans = []
    _n = 0
    for _si, (_count, _meter) in enumerate(sections):
        for _k in range(_count):
            _n += 1
            _prefs = b.tags_for(cfg['level'], _k % 8)
            _pat = b.pick_pattern(_meter, _prefs, cadence=(_n == 32))
            plans.append(dict(mnum=_n, meter=_meter, pat=_pat, k=_k, si=_si))

    for _idx, _pl in enumerate(plans):
            mnum = _pl['mnum']; meter = _pl['meter']; pat = _pl['pat']
            k = _pl['k']; si = _pl['si']
            is_phrase_end = (mnum % 8 == 0) or (mnum == 32)
            is_final = (mnum == 32)
            if mnum % 4 == 1 and mnum > 1:
                b.mel.phrase_start()
            tie_ok_next = False
            if _idx + 1 < len(plans):
                _nxt, _ = expand(plans[_idx + 1]['pat'])
                tie_ok_next = len(_nxt) > 0 and not _nxt[0]['rest']
            items = b.make_measure(meter, pat, mnum, is_phrase_end, is_final, tie_ok_next=tie_ok_next)

            # --- 방향 요소 ---
            dirs = []
            if mnum in tempos:
                unit = 'dotted-quarter' if meter in ((6, 8), (9, 8), (12, 8)) else 'quarter'
                dirs.append(tempo_xml(unit, tempos[mnum]))
                b.last_dyn = None
            if mnum in dyn_plan:
                dirs.append(dyn(dyn_plan[mnum]))
                b.last_dyn = dyn_plan[mnum]
            elif si > 0 and k == 0:
                d = {'기초': 'mf', '중급': 'mp', '고급': 'p'}[cfg['level']]
                dirs.append(dyn(d))
                b.last_dyn = d
            # 고급: subito p
            if cfg['level'] == '고급' and mnum in cfg.get('subito', []):
                dirs.append(words_below('subito p'))
                if not b.wedge_open:
                    dirs.append(wedge('crescendo'))
                    b.wedge_open = True
                b.features.add('subito p')
            # 크레셴도/디미누엔도
            if cfg['level'] != '기초' and not b.wedge_open and k == 3 and si % 2 == 0:
                dirs.append(wedge('crescendo'))
                b.wedge_open = True
            elif b.wedge_open and k in (1, 2):
                pass
            if b.wedge_open and k == 2:
                dirs.append(wedge('stop'))
                b.wedge_open = False
            # 곡 마지막
            if is_final:
                dirs.append(dyn('p'))
                if b.wedge_open:
                    dirs.append(wedge('stop'))
                    b.wedge_open = False

            # --- 장식음 슬러 정리: 각 grace 무리 뒤 첫 음에 stop 부여 ---
            for i, it in enumerate(items):
                if it.get('grace') and i > 0 and not items[i - 1].get('grace'):
                    for j in range(i + 1, len(items)):
                        if items[j].get('grace'):
                            continue
                        if not items[j]['rest']:
                            cur = list(items[j].get('gslur') or [])
                            if 'stop' not in cur:
                                cur.append('stop')
                            items[j]['gslur'] = cur
                        break
            # --- 노트 XML ---
            body = []
            prev_grace = False
            for it in items:
                if it.get('grace'):
                    gsl = None if prev_grace else [('start', 2)]
                    body.append(note_xml(it['pitch'], 0, it['ntype'], beams=it.get('beams'),
                                         grace=True, grace_slash=it.get('grace_slash', True),
                                         slurs=gsl))
                    prev_grace = True
                elif it['rest']:
                    prev_grace = False
                    body.append(note_xml(None, it['dur'], it['ntype'], dot=it['dot'],
                                         rest=True, beams=it.get('beams')))
                else:
                    prev_grace = False
                    sl = [(t, 1) for t in (it.get('slur') or [])] + \
                         [(t, 2) for t in (it.get('gslur') or [])]
                    body.append(note_xml(it['pitch'], it['dur'], it['ntype'], dot=it['dot'],
                                         beams=it.get('beams'),
                                         slurs=sl or None, ties=it.get('tie'),
                                         acc=it.get('acc'), mordent=it.get('mordent', False),
                                         trill=it.get('trill', False), stacc=it.get('stacc', False),
                                         accent=it.get('accent', False), tenuto=it.get('tenuto', False),
                                         tuplet=it.get('tuplet'), fermata=is_final and it is items[-1]))

            # --- attributes / barline ---
            attrs = ''
            if mnum == 1:
                attrs = (f"      <attributes>\n        <divisions>12</divisions>\n"
                         f"        <key><fifths>{b.fifths}</fifths></key>\n"
                         f"        <time><beats>{meter[0]}</beats><beat-type>{meter[1]}</beat-type></time>\n"
                         f"        <clef><sign>G</sign><line>2</line></clef>\n      </attributes>")
            else:
                parts = []
                if mnum in key_changes:
                    parts.append(f"        <key><fifths>{KEY_FIFTHS[key_changes[mnum]]}</fifths></key>")
                if meter != measure_xmls[-1]['meter']:
                    parts.append(f"        <time><beats>{meter[0]}</beats><beat-type>{meter[1]}</beat-type></time>")
                if parts:
                    attrs = "      <attributes>\n" + "\n".join(parts) + "\n      </attributes>"

            if breaks_at is None:
                sys_break = ('      <print new-system="yes"/>'
                             if (per_system and mnum % per_system == 1 and mnum > 1) else "")
            else:
                sys_break = '      <print new-system="yes"/>' if mnum in breaks_at else ""
            barline = ''
            if mnum == 32:
                barline = '      <barline location="right"><bar-style>light-heavy</bar-style></barline>'
            elif (mnum + 1) in key_changes or (mnum < 32 and meter != sections_meter(sections, mnum + 1)):
                barline = '      <barline location="right"><bar-style>light-light</bar-style></barline>'

            measure_xmls.append(dict(number=mnum, body=body, attrs=attrs, sys=sys_break,
                                     barline=barline, meter=meter, dirs=dirs))

    # --- 최종 XML ---
    blocks = []
    for mx in measure_xmls:
        blocks.append(f'    <measure number="{mx["number"]}">\n{mx["sys"]}\n{mx["attrs"]}\n'
                      + "\n".join(mx['dirs']) + "\n" + "\n".join(mx['body']) + "\n" + mx['barline'] + "\n    </measure>")
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
           '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
           '"http://www.musicxml.org/dtds/partwise.dtd">\n'
           '<score-partwise version="3.1">\n'
           '  <part-list><score-part id="P1"><part-name></part-name></score-part></part-list>\n'
           '  <part id="P1">\n' + "\n".join(blocks) + '\n  </part>\n</score-partwise>')
    return xml, b, measure_xmls


def sections_meter(sections, mnum):
    acc = 0
    for count, meter in sections:
        acc += count
        if mnum <= acc:
            return meter
    return sections[-1][1]


# ----------------------------------------------------------------------------
# 렌더링
# ----------------------------------------------------------------------------
# 조판 옵션 ------------------------------------------------------------------
# spacingLinear 를 키우면 음 길이에 비례해 좌우 간격이 벌어지고, 마디가 화면 폭을
# 거의 채우게 되어 Verovio 의 '남는 폭 배분' 이 개입할 여지가 줄어든다.
# (기본값 0.25 대비) 남는 폭이 크면 장식음 무리 앞에 빈틈이 몰리는 현상이 생긴다.
LAYOUT = {
    "pageWidth": 1800,
    "pageHeight": 4000,        # adjustPageHeight 로 내용 높이에 맞춰 잘라 쓴다
    "scale": 37,               # 출력 해상도
    "unit": 10.5,              # 오선 한 칸 크기(기본 9.0). 키우면 음표가 커진다
    "font": "Leland",          # SIL OFL 오픈소스 악보 활자
    "graceFactor": 0.58,
    "beamMaxSlope": 20,        # 기본 10°로는 계단처럼 끊기던 장식음 겹빔을 곧게 잇는다
    "breaks": "auto",          # 마디 폭에 맞춰 줄바꿈 → 줄이 가득 차 간격이 고르다
    "minLastJustification": 0.8,
    "breaksNoWidow": True,   # 마지막 줄에 마디 하나만 남지 않게
    "spacingLinear": 1.0,
    "spacingNonLinear": 0.34,
    "spacingSystem": 14,
    "justifyVertically": False,
    "mnumInterval": 0,
    "adjustPageHeight": True,
    "svgViewBox": True,
    "svgRemoveXlink": True,
    "footer": "none",
    "header": "none",
}


def system_measure_counts(xml, layout=None):
    """한 페이지에서 줄(system)별 마디 수를 센다."""
    tk = verovio.toolkit()
    opts = dict(LAYOUT)
    if layout:
        opts.update(layout)
    tk.setOptions(opts)
    tk.loadData(xml)
    svg = tk.renderToSVG(1)
    root = ET.fromstring(svg)
    ns = '{http://www.w3.org/2000/svg}'
    tops = []
    for g_el in root.iter(f'{ns}g'):
        if g_el.attrib.get('class') != 'measure':
            continue
        y = None
        for p in g_el.iter(f'{ns}path'):
            d = p.attrib.get('d', '')
            if d.startswith('M'):
                try:
                    y = float(d.split()[1])
                except (IndexError, ValueError):
                    y = None
                break
        if y is not None:
            tops.append(y)
    counts = []
    for y in tops:
        if counts and abs(y - counts[-1][0]) < 50:
            counts[-1][1] += 1
        else:
            counts.append([y, 1])
    return [c[1] for c in counts]


def render(xml, number, outdir, credit='LEE SEUNG CHUL (with AI)',
           footer='무단 복제 및 배포를 절대 금합니다.', font=None,
           filename=None, layout=None):
    tk = verovio.toolkit()
    opts = dict(LAYOUT)
    if layout:
        opts.update(layout)
    if font:
        opts["font"] = font
    tk.setOptions(opts)
    tk.loadData(xml)
    svg = tk.renderToSVG(1)
    n_meas = svg.count('class="measure"')
    if n_meas != 32:
        raise RuntimeError(f'#{number}: 1페이지에 마디 {n_meas}개만 들어갔다 (32개여야 함)')
    svg = svg.replace('class="mNum"', 'class="mNum" fill="#888888" opacity="0.75"')
    svg = re.sub(r'<rect class="page-margin"[^>]*/>', '', svg)

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    for parent in root.iter():
        for idx_c, child in enumerate(list(parent)):
            if child.tag == f"{ns}text":
                txt = "".join(child.itertext()).strip()
                m_t = re.match(r'^♩(\.?)\s*=\s*([0-9]+)$', txt)
                if m_t:
                    has_dot = (m_t.group(1) == ".")
                    bpm = m_t.group(2)
                    x_s = child.attrib.get("x")
                    y_s = child.attrib.get("y")
                    if not x_s or not y_s:
                        for ts in child.iter(f"{ns}tspan"):
                            if "x" in ts.attrib and "y" in ts.attrib:
                                x_s, y_s = ts.attrib["x"], ts.attrib["y"]
                                break
                    if x_s and y_s:
                        x, y = float(x_s), float(y_s) - 320
                        g = ET.Element(f"{ns}g", {"class": "tempo-vector"})
                        head = ET.Element(f"{ns}ellipse", {
                            "cx": f"{x+85:.1f}", "cy": f"{y-55:.1f}",
                            "rx": "108", "ry": "70",
                            "transform": f"rotate(-22 {x+85:.1f} {y-55:.1f})",
                            "fill": "#111111"})
                        stem = ET.Element(f"{ns}rect", {
                            "x": f"{x+164:.1f}", "y": f"{y-460:.1f}",
                            "width": "32", "height": "405", "fill": "#111111"})
                        g.append(head)
                        g.append(stem)
                        if has_dot:
                            dot = ET.Element(f"{ns}circle", {
                                "cx": f"{x+260:.1f}", "cy": f"{y-45:.1f}",
                                "r": "38", "fill": "#111111"})
                            g.append(dot)
                        eq_x = x + (345 if has_dot else 255)
                        t_el = ET.Element(f"{ns}text", {
                            "x": f"{eq_x:.1f}", "y": f"{y-10:.1f}",
                            "font-size": "350",
                            "font-family": "Noto Sans CJK KR, DejaVu Sans, sans-serif",
                            "font-weight": "bold", "fill": "#111111"})
                        t_el.text = f"= {bpm}"
                        g.append(t_el)
                        parent.remove(child)
                        parent.insert(idx_c, g)

    svg = ET.tostring(root, encoding="unicode")
    svg = re.sub(r'(<svg\b[^>]*>)', r'\1<rect width="100%" height="100%" fill="#ffffff"/>', svg, count=1)

    png_bytes = resvg_py.svg_to_bytes(svg_string=svg, zoom=3)
    score_rgba = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    white_bg = Image.new("RGBA", score_rgba.size, (255, 255, 255, 255))
    score_img = Image.alpha_composite(white_bg, score_rgba).convert("RGB")
    score_img = score_img.crop((18, 18, score_img.width - 18, score_img.height - 18))

    font_box = ImageFont.truetype(FONT_KR, 36)
    font_credit = ImageFont.truetype(FONT_KR, 30)
    font_footer = ImageFont.truetype(FONT_KR, 26)
    pad_top, pad_side, pad_bot = 135, 85, 118
    canvas = Image.new("RGB", (score_img.width + pad_side * 2,
                               score_img.height + pad_top + pad_bot), "white")
    draw = ImageDraw.Draw(canvas)

    # 좌상단 번호 박스
    label = str(number)
    nb = draw.textbbox((0, 0), label, font=font_box)
    tw = nb[2] - nb[0]
    box_w = max(72, tw + 34)
    box_h = 52
    box_x, box_y = pad_side + 20, 55
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], outline="#111111", width=3)
    draw.text((box_x + (box_w - tw) // 2, box_y + (box_h - (nb[3] - nb[1])) // 2 - 6),
              label, fill="#111111", font=font_box)

    # 우상단 크레딧
    cb = draw.textbbox((0, 0), credit, font=font_credit)
    draw.text((canvas.width - pad_side - 15 - (cb[2] - cb[0]), 62), credit,
              fill="#333333", font=font_credit)

    # 하단 문구
    fb = draw.textbbox((0, 0), footer, font=font_footer)
    draw.text(((canvas.width - (fb[2] - fb[0])) // 2, canvas.height - 58), footer,
              fill="#555555", font=font_footer)

    canvas.paste(score_img, (pad_side, pad_top))

    png_out = os.path.join(outdir, f"{filename or f'{number:03d}'}.png")
    pdf_out = os.path.join(outdir, f"{filename or f'{number:03d}'}.pdf")
    canvas.save(png_out, optimize=True)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=92, subsampling=0, optimize=True)
    scale = min((595 - 24) / canvas.width, (842 - 24) / canvas.height)
    w, h = canvas.width * scale, canvas.height * scale
    page.insert_image(fitz.Rect((595 - w) / 2, (842 - h) / 2, (595 + w) / 2, (842 + h) / 2),
                      stream=buf.getvalue())
    doc.save(pdf_out, deflate=True, garbage=4, clean=True)
    doc.close()
    return png_out, pdf_out, canvas.size


# ----------------------------------------------------------------------------
# 검증
# ----------------------------------------------------------------------------
def validate_xml(xml, cfg):
    root = ET.fromstring(xml.split('?>', 1)[1].replace('<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">', ''))
    part = root.find('part')
    measures = part.findall('measure')
    assert len(measures) == 32, f"measure count {len(measures)}"
    problems = []
    meter = None
    for idx, m in enumerate(measures, 1):
        attrs = m.find('attributes')
        if attrs is not None and attrs.find('time') is not None:
            t = attrs.find('time')
            meter = (int(t.find('beats').text), int(t.find('beat-type').text))
        total = 0
        for note in m.findall('note'):
            if note.find('grace') is not None:
                continue
            d = int(note.find('duration').text)
            total += d
            if note.find('rest') is None:
                p = note.find('pitch')
                step = p.find('step').text
                octv = int(p.find('octave').text)
                alter = int(p.find('alter').text) if p.find('alter') is not None else 0
                midi = midi_of(step, octv, alter)
                if not (LOW_MIDI <= midi <= HIGH_MIDI):
                    problems.append(f"m{idx} out of range {step}{octv} alter{alter} midi{midi}")
        expect = METER_TOTAL[meter]
        if total != expect:
            problems.append(f"m{idx} duration {total} != {expect} ({METER_LABEL[meter]})")
    if problems:
        raise AssertionError(f"#{cfg['no']}: " + "; ".join(problems[:8]))
    return True


# ----------------------------------------------------------------------------
# 테스트 실행
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    cfg = dict(no=1, level='기초', key='Eb', seed=1, sections=[(32, (4, 4))],
               tempos={1: 72}, dynamics={1: 'mp'}, title='순차 진행과 기본 슬러')
    xml, b, mxs = build_piece(cfg)
    validate_xml(xml, cfg)
    os.makedirs('out', exist_ok=True)
    print(render(xml, 1, 'out'))
    print('features', sorted(b.features))
