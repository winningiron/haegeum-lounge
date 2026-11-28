/* 해금 초견 라운지 · 연주 도구
   - 서양 전자 메트로놈 (마디 첫 박 강박 · 첫 마디 예비박)
   - Salamander Grand Piano 실제 녹음 샘플 가이드 멜로디 + 노래방식 마디 커서
   - 마이크 실시간 음정 체크 (자기상관 피치 검출) + 종료 후 점수·코멘트
   - A–B 마디 구간 반복, 집중 연습(30초 초견 읽기), 조율 기준음(440~450Hz)
   피아노 음원: Salamander Grand Piano (Alexander Holm, CC BY 3.0) */
window.LoungePlayer = (function () {
  'use strict';

  const $ = (s) => document.querySelector(s);
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const fmt = (s) => {
    s = Math.max(0, Math.round(s));
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  };

  const D = {};                       // DOM
  const S = {
    piece: null, tl: null, reqNo: null,
    events: [], evIdx: 0,
    playing: false, mode: 'both', speed: 1,
    anchorCtx: 0, anchorPos: 0, pos: 0,
    ab: { a: null, b: null, on: false },
    sel: 0,                            // 현재(정지 시) 선택 마디 index
    lastBar: -1,
    focus: false, timerId: 0, rafId: 0,
    countdown: 0, countdownId: 0,
    a4: 442,
    mic: { on: false, stream: null, analyser: null, buf: null },
    session: null,
    result: null,
    geo: { left: 0, top: 0, w: 0, h: 0 }
  };

  /* ============================================================ 피아노 음원 */
  const SAMPLES = [57, 60, 63, 66, 69, 72, 75, 78, 81, 84];   // A3 C4 D#4 F#4 A4 C5 D#5 F#5 A5 C6
  const NAMES = { 57: 'A3', 60: 'C4', 63: 'Ds4', 66: 'Fs4', 69: 'A4',
                  72: 'C5', 75: 'Ds5', 78: 'Fs5', 81: 'A5', 84: 'C6' };
  const Sound = {
    ctx: null, master: null, bus: null, buffers: {}, ready: false, loading: null,
    sources: new Set(),
    init() {
      if (!this.ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return false;
        this.ctx = new AC();
        this.master = this.ctx.createGain();
        this.master.gain.value = 0.85;
        this.master.connect(this.ctx.destination);
      }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      return true;
    },
    load() {
      if (this.ready) return Promise.resolve(true);
      if (this.loading) return this.loading;
      if (!this.init()) return Promise.resolve(false);
      this.loading = Promise.all(SAMPLES.map((m) => new Promise((res) => {
        fetch('assets/piano/' + NAMES[m] + '.mp3')
          .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(r.status)))
          .then((buf) => new Promise((ok, no) => this.ctx.decodeAudioData(buf, ok, no)))
          .then((audio) => { this.buffers[m] = audio; res(true); })
          .catch(() => res(false));
      }))).then((r) => {
        this.ready = r.some(Boolean);
        this.loading = null;
        return this.ready;
      });
      return this.loading;
    },
    nearest(midi) {
      let best = SAMPLES[0];
      for (const s of SAMPLES) if (Math.abs(s - midi) < Math.abs(best - midi)) best = s;
      return best;
    },
    note(midi, when, dur, vel) {
      const ctx = this.ctx;
      const s = this.nearest(midi);
      const buf = this.buffers[s];
      if (!buf) return;
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.playbackRate.value = Math.pow(2, (midi - s) / 12);
      const g = ctx.createGain();
      const peak = 0.30 * vel;
      const atk = 0.004, rel = 0.18;
      g.gain.setValueAtTime(0.0001, when);
      g.gain.exponentialRampToValueAtTime(peak, when + atk);
      const sustainEnd = Math.max(when + atk + 0.02, when + dur);
      g.gain.setValueAtTime(peak, sustainEnd - 0.04 > when + atk ? sustainEnd - 0.04 : when + atk);
      g.gain.exponentialRampToValueAtTime(0.0001, sustainEnd + rel);
      src.connect(g).connect(this.bus || this.master);
      src.start(when);
      src.stop(sustainEnd + rel + 0.05);
      this.sources.add(src);
      src.onended = () => this.sources.delete(src);
    },
    click(when, strong) {
      const ctx = this.ctx;
      const g = ctx.createGain();
      const o = ctx.createOscillator();
      o.type = 'sine';
      o.frequency.setValueAtTime(strong ? 1568 : 1046, when);
      const peak = strong ? 0.34 : 0.17;
      g.gain.setValueAtTime(0.0001, when);
      g.gain.exponentialRampToValueAtTime(peak, when + 0.003);
      g.gain.exponentialRampToValueAtTime(0.0001, when + (strong ? 0.20 : 0.10));
      o.connect(g).connect(this.master);
      o.start(when);
      o.stop(when + (strong ? 0.24 : 0.13));
      // 아주 짧은 타격감 (전자 메트로놈)
      const n = ctx.createBufferSource();
      const len = Math.floor(ctx.sampleRate * 0.012);
      if (!this._noise) {
        const nb = ctx.createBuffer(1, len, ctx.sampleRate);
        const d = nb.getChannelData(0);
        for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
        this._noise = nb;
      }
      n.buffer = this._noise;
      const ng = ctx.createGain();
      ng.gain.value = strong ? 0.08 : 0.05;
      const bp = ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.frequency.value = strong ? 2600 : 1900;
      n.connect(bp).connect(ng).connect(this.master);
      n.start(when);
    },
    tone(freq, when, dur, vol) {
      const ctx = this.ctx;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'sine';
      o.frequency.value = freq;
      g.gain.setValueAtTime(0.0001, when);
      g.gain.exponentialRampToValueAtTime(vol || 0.16, when + 0.03);
      g.gain.setValueAtTime(vol || 0.16, when + dur - 0.12);
      g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
      o.connect(g).connect(this.master);
      o.start(when);
      o.stop(when + dur + 0.02);
    },
    panic() {
      for (const s of Array.from(this.sources)) {
        try { s.stop(); } catch (e) { /* 이미 끝난 소리 */ }
      }
      this.sources.clear();
    }
  };

  /* ============================================================ 타임라인 */
  function noteName(midi) {
    const pc = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B'];
    return pc[((midi % 12) + 12) % 12] + (Math.floor(midi / 12) - 1);
  }
  const hzOf = (midi, a4) => (a4 || S.a4) * Math.pow(2, (midi - 69) / 12);

  function loadTimeline(no) {
    if (S.tl && S.tl.no === no) return Promise.resolve(S.tl);
    if (S.reqNo === no && S.req) return S.req;
    S.reqNo = no;
    S.req = fetch('data/tl/' + String(no).padStart(3, '0') + '.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .catch(() => null);
    return S.req;
  }

  function buildEvents(tl) {
    const ev = [];
    const b0 = tl.bars[0];
    // 예비박: 첫 마디 한 마디 앞에서 같은 박자로
    for (const off of b0.b) {
      ev.push({ t: b0.t - b0.d + (off / 12) * (60 / b0.q), k: 'c', s: off === b0.b[0] ? 2 : 1 });
    }
    for (const bar of tl.bars) {
      for (const off of bar.b) {
        ev.push({ t: bar.t + (off / 12) * (60 / bar.q), k: 'c', s: off === bar.b[0] ? 2 : 1 });
      }
    }
    for (const n of tl.notes) {
      ev.push({ t: n[0] / 1000, d: n[1] / 1000, midi: n[2], m: n[3], v: n[4], k: 'n' });
    }
    ev.sort((a, b) => a.t - b.t);
    return ev;
  }

  function barAt(t) {
    const bars = S.tl.bars;
    let lo = 0, hi = bars.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (bars[mid].t <= t) lo = mid; else hi = mid - 1;
    }
    return lo;
  }

  /* ============================================================ 커서·레이아웃 */
  function syncGeometry() {
    const img = D.img;
    if (!img || !img.naturalWidth) return;
    const left = img.offsetLeft, top = img.offsetTop;
    const w = img.clientWidth, h = img.clientHeight;
    S.geo = { left, top, w, h };
    D.layer.style.left = left + 'px';
    D.layer.style.top = top + 'px';
    D.layer.style.width = w + 'px';
    D.layer.style.height = h + 'px';
    drawCursor(S.pos, true);
  }

  function barBox(i) {
    const b = S.tl.bars[clamp(i, 0, S.tl.bars.length - 1)];
    return b;
  }

  function drawCursor(t, force) {
    if (!S.tl || !S.geo.w) return;
    const bars = S.tl.bars;
    let i = barAt(Math.max(0, t));
    const b = bars[i];
    const inner = clamp((t - b.t) / b.d, 0, 1);
    const x = b.x * S.geo.w;
    const y = b.y * S.geo.h;
    const w = b.w * S.geo.w;
    const h = b.h * S.geo.h;
    const c = D.cursor;
    c.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px)`;
    c.style.width = w.toFixed(1) + 'px';
    c.style.height = h.toFixed(1) + 'px';
    c.querySelector('.pfill').style.width = (inner * 100).toFixed(2) + '%';
    if (D.head) D.head.style.left = (inner * 100).toFixed(2) + '%';
    if (S.playing && i !== S.lastBar) {
      S.lastBar = i;
      ensureVisible(i);
    }
    if (force) S.lastBar = i;
    // A–B 표시
    D.markA.hidden = S.ab.a == null;
    D.markB.hidden = S.ab.b == null;
    if (S.ab.a != null) placeMark(D.markA, S.ab.a);
    if (S.ab.b != null) placeMark(D.markB, S.ab.b);
  }

  function placeMark(el, i) {
    const b = barBox(i);
    el.style.transform = `translate(${(b.x * S.geo.w).toFixed(1)}px,${(b.y * S.geo.h).toFixed(1)}px)`;
  }

  function ensureVisible(i) {
    const st = D.stage, b = S.tl.bars[i], sys = S.tl.systems[b.s];
    const top = D.img.offsetTop + sys.y0 * D.img.clientHeight - 24;
    const bot = D.img.offsetTop + sys.y1 * D.img.clientHeight + 24;
    const viewTop = st.scrollTop, viewBot = st.scrollTop + st.clientHeight;
    if (top < viewTop + 8 || bot > viewBot - 8) {
      st.scrollTo({ top: Math.max(0, top - st.clientHeight * 0.14), behavior: 'smooth' });
    }
  }

  /* ============================================================ 재생 */
  function currentPos() {
    if (!S.playing) return S.pos;
    return S.anchorPos + (Sound.ctx.currentTime - S.anchorCtx) * S.speed;
  }

  function scheduleEvent(e, when) {
    if (e.k === 'c') {
      if (S.mode !== 'piano') Sound.click(when, e.s === 2);
    } else {
      if (S.mode !== 'metro') Sound.note(e.midi, when, e.d / S.speed, e.v === 3 ? 1.0 : e.v === 1 ? 0.45 : 0.82);
    }
  }

  function pump() {
    if (!S.playing) return;
    const now = Sound.ctx.currentTime;
    const pos = currentPos();
    const horizon = pos + 0.5 * S.speed;          // 0.5초 앞까지 미리 잡는다
    let guard = 0;
    while (S.evIdx < S.events.length && guard++ < 400) {
      const e = S.events[S.evIdx];
      if (e.t > horizon) break;
      const when = now + (e.t - pos) / S.speed;
      if (when > now - 0.02) scheduleEvent(e, Math.max(when, now));
      S.evIdx++;
    }
    // 끝
    if (pos > S.tl.dur + 0.25) { stop(true); return; }
    // A–B 반복
    if (S.ab.on && S.ab.a != null && S.ab.b != null) {
      const bEnd = S.tl.bars[S.ab.b].t + S.tl.bars[S.ab.b].d;
      if (pos >= bEnd) { startAt(S.tl.bars[S.ab.a].t, false); return; }
    }
    if (S.mic.on) sampleMic();
    S.pos = pos;
    drawCursor(pos);
    updateProgress(pos);
  }

  function startAt(pos, countIn) {
    Sound.init();
    Sound.bus = Sound.ctx.createGain();
    Sound.bus.connect(Sound.master);
    const from = countIn ? pos - S.tl.bars[barAt(Math.max(0, pos))].d : pos;
    S.anchorPos = from;
    S.anchorCtx = Sound.ctx.currentTime + 0.06;
    S.evIdx = 0;
    while (S.evIdx < S.events.length && S.events[S.evIdx].t < from - 0.001) S.evIdx++;
    S.playing = true;
    S.lastBar = -1;
    S.noteIdx = 0;
    D.play.classList.add('is-playing');
    D.play.querySelector('b').textContent = '정지';
    D.play.querySelector('#pPlayIcon').textContent = '■';
    if (!S.timerId) S.timerId = setInterval(pump, 40);
    pump();
  }

  function play() {
    if (!S.tl) return;
    Sound.load().then((ok) => {
      if (!ok) { toast('피아노 음원을 불러오지 못했어요. 잠시 뒤 다시 시도해 주세요.'); return; }
      newSession();
      const start = S.ab.on && S.ab.a != null ? S.tl.bars[S.ab.a].t : S.tl.bars[S.sel].t;
      startAt(start, S.mode !== 'piano');
    });
  }

  function stop(atEnd) {
    if (!S.playing) return;
    S.playing = false;
    S.pos = atEnd ? S.tl.dur : currentPos();
    clearInterval(S.timerId);
    S.timerId = 0;
    Sound.panic();
    if (Sound.bus) { try { Sound.bus.disconnect(); } catch (e) {} Sound.bus = null; }
    D.play.classList.remove('is-playing');
    D.play.querySelector('b').textContent = '연주';
    D.play.querySelector('#pPlayIcon').textContent = '▶';
    if (atEnd) { S.sel = 0; drawCursor(0); updateProgress(0); S.pos = 0; }
    else { drawCursor(S.pos); updateProgress(S.pos); }
    if (S.mic.on && S.session && S.session.samples > 30) showResult();
    else if (S.mic.on && S.session) S.session = null;
  }

  function seekMeasure(i) {
    S.sel = clamp(i, 0, S.tl.bars.length - 1);
    const t = S.tl.bars[S.sel].t;
    S.pos = t;
    if (S.playing) { startAt(t, false); }
    else { drawCursor(t); updateProgress(t); }
  }

  function updateProgress(t) {
    const total = S.tl ? S.tl.dur : 0;
    D.fill.style.width = (total ? clamp(t / total, 0, 1) * 100 : 0).toFixed(2) + '%';
    D.time.textContent = fmt(t);
  }

  /* ============================================================ 마이크 음정 */
  function noteIndexAt(t) {
    const notes = S.tl.notes;
    let i = S.noteIdx || 0;
    const ms = t * 1000;
    if (i > 0 && notes[i - 1][0] > ms) i = 0;
    while (i < notes.length && notes[i][0] <= ms) i++;
    S.noteIdx = i;
    // 현재 울리는 음: i-1 부터 거슬러 올라가 t를 담고 있는 음
    for (let j = i - 1; j >= Math.max(0, i - 6); j--) {
      const n = notes[j];
      if (ms >= n[0] && ms < n[0] + Math.max(120, n[1])) return n;
    }
    return null;
  }

  function initAnalyser(stream) {
    Sound.init();
    const ctx = Sound.ctx;
    const src = ctx.createMediaStreamSource(stream);
    const an = ctx.createAnalyser();
    an.fftSize = 4096;
    an.smoothingTimeConstant = 0;
    src.connect(an);
    S.mic.analyser = an;
    S.mic.buf = new Float32Array(an.fftSize);
  }

  // McLeod NSDF 기반 피치 검출
  function detectPitch(buf, sr) {
    const N = buf.length;
    let rms = 0;
    for (let i = 0; i < N; i++) rms += buf[i] * buf[i];
    rms = Math.sqrt(rms / N);
    if (rms < 0.008) return 0;
    const minLag = Math.floor(sr / 1300);
    const maxLag = Math.min(Math.floor(sr / 120), Math.floor(N / 2));
    const nsdf = new Float32Array(maxLag + 2);
    for (let lag = minLag; lag <= maxLag; lag++) {
      let ac = 0, m = 0;
      const n = N - lag;
      for (let i = 0; i < n; i++) {
        const a = buf[i], b = buf[i + lag];
        ac += a * b;
        m += a * a + b * b;
      }
      nsdf[lag] = m > 1e-9 ? (2 * ac) / m : 0;
    }
    // 첫 양의 구간에서 가장 큰 봉우리
    let lag = -1, best = 0.0001;
    let started = false;
    for (let i = minLag; i <= maxLag; i++) {
      if (nsdf[i] > 0.15) started = true;
      if (started && nsdf[i] > nsdf[i - 1] && nsdf[i] >= nsdf[i + 1]) {
        if (nsdf[i] > best) { best = nsdf[i]; lag = i; }
        if (best > 0.92 && i > minLag + 4) break;
      }
    }
    if (lag < 0 || best < 0.55) return 0;
    // 포물선 보정
    const y0 = nsdf[lag - 1], y1 = nsdf[lag], y2 = nsdf[lag + 1];
    const denom = 2 * (2 * y1 - y0 - y2);
    const delta = denom !== 0 ? (y2 - y0) / denom : 0;
    const trueLag = lag + clamp(delta, -0.5, 0.5);
    return sr / trueLag;
  }

  function sampleMic() {
    const an = S.mic.analyser;
    if (!an || !S.tl) return;
    const now = performance.now();
    if (S.mic.lastT && now - S.mic.lastT < 55) return;
    S.mic.lastT = now;
    an.getFloatTimeDomainData(S.mic.buf);
    const t = currentPos();
    const n = noteIndexAt(t);
    const f = detectPitch(S.mic.buf, Sound.ctx.sampleRate);
    const sess = S.session;
    if (!sess) return;
    if (!n || !f) {
      D.hud.classList.toggle('is-idle', !n);
      return;
    }
    const target = hzOf(n[2]);
    const cents = 1200 * Math.log2(f / target);
    if (!isFinite(cents) || Math.abs(cents) > 120) return;      // 옥타브 오류·다른 소리 제외
    const m = n[3];
    const s = sess.measures[m] || (sess.measures[m] = { sum: 0, sum2: 0, cnt: 0, bad: 0 });
    s.sum += cents; s.sum2 += cents * cents; s.cnt++;
    if (Math.abs(cents) > 35) s.bad++;
    sess.sum += cents; sess.sum2 += cents * cents; sess.samples++;
    if (Math.abs(cents) <= 20) sess.good++;
    else if (Math.abs(cents) <= 40) sess.ok++;
    else sess.off++;
    // 화면 표시
    D.hud.classList.remove('is-idle');
    D.hud.classList.toggle('is-good', Math.abs(cents) <= 20);
    D.hud.classList.toggle('is-sharp', cents > 20);
    D.hud.classList.toggle('is-flat', cents < -20);
    D.hudNote.textContent = noteName(n[2]);
    D.hudCent.textContent = (cents > 0 ? '+' : '') + Math.round(cents) + '¢';
    D.hudNeedle.style.transform = 'translateX(' + clamp(cents / 50, -1, 1) * 46 + 'px)';
  }

  function resetSessionIfNeeded() {
    if (!S.session) newSession();
  }
  function newSession() {
    S.session = { measures: {}, sum: 0, sum2: 0, samples: 0, good: 0, ok: 0, off: 0 };
  }

  async function micToggle() {
    if (S.mic.on) {
      micOff();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast('이 브라우저에서는 마이크를 쓸 수 없어요.');
      return;
    }
    Sound.init();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
      });
      S.mic.stream = stream;
      initAnalyser(stream);
      S.mic.on = true;
      newSession();
      D.mic.classList.add('is-on');
      D.mic.setAttribute('aria-pressed', 'true');
      D.hud.hidden = false;
      D.hud.classList.add('is-idle');
      toast('음정 체크를 켰습니다. 연주가 끝나면 점수와 코멘트를 보여 드려요.');
    } catch (e) {
      toast('마이크 권한이 필요합니다. 브라우저 주소창의 권한을 허용해 주세요.');
    }
  }

  function micOff() {
    S.mic.on = false;
    if (S.mic.stream) S.mic.stream.getTracks().forEach((t) => t.stop());
    S.mic.stream = null;
    S.mic.analyser = null;
    D.mic.classList.remove('is-on');
    D.mic.setAttribute('aria-pressed', 'false');
    D.hud.hidden = true;
    if (S.session && S.session.samples > 30) showResult();
  }

  /* ============================================================ 결과 */
  function showResult() {
    const q = S.session;
    if (!q || !q.samples) return;
    const total = q.good + q.ok + q.off || 1;
    const score = Math.round(100 * (q.good + 0.5 * q.ok) / total);
    const mean = q.sum / q.samples;
    const sd = Math.sqrt(Math.max(0, q.sum2 / q.samples - mean * mean));
    D.rcScore.textContent = score;
    D.rcSub.textContent = `${S.piece.no}번 ${S.piece.title} · ${q.samples}회 측정`;
    const lines = [];
    if (Math.abs(mean) <= 10) lines.push(`음정 중심이 안정적입니다. 평균 <b>${mean > 0 ? '+' : ''}${mean.toFixed(0)}센트</b>.`);
    else if (mean < 0) lines.push(`전체적으로 <b>낮게</b> 잡혔습니다 (평균 ${mean.toFixed(0)}센트). 유현 개방현을 조금 올려 보세요.`);
    else lines.push(`전체적으로 <b>높게</b> 잡혔습니다 (평균 +${mean.toFixed(0)}센트). 활 압력을 조금 줄여 보세요.`);
    if (sd > 28) lines.push(`음마다 흔들림이 큽니다 (편차 ±${sd.toFixed(0)}센트). 느린 속도(0.75×)로 한 번 더.`);
    // 흔들린 구간
    const worst = Object.entries(q.measures)
      .filter(([, v]) => v.cnt >= 4)
      .map(([m, v]) => ({ m: +m, mean: v.sum / v.cnt, abs: Math.abs(v.sum / v.cnt), bad: v.bad / v.cnt }))
      .filter((x) => x.abs > 25 || x.bad > 0.4)
      .sort((a, b) => (b.abs + b.bad * 60) - (a.abs + a.bad * 60))
      .slice(0, 3);
    if (worst.length) {
      const ranges = worst.map((x) => `${x.m}마디(${x.mean > 0 ? '+' : ''}${x.mean.toFixed(0)}¢)`).join(', ');
      lines.push(`흔들린 곳: <b>${ranges}</b> — 그 마디만 A–B로 묶어 반복해 보세요.`);
    } else if (score >= 80) {
      lines.push('흔들린 마디가 거의 없습니다. 템포를 한 단계 올려 보세요.');
    }
    if (score >= 90) lines.push('초견으로 이 정도면 아주 좋습니다. 바로 다음 곡으로.');
    D.rcLines.innerHTML = lines.map((t) => `<li>${t}</li>`).join('');
    // 마디별 눈금
    const bars = S.tl.bars;
    const step = Math.max(1, Math.ceil(bars.length / 60));
    let ticks = '';
    for (let i = 0; i < bars.length; i += step) {
      const v = q.measures[bars[i].n];
      let cls = 'none';
      if (v && v.cnt) {
        const a = Math.abs(v.sum / v.cnt);
        cls = a <= 20 ? 'good' : a <= 40 ? 'mid' : 'bad';
      }
      ticks += `<i class="${cls}"></i>`;
    }
    D.rcTicks.innerHTML = ticks;
    D.rc.hidden = false;
    S.result = score;
  }

  /* ============================================================ 조율 */
  const TONIC = { '-1': 'F', '-2': 'B♭', '-3': 'E♭', '-4': 'A♭', '-5': 'D♭', '-6': 'G♭' };
  const TONIC_PC = { 'F': 5, 'B♭': 10, 'E♭': 3, 'A♭': 8, 'D♭': 1, 'G♭': 6 };

  function updateTune() {
    const a4 = S.a4;
    D.tpA4.textContent = a4.toFixed(1);
    D.tuneHz.textContent = a4.toFixed(0);
    if (S.piece) {
      const name = TONIC[String(S.piece.fifths)] || '—';
      const pc = TONIC_PC[name];
      const midi = pc == null ? 69 : (pc >= 3 ? 60 + pc : 48 + pc);   // 으뜸음은 가운데 음역에서
      D.tpTonic.textContent = midi ? noteName(midi) : '—';
      D.tpTonic.dataset.midi = midi;
    }
    D.tpG.textContent = 'G3 · ' + hzOf(55).toFixed(1) + 'Hz';
    D.tpC.textContent = 'C4 · ' + hzOf(60).toFixed(1) + 'Hz';
  }

  function playTone(which) {
    Sound.init();
    const a4 = S.a4;
    const now = Sound.ctx.currentTime + 0.03;
    if (which === 'a4') Sound.tone(a4, now, 1.8, 0.14);
    else if (which === 'g3') Sound.tone(hzOf(55), now, 1.8, 0.14);
    else if (which === 'c4') Sound.tone(hzOf(60), now, 1.8, 0.14);
    else if (which === 'tonic') {
      const midi = +(D.tpTonic.dataset.midi || 72);
      Sound.tone(hzOf(midi), now, 1.8, 0.14);
    }
  }

  /* ============================================================ 집중 연습 */
  function setFocus(on) {
    S.focus = on;
    D.modal.classList.toggle('is-focus', on);
    D.focusExit.hidden = !on;
    if (on) {
      window.scrollTo(0, 0);
      D.stage.scrollTop = 0;
      D.stage.scrollLeft = 0;
      setTimeout(() => { D.stage.scrollTop = 0; syncGeometry(); }, 60);
    } else {
      clearInterval(S.countdownId);
      S.countdownId = 0;
      D.timerEl.classList.remove('is-show');
      D.modal.classList.remove('is-counting');
    }
    setTimeout(syncGeometry, 80);
  }

  function startReadTimer(sec) {
    if (!S.focus) setFocus(true);
    D.stage.scrollTop = 0;
    let left = sec;
    D.modal.classList.add('is-counting');
    D.timerEl.classList.add('is-show');
    D.timerEl.innerHTML = `<b>${left}</b><span>초 동안 악보를 읽으세요</span>`;
    clearInterval(S.countdownId);
    S.countdownId = setInterval(() => {
      left--;
      if (left > 0) {
        D.timerEl.innerHTML = `<b>${left}</b><span>초 동안 악보를 읽으세요</span>`;
      } else {
        clearInterval(S.countdownId);
        S.countdownId = 0;
        D.timerEl.innerHTML = '<b>시작하세요!</b>';
        Sound.init();
        const now = Sound.ctx.currentTime + 0.02;
        Sound.tone(1318, now, 0.14, 0.2);
        Sound.tone(1760, now + 0.18, 0.22, 0.2);
        setTimeout(() => { D.timerEl.classList.remove('is-show'); D.modal.classList.remove('is-counting'); }, 2000);
        S.sel = 0;
        play();
      }
    }, 1000);
  }

  /* ============================================================ UI */
  let toastTimer = 0;
  function toast(msg) {
    let el = $('#pToast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'pToast';
      el.className = 'p-toast';
      D.modal.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add('is-show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('is-show'), 3600);
  }

  function bind() {
    D.play.addEventListener('click', () => {
      if (S.playing) stop(false); else play();
    });
    D.modeEl.querySelectorAll('button').forEach((b) => {
      b.addEventListener('click', () => {
        S.mode = b.dataset.mode;
        D.modeEl.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x === b));
        if (S.playing) { const t = currentPos(); startAt(t, false); }
      });
    });
    D.speedEl.querySelectorAll('button').forEach((b) => {
      b.addEventListener('click', () => {
        const t = currentPos();
        S.speed = +b.dataset.speed;
        D.speedEl.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x === b));
        if (S.playing) startAt(t, false);
      });
    });
    D.ab.addEventListener('click', () => {
      if (S.ab.a == null) { S.ab.a = S.sel; toast('A 지점: ' + (S.sel + 1) + '마디'); }
      else if (S.ab.b == null) { S.ab.b = S.sel; S.ab.on = true; D.ab.classList.add('is-on'); D.ab.setAttribute('aria-pressed', 'true'); toast('B 지점: ' + (S.sel + 1) + '마디 · 구간 반복 중'); }
      else { S.ab = { a: null, b: null, on: false }; D.ab.classList.remove('is-on'); D.ab.setAttribute('aria-pressed', 'false'); toast('구간 반복을 해제했습니다.'); }
      drawCursor(S.pos, true);
    });
    D.mic.addEventListener('click', micToggle);
    D.tune.addEventListener('click', () => {
      if (!D.tunePop.hidden) { D.tunePop.hidden = true; return; }
      updateTune();
      D.tunePop.hidden = false;
    });
    $('#tuneClose').addEventListener('click', () => { D.tunePop.hidden = true; });
    D.tpSlider.addEventListener('input', () => {
      S.a4 = +D.tpSlider.value;
      updateTune();
      try { localStorage.setItem('hg_a4', String(S.a4)); } catch (e) {}
    });
    D.tunePop.querySelectorAll('[data-tone]').forEach((b) => {
      b.addEventListener('click', () => playTone(b.dataset.tone));
    });
    D.focus.addEventListener('click', () => {
      if (!S.focus) setFocus(true);
      startReadTimer(30);
    });
    D.focusExit.addEventListener('click', () => setFocus(false));
    $('#focusTimer').addEventListener('click', () => startReadTimer(30));
    $('#rcClose').addEventListener('click', () => { D.rc.hidden = true; });
    $('#rcDismiss').addEventListener('click', () => { D.rc.hidden = true; });
    $('#rcAgain').addEventListener('click', () => { D.rc.hidden = true; S.sel = 0; newSession(); play(); });
    // 진행 바 클릭 이동
    D.seek.addEventListener('click', (e) => {
      if (!S.tl) return;
      const r = D.seek.getBoundingClientRect();
      const t = clamp((e.clientX - r.left) / r.width, 0, 1) * S.tl.dur;
      seekMeasure(barAt(t));
    });
    // 악보 클릭 → 그 마디부터
    D.stage.addEventListener('click', (e) => {
      if (!S.tl || !S.geo.w) return;
      if (Math.abs(e.clientX - S.dragX) > 8 || Math.abs(e.clientY - S.dragY) > 8) return;
      const r = D.img.getBoundingClientRect();
      const fx = (e.clientX - r.left) / r.width;
      const fy = (e.clientY - r.top) / r.height;
      const bars = S.tl.bars;
      let best = -1, bestD = 1e9;
      bars.forEach((b, i) => {
        const dx = Math.max(b.x - fx, 0, fx - (b.x + b.w));
        const dy = Math.max(b.y - fy, 0, fy - (b.y + b.h));
        const d = dx * 3 + dy;
        if (d < bestD) { bestD = d; best = i; }
      });
      if (best >= 0 && bestD < 0.05) seekMeasure(best);
    });
    D.stage.addEventListener('pointerdown', (e) => { S.dragX = e.clientX; S.dragY = e.clientY; });
    // 키보드
    window.addEventListener('keydown', (e) => {
      if (!S.tl || !D.modal.classList.contains('is-open')) return;
      if (e.target && /INPUT|TEXTAREA/.test(e.target.tagName)) return;
      if (e.code === 'Space') { e.preventDefault(); if (S.playing) stop(false); else play(); }
      if (e.key === '[' && S.tl) seekMeasure(barAt(S.pos) - 1);
      if (e.key === ']' && S.tl) seekMeasure(barAt(S.pos) + 1);
    });
    // 30초 타이머 버튼 (집중 연습 진입시)
    setInterval(() => {
      if (S.playing && S.tl) updateProgress(currentPos());
    }, 250);
  }

  /* ============================================================ 열기/닫기 */
  function open(piece) {
    D.modal = $('#modal');
    D.stage = $('#stage');
    D.img = $('#mImg');
    D.layer = $('#playLayer');
    D.cursor = $('#pCursor');
    D.head = D.cursor.querySelector('.phead');
    D.markA = $('#pMarkA');
    D.markB = $('#pMarkB');
    D.play = $('#pPlay');
    D.modeEl = $('#pMode');
    D.speedEl = $('#pSpeed');
    D.ab = $('#pAB');
    D.mic = $('#pMic');
    D.tune = $('#pTune');
    D.tuneHz = $('#pTuneHz');
    D.focus = $('#pFocus');
    D.focusExit = $('#pFocusExit');
    D.seek = $('#pSeek');
    D.fill = $('#pSeekFill');
    D.time = $('#pTime');
    D.total = $('#pTotal');
    D.hud = $('#pitchHud');
    D.hudNote = $('#phNote');
    D.hudCent = $('#phCent');
    D.hudNeedle = $('#phNeedle');
    D.timerEl = $('#focusTimer');
    D.rc = $('#resultCard');
    D.rcScore = $('#rcScore');
    D.rcSub = $('#rcSub');
    D.rcLines = $('#rcLines');
    D.rcTicks = $('#rcTicks');
    D.tunePop = $('#tunePop');
    D.tpA4 = $('#tpA4');
    D.tpSlider = $('#tpSlider');
    D.tpTonic = $('#tpTonic');
    D.tpG = $('#tpG');
    D.tpC = $('#tpC');

    if (!bind.done) { bind(); bind.done = true; }
    try {
      const v = localStorage.getItem('hg_a4');
      if (v) { S.a4 = +v; D.tpSlider.value = String(S.a4); }
    } catch (e) {}

    stop(false);
    S.piece = piece;
    S.tl = null;
    S.sel = 0;
    S.pos = 0;
    S.ab = { a: null, b: null, on: false };
    D.ab.classList.remove('is-on');
    S.session = null;
    D.rc.hidden = true;
    D.tunePop.hidden = true;
    D.total.textContent = '0:00';
    updateProgress(0);
    D.cursor.style.opacity = '0';
    updateTune();
    Sound.load();
    loadTimeline(piece.no).then((tl) => {
      if (!tl || (S.piece && S.piece.no !== tl.no)) return;
      S.tl = tl;
      S.events = buildEvents(tl);
      D.total.textContent = fmt(tl.dur);
      D.cursor.style.opacity = '';
      S.sel = 0;
      drawCursor(0, true);
      syncGeometry();
    });
  }

  function close() {
    stop(false);
    if (S.mic.on) micOff();
    if (S.focus) setFocus(false);
    S.piece = null; S.tl = null; S.events = [];
    D.rc.hidden = true; D.tunePop.hidden = true;
    clearInterval(S.countdownId);
    if (D.timerEl) D.timerEl.classList.remove('is-show');
  }

  return { open, close, syncGeometry, setFocus, startReadTimer,
           _S: S, _Sound: Sound, _barAt: barAt, _draw: drawCursor };
})();
