/* 해금 초견 라운지 */
(function () {
  const LEVELS = {
    '기초': {
      desc: '온음표·2분음표에서 시작해 8분음표·8분쉼표, 엇박, 모르덴트와 앞꾸밈음, 점8분+16분, 박자 바뀜까지 50곡. 4/4 · 3/4 · 2/4 · 6/8 · 12/8. 조표는 E♭(♭3) 27곡 · A♭(♭4) 17곡, 35번 B♭·43번 D♭.',
      hint: '느리게, 소리보다 눈이 먼저'
    },
    '중급': {
      desc: '100곡. 박자 전환과 3연음, 점8분+16분, 두 음 장식음과 모르덴트, 임시표, 조바꿈, 5/8·7/8 변박. 51~60 박자 전환 첫걸음(곡당 4구간) → 61~90 점8분·복합박·첫 조바꿈 → 91~110 빠른 템포·변박 첫 등장 → 111~130 조바꿈과 셋잇단 → 131~150 네 박자 종합(곡당 3.9구간). 조표는 E♭ 42 · A♭ 27 · B♭ 17 · D♭ 12 · F 2.',
      hint: '박이 바뀌는 지점을 미리 표시하며'
    },
    '고급': {
      desc: '50곡. 5/8 · 7/8 · 12/8의 복합 박자, 잦은 박자·조 변화, 트릴과 윗·아랫모르덴트, 16분과 셋잇단 교차, subito p. 151~160 박자 전환이 가장 잦은 구간(곡당 4.8구간) → 161~180 변박과 잦은 변화 → 181~190 조표 확장 → 191~200 실전 초견.',
      hint: '덩어리로 보고, 방향 전환을 예상하며'
    }
  };

  const ROADMAP = [
    {
      part: '1부', title: '기초', sub: '1~50 · 한 마디씩 눈으로 읽는 힘',
      blocks: [
        { range: '1~10', head: '음표 하나에서 시작', text: '온음표·2분음표 → 점2분음표·4분음표 → 4분쉼표·점4분음표 → 8분음표와 슬러. 4/4·3/4·6/8·12/8. 조표는 E♭(1~7번) → A♭(8~10번).', done: true },
        { range: '11~20', head: '8분음표의 확장', text: '8분음표 두 개·네 개 잇기, 8분쉼표, 3/4·6/8·2/4·12/8의 8분음표 흐름, 마디를 넘는 붙임줄. 음역 A3~G5.', done: true },
        { range: '21~30', head: '엇박과 시김새', text: '4분쉼표로 만드는 엇박, 8분음표 연속, 긴 음의 모르덴트와 한 음 앞꾸밈음. 조표 E♭·A♭.', done: true },
        { range: '31~40', head: '점8분+16분', text: '긴 음과 짧은 음의 대비, 점8분음표+16분음표 짝, 프레이즈 첫 음 당김활. 35번에서 B♭(♭2) 첫 만남.', done: true },
        { range: '41~50', head: '기초 종합', text: '한 곡에 한 번 박자 바뀜(3/4→6/8·4/4→3/4·2/4→4/4), 43번 D♭(♭5), 엇박과 점8분을 모은 마무리.', done: true }
      ]
    },
    {
      part: '2부', title: '중급', sub: '51~150 · 박자가 흔들리는 악보를 버티는 힘 · 100곡',
      blocks: [
        { range: '51~70', head: '박자 전환과 3연음', text: '51~60은 4/4·3/4·2/4·6/8·9/8·12/8을 곡당 4구간으로 넓게 오가며 박자 전환을 처음 만난다. 61~70은 3/4·6/8·9/8·12/8 기본기에 두 음 장식음·모르덴트·넓은 도약을 얹고 첫 조바꿈을 넣는다(곡당 2.8구간). 조표는 E♭·A♭에서 B♭·D♭으로.', done: true },
        { range: '71~90', head: '점8분과 복합박', text: '점8분+16분, 12/8와 6/8 오가기, 16분 연속, 한 곡 두 번의 조바꿈, 3/4와 2/4의 대비. 박자 구간이 2.9~3.0개로 늘어난다.', done: true },
        { range: '91~110', head: '넓은 도약과 변박 첫 등장', text: '빠른 템포(♩=100~104), 5/8·7/8 첫 등장, F(♭1) 첫 만남, 복합박 세 가지 엮기. 곡당 3.0~3.2구간.', done: true },
        { range: '111~130', head: '조바꿈·셋잇단·변박의 결', text: '조바꿈 두 번, 4/4의 셋잇단, 5/8와 7/8의 교차, 3/4·2/4 오가기, 12/8의 조바꿈. 곡당 3.3~3.4구간으로 박자 전환이 촘촘해진다.', done: true },
        { range: '131~150', head: '중급 종합', text: '곡마다 3~4개의 박자를 한 곡에 모으고(곡당 3.9구간) 조바꿈·빠른 템포·16분·시김새를 함께 쓴다. 여기까지가 중급 100곡.', done: true }
      ]
    },
    {
      part: '3부', title: '고급', sub: '151~200 · 처음 보는 악보를 즉시 통과하는 힘 · 50곡',
      blocks: [
        { range: '151~160', head: '복합 박자와 조바꿈', text: '5/8·7/8·12/8·6/8·4/4·3/4의 잦은 전환(곡당 4.8구간으로 전곡에서 가장 잦다), 트릴, subito p, 조바꿈. 조표는 E♭에서 F(♭1)·G♭(♭6)까지.', done: true },
        { range: '161~180', head: '변박과 잦은 변화', text: '3~4회 박자 변화, 16분과 셋잇단 교차, 넓은 음역 도약, 한 곡 두 번 조바꿈. 윗·아랫모르덴트를 섞어 쓴다.', done: true },
        { range: '181~190', head: '조표 확장', text: 'D♭·F·G♭의 겹변박, 조바꿈과 변박의 결합, 5/8에서 12/8까지 한 곡에.', done: true },
        { range: '191~200', head: '실전 초견', text: '네 가지 박자를 한 곡에, G(♯1)·D(♯2) 조표, 200번까지 이어지는 종합 초견.', done: true }
      ]
    }
  ];

  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));

  const state = {
    level: '기초',
    list: [],
    index: 0,
    zoom: 1,
    fitW: 0,
    fs: false,
    fsNative: false,
    fsExitAt: 0,
    dragging: false
  };

  const pieces = (window.PIECES || []).slice().sort((a, b) => a.no - b.no);

  function levelPieces(level) {
    return pieces.filter(p => p.level === level);
  }

  function meterText(p) {
    return p.meters.join(' → ');
  }

  function tempoText(p) {
    const t = p.tempos || [];
    if (!t.length) return '';
    // 8분의 8 박자(6/8·9/8·12/8·5/8·7/8)는 점4분음표가 한 박 — ♩. 로 적는다
    const beat = p.meters.every(m => /\/8$/.test(m)) ? '♩.' : '♩';
    // 곡 중 템포가 바뀌면 첫 템포만 보여 주지 말고 전부 적는다 (예: ♩ = 80 → 63 → 84 → 72)
    return beat + ' = ' + t.join(' → ');
  }

  /* ---------------- render ---------------- */
  function renderStats() {
    const bars = pieces.map(p => p.bars).filter(Boolean);
    const staggers = pieces.map(p => (p.lines ? p.lines.length : 0)).filter(Boolean);
    const barText = bars.length
      ? (Math.min(...bars) === Math.max(...bars) ? `${Math.min(...bars)}` : `${Math.min(...bars)}~${Math.max(...bars)}`)
      : '35~56';
    const sysText = staggers.length
      ? (Math.min(...staggers) === Math.max(...staggers) ? `${Math.min(...staggers)}` : `${Math.min(...staggers)}~${Math.max(...staggers)}`)
      : '7';
    const keyOrder = ['E♭', 'A♭', 'B♭', 'D♭', 'F', 'G♭', 'G', 'D'];
    const kc = {};
    pieces.forEach(p => { if (p.key) kc[p.key] = (kc[p.key] || 0) + 1; });
    const keyText = keyOrder.filter(k => kc[k]).map(k => `${k} ${kc[k]}`).join(' · ') || 'E♭·A♭·B♭·D♭·F·G♭';    $('#heroStats').innerHTML = [
      `<span class="stat"><b>${pieces.length}</b>곡 공개</span>`,
      `<span class="stat"><b>${barText}</b>마디 · <b>${sysText}</b>단</span>`,
      `<span class="stat">음역 <b>A3~C6</b></span>`,
      `<span class="stat">조표 <b>${keyText}</b></span>`
    ].join('');
  }

  function render() {
    const lv = LEVELS[state.level];
    $('#levelTitle').textContent = state.level;
    $('#levelDesc').textContent = lv.desc;
    state.list = levelPieces(state.level);

    const grid = $('#grid');
    grid.innerHTML = state.list.map((p, i) => `
      <article class="card" data-i="${i}">
        <div class="card-body top">
          <div class="card-head">
            <div class="no">${p.no}</div>
            <div class="card-title">${p.title}</div>
          </div>
        </div>
        <button class="thumb" data-open="${i}" aria-label="${p.no}번 ${p.title} 악보 보기">
          <img src="${p.thumb}" alt="" loading="lazy" decoding="async">
          <span class="zoomhint">눌러서 크게 보기</span>
        </button>
        <div class="card-body">
          <div class="badges">
            <span class="badge key">${p.key}</span>
            <span class="badge meter">${meterText(p)}</span>
            <span class="badge">${tempoText(p)}</span>
          </div>
          <div class="card-actions">
            <button class="btn" data-open="${i}">악보 보기</button>
            <a class="btn ghost" href="${p.pdf}" target="_blank" rel="noopener">PDF</a>
          </div>
        </div>
      </article>`).join('');

    $$('[data-open]', grid).forEach(btn => {
      btn.addEventListener('click', () => openModal(Number(btn.dataset.open)));
    });
  }

  function renderRoadmap() {
    $('#roadmap').innerHTML = ROADMAP.map(part => `
      <div class="part">
        <h3>${part.part} · ${part.title}</h3>
        <p class="part-sub">${part.sub}</p>
        ${part.blocks.map(b => `
          <div class="block ${b.done ? 'done' : ''}">
            <div class="blk-head">
              <b>${b.head}</b>
              <span class="range">${b.range}</span>
            </div>
            <p>${b.text} ${b.done
              ? '<span class="status done">공개</span>'
              : '<span class="status soon">준비 중</span>'}</p>
          </div>`).join('')}
      </div>`).join('');
  }

  /* ---------------- modal ---------------- */
  const modal = $('#modal');
  const stage = $('#stage');
  const img = $('#mImg');

  function openModal(i) {
    if (!state.list.length) return;
    state.index = (i + state.list.length) % state.list.length;
    const p = state.list[state.index];
    $('#mNo').textContent = p.no;
    $('#mTitle').textContent = p.title;
    $('#mMeta').textContent = [
      p.level, p.key, meterText(p), tempoText(p),
      (p.bars ? p.bars + '마디' : ''),
      (p.lines ? p.lines.length + '단' + (new Set(p.lines).size > 1
        ? ' (' + p.lines.join('·') + '마디)' : '') : ''),
      p.focus || ''
    ].filter(Boolean).join(' · ');
    $('#mPdf').href = p.pdf;
    $('#mPrint').href = p.pdf;
    const posText = `${state.index + 1} / ${state.list.length}`;
    const posA = $('#mPos'); if (posA) posA.textContent = posText;
    const posB = $('#mPosF'); if (posB) posB.textContent = posText;
    $('#mLoading').classList.remove('is-hidden');
    img.style.width = '';
    img.removeAttribute('src');
    img.alt = `${p.no}번 ${p.title} 악보`;
    const onLoaded = () => {
      $('#mLoading').classList.add('is-hidden');
      setZoom(1, true);
      stage.scrollTop = 0;
      stage.scrollLeft = 0;
    };
    img.onload = onLoaded;
    img.src = p.image;
    if (img.complete && img.naturalWidth) onLoaded();
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    if (window.LoungePlayer) window.LoungePlayer.open(p);
  }

  function closeModal() {
    if (window.LoungePlayer) window.LoungePlayer.close();
    if (state.fs) exitFs(false);
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    img.removeAttribute('src');
  }

  function stageWidth() {
    return Math.max(240, stage.clientWidth - 36);
  }

  function applyZoom() {
    if (!img.naturalWidth) return;
    const availW = Math.max(240, stage.clientWidth - 36);
    let w;
    if (state.fs) {
      const availH = Math.max(160, stage.clientHeight - 36);
      const ratio = img.naturalWidth / img.naturalHeight;
      w = Math.min(availW, availH * ratio) * state.zoom;
    } else {
      w = availW * state.zoom;
    }
    img.style.width = Math.round(w) + 'px';
    $('#zLevel').textContent = Math.round(state.zoom * 100) + '%';
    if (window.LoungePlayer) window.LoungePlayer.syncGeometry();
  }

  function setZoom(z, reset) {
    state.zoom = Math.min(6, Math.max(0.4, z));
    if (reset) state.zoom = 1;
    applyZoom();
  }

  $('#zIn').addEventListener('click', () => setZoom(state.zoom * 1.25));
  $('#zOut').addEventListener('click', () => setZoom(state.zoom / 1.25));
  $('#zFit').addEventListener('click', () => setZoom(1, true));
  $('#mClose').addEventListener('click', closeModal);

  /* ---------------- 전체 화면 ---------------- */
  const fsBtn = $('#fsBtn');

  function fsActive() {
    return !!(document.fullscreenElement === modal ||
              document.webkitFullscreenElement === modal ||
              modal.classList.contains('is-fs'));
  }

  function setFsUI(on) {
    fsBtn.textContent = on ? '전체 화면 종료' : '전체 화면';
    fsBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  function enterFs() {
    state.fs = true;
    modal.classList.add('is-fs');
    setFsUI(true);
    const req = modal.requestFullscreen || modal.webkitRequestFullscreen;
    if (req) {
      state.fsNative = true;
      try {
        const p = req.call(modal, { navigationUI: 'hide' });
        if (p && p.catch) p.catch(() => {});
      } catch (e) { /* iPadOS Safari 등: CSS 전체 화면으로 대신 */ }
    }
    setZoom(1, true);
  }

  function exitFs(restoreZoom) {
    state.fs = false;
    modal.classList.remove('is-fs');
    setFsUI(false);
    state.fsExitAt = Date.now();
    if (document.fullscreenElement && document.exitFullscreen) {
      try { const p = document.exitFullscreen(); if (p && p.catch) p.catch(() => {}); } catch (e) {}
    } else if (document.webkitFullscreenElement && document.webkitExitFullscreen) {
      try { document.webkitExitFullscreen(); } catch (e) {}
    }
    state.fsNative = false;
    if (restoreZoom !== false) setZoom(1, true);
  }

  fsBtn.addEventListener('click', () => {
    if (fsActive()) exitFs(); else enterFs();
  });

  function onFsChange() {
    const native = document.fullscreenElement === modal ||
                   document.webkitFullscreenElement === modal;
    if (!native && state.fs && state.fsNative) {
      // 사용자가 Esc/브라우저 버튼으로 나간 경우
      exitFs();
    } else if (native) {
      applyZoom();   // 전체화면 크기가 잡힌 뒤 한 장이 화면에 맞게
    }
  }
  document.addEventListener('fullscreenchange', onFsChange);
  document.addEventListener('webkitfullscreenchange', onFsChange);

  $('#prevBtn').addEventListener('click', () => openModal(state.index - 1));
  $('#nextBtn').addEventListener('click', () => openModal(state.index + 1));
  $('#prevBtnF').addEventListener('click', () => openModal(state.index - 1));
  $('#nextBtnF').addEventListener('click', () => openModal(state.index + 1));

  stage.addEventListener('wheel', (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    setZoom(state.zoom * (e.deltaY < 0 ? 1.12 : 0.89));
  }, { passive: false });

  img.addEventListener('dblclick', () => setZoom(state.zoom > 1.05 ? 1 : 2, state.zoom > 1.05));

  // drag to pan
  let drag = null;
  stage.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    if (stage.scrollWidth <= stage.clientWidth + 4) return;
    drag = { x: e.clientX, y: e.clientY, sl: stage.scrollLeft, st: stage.scrollTop };
    img.classList.add('dragging');
  });
  window.addEventListener('pointermove', (e) => {
    if (!drag) return;
    stage.scrollLeft = drag.sl - (e.clientX - drag.x);
    stage.scrollTop = drag.st - (e.clientY - drag.y);
  });
  window.addEventListener('pointerup', () => {
    drag = null; img.classList.remove('dragging');
  });

  // pinch zoom
  let pinch = null;
  stage.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) {
      pinch = { d: dist(e.touches), z: state.zoom };
    }
  }, { passive: true });  stage.addEventListener('touchmove', (e) => {
    if (pinch && e.touches.length === 2) {
      e.preventDefault();
      setZoom(pinch.z * (dist(e.touches) / pinch.d));
    }
  }, { passive: false });
  stage.addEventListener('touchend', () => { pinch = null; }, { passive: true });

  /* ---------------- 좌우 스와이프로 이전/다음 곡 ---------------- */
  // 사진을 넘기듯 악보를 넘긴다. 한 손가락이고, 악보가 가로로 넘치지 않고(확대 전),
  // 가로 이동이 세로 이동보다 뚜렷할 때만 넘긴다 (핀치·패닝·세로 스크롤과 엮이지 않게).
  let swipe = null;
  const SWIPE_MIN = 65;              // 최소 가로 이동(px)
  const SWIPE_RATIO = 1.8;           // 세로 이동 대비 가로 이동 배율

  function swipeBlocked() {
    if (window.LoungePlayer && window.LoungePlayer.examActive && window.LoungePlayer.examActive()) return true;
    return stage.scrollWidth > stage.clientWidth + 4;   // 확대돼 가로 스크롤이 되면 패닝이 우선
  }

  stage.addEventListener('touchstart', (e) => {
    swipe = null;
    if (e.touches.length !== 1) return;
    if (swipeBlocked()) return;
    const t = e.touches[0];
    swipe = { x: t.clientX, y: t.clientY, done: false };
  }, { passive: true });

  stage.addEventListener('touchmove', (e) => {
    if (!swipe || swipe.done || e.touches.length !== 1) return;
    const t = e.touches[0];
    const dx = t.clientX - swipe.x;
    const dy = t.clientY - swipe.y;
    if (Math.abs(dx) >= SWIPE_MIN && Math.abs(dx) > Math.abs(dy) * SWIPE_RATIO) {
      swipe.done = true;
      if (dx < 0) openModal(state.index + 1);   // 왼쪽으로 → 다음 곡
      else openModal(state.index - 1);          // 오른쪽으로 → 이전 곡
    }
  }, { passive: true });

  stage.addEventListener('touchend', () => { swipe = null; }, { passive: true });
  stage.addEventListener('touchcancel', () => { swipe = null; }, { passive: true });
  function dist(t) {
    const dx = t[0].clientX - t[1].clientX, dy = t[0].clientY - t[1].clientY;
    return Math.hypot(dx, dy) || 1;
  }

  window.addEventListener('keydown', (e) => {
    if (!modal.classList.contains('is-open')) return;
    if (e.key === 'Escape') {
      if (state.fs) {
        if (Date.now() - state.fsExitAt < 350) return;   // 네이티브 전체화면 종료와 겹침
        exitFs();
      } else if (Date.now() - state.fsExitAt >= 350) {
        closeModal();
      }
      return;
    }
    if (e.key === 'ArrowLeft') openModal(state.index - 1);
    if (e.key === 'ArrowRight') openModal(state.index + 1);
    if (e.key === '+' || e.key === '=') setZoom(state.zoom * 1.25);
    if (e.key === '-') setZoom(state.zoom / 1.25);
    if (e.key === 'f' || e.key === 'F') {
      if (fsActive()) exitFs(); else enterFs();
    }
  });

  window.addEventListener('resize', () => {
    if (modal.classList.contains('is-open')) applyZoom();
  });

  /* ---------------- 보기 전환 (악보 / 자료) ---------------- */
  const views = { scores: $('#viewScores'), docs: $('#viewDocs') };
  const levelTabs = $('#tabs');

  function showView(name) {
    if (!views[name]) name = 'scores';
    Object.entries(views).forEach(([k, el]) => {
      if (!el) return;
      el.classList.toggle('is-hidden', k !== name);
    });
    if (levelTabs) levelTabs.classList.toggle('is-hidden', name !== 'scores');
    const examRow = document.querySelector('#examRow');
    if (examRow) examRow.classList.toggle('is-hidden', name !== 'scores');
    $$('.vtab').forEach(t => t.classList.toggle('is-active', t.dataset.view === name));
    document.body.dataset.view = name;
    if (name === 'scores') render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (history.replaceState) history.replaceState(null, '', name === 'docs' ? '#docs' : '#scores');
  }

  $$('.vtab').forEach(t => t.addEventListener('click', () => showView(t.dataset.view)));
  if (location.hash === '#docs') showView('docs');
  window.addEventListener('hashchange', () => {
    showView(location.hash === '#docs' ? 'docs' : 'scores');
  });

  /* ---------------- tabs ---------------- */
  $$('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.tab').forEach(t => t.classList.remove('is-active'));
      tab.classList.add('is-active');
      state.level = tab.dataset.level;
      render();
      syncExamNote();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });

  /* ---------------- 실전 테스트 (랜덤 출제) ---------------- */
  const examRow = document.querySelector('#examRow');
  const examScope = document.querySelector('#examScope');
  const examNote = document.querySelector('#examNote');

  function examPool() {
    return (examScope && examScope.value === 'all') ? pieces.slice() : levelPieces(state.level);
  }

  function syncExamNote() {
    if (!examNote) return;
    const n = examPool().length;
    const where = examScope && examScope.value === 'all' ? '전체' : state.level;
    examNote.textContent = `30초 읽고, 소리·마디 표시 없이 제한 시간 안에 연주 · ${where} ${n}곡 중 뽑기`;
  }

  function openPieceByNo(no) {
    const p = pieces.find((x) => x.no === no);
    if (!p) return false;
    if (p.level !== state.level) {
      state.level = p.level;
      $$('.tab').forEach((t) => t.classList.toggle('is-active', t.dataset.level === p.level));
      render();
      syncExamNote();
    }
    const i = state.list.findIndex((x) => x.no === no);
    if (i < 0) return false;
    openModal(i);
    return true;
  }

  function startExamRandom(excludeNo) {
    let pool = examPool();
    if (excludeNo != null && pool.length > 1) pool = pool.filter((p) => p.no !== excludeNo);
    if (!pool.length) return;
    const p = pool[Math.floor(Math.random() * pool.length)];
    if (!openPieceByNo(p.no)) return;
    if (window.LoungePlayer && window.LoungePlayer.startExam) window.LoungePlayer.startExam();
  }

  const examStartBtn = document.querySelector('#examStart');
  if (examStartBtn) examStartBtn.addEventListener('click', () => startExamRandom());
  if (examScope) examScope.addEventListener('change', syncExamNote);
  syncExamNote();

  /* 다른 화면·도구에서 쓰는 최소 인터페이스 */
  window.LoungeApp = {
    openPieceByNo,
    startExamRandom,
    examPool: () => examPool().map((p) => p.no)
  };

  renderStats();
  render();
  renderRoadmap();
})();
