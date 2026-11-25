/* 해금 초견 라운지 */
(function () {
  const LEVELS = {
    '기초': {
      desc: '순차 진행과 3도·4도 도약, 기본 슬러와 스타카토, 한 음 장식음. 4/4 · 3/4 · 2/4 · 6/8 · 12/8.',
      hint: '느리게, 소리보다 눈이 먼저'
    },
    '중급': {
      desc: '박자 전환과 3연음, 점8분+16분, 두 음 장식음과 농현, 임시표, 세 곡의 조바꿈.',
      hint: '박이 바뀌는 지점을 미리 표시하며'
    },
    '고급': {
      desc: '5/8 · 7/8 · 12/8의 복합 박자, 잦은 박자 변화, 트릴과 2~3음 장식음, subito p, 조바꿈.',
      hint: '덩어리로 보고, 방향 전환을 예상하며'
    }
  };

  const ROADMAP = [
    {
      part: '1부', title: '기초', sub: '1~50 · 한 마디씩 눈으로 읽는 힘',
      blocks: [
        { range: '1~10', head: '조성과 박자의 기본', text: 'E♭·B♭·F·A♭, 4/4·3/4·2/4·6/8·12/8. 순차 진행, 3도 도약, 기본 슬러·스타카토, 한 음 장식음.', done: true },
        { range: '11~20', head: '8분·16분의 확장', text: '16분 음표 연결, 붙임줄, 당김음의 첫걸음, 셋잇단의 기초, 두 옥타브 안의 음역.' },
        { range: '21~30', head: '복합 박자 첫 만남', text: '9/8과 5/8, 조표 3~4개, 농현과 퇴성의 기본 표기.' },
        { range: '31~40', head: '프레이즈와 호흡', text: '네 마디 프레이즈, 여섯잇단, 이명동음 읽기, 쉼표로 나누는 호흡.' },
        { range: '41~50', head: '기초 종합', text: '짧은 조바꿈, 셈여림의 폭, 초견 속도 훈련.' }
      ]
    },
    {
      part: '2부', title: '중급', sub: '51~100 · 박자가 흔들리는 악보를 버티는 힘',
      blocks: [
        { range: '51~60', head: '박자 전환과 3연음', text: '4/4·3/4·2/4·6/8·9/8·12/8 전환, 넓은 도약, 두 음 장식음, 농현, 세 곡의 조바꿈.', done: true },
        { range: '61~70', head: '비대칭 박자', text: '5/8과 7/8의 묶음 감각, 엇박 쉼표, 16분 연결.' },
        { range: '71~80', head: '꾸밈음과 반음계', text: '2~3음 장식음, 트릴의 기초, 반음계적 진행과 임시표 정리.' },
        { range: '81~90', head: '조바꿈 두 번', text: '한 곡 안의 두 번 조바꿈, 빠른 템포, 리듬 변형.' },
        { range: '91~100', head: '중급 종합', text: '실내악 악보 발췌 수준의 리듬과 셈여림.' }
      ]
    },
    {
      part: '3부', title: '고급', sub: '101~150 · 처음 보는 악보를 즉시 통과하는 힘',
      blocks: [
        { range: '101~110', head: '복합 박자와 조바꿈', text: '5/8·7/8·12/8·6/8·4/4·3/4의 잦은 전환, 트릴, subito p, 조바꿈.', done: true },
        { range: '111~120', head: '잦은 변화', text: '3~4회 박자 변화, 잦은 임시표, 넓은 음역 도약.' },
        { range: '121~130', head: '자유 리듬', text: '무박자·카덴차적 프레이즈, 지시어 읽기.' },
        { range: '131~140', head: '창작 초견', text: '현대 국악 어법, 특수 주법 표기, 비정형 리듬.' },
        { range: '141~150', head: '실전 모의 초견', text: '오케스트라 발췌 형식, 시간 제한 초견.' }
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
    const first = p.tempos[0];
    return '♩ = ' + first;
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
    $('#heroStats').innerHTML = [
      `<span class="stat"><b>${pieces.length}</b>곡 공개</span>`,
      `<span class="stat"><b>${barText}</b>마디 · <b>${sysText}</b>단</span>`,
      `<span class="stat">음역 <b>A3~C6</b></span>`,
      `<span class="stat">조표 <b>E♭·B♭·A♭·F·D♭</b></span>`
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
      p.level, p.key, meterText(p),
      (p.bars ? p.bars + '마디' : ''),
      (p.lines ? p.lines.length + '단' + (new Set(p.lines).size > 1
        ? ' (' + p.lines.join('·') + '마디)' : '') : '')
    ].filter(Boolean).join(' · ');
    $('#mPdf').href = p.pdf;
    $('#mPrint').href = p.pdf;
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
    $('#prevBtn').disabled = false;
    $('#nextBtn').disabled = false;
  }

  function closeModal() {
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
  }, { passive: true });
  stage.addEventListener('touchmove', (e) => {
    if (pinch && e.touches.length === 2) {
      e.preventDefault();
      setZoom(pinch.z * (dist(e.touches) / pinch.d));
    }
  }, { passive: false });
  stage.addEventListener('touchend', () => { pinch = null; }, { passive: true });
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

  /* ---------------- tabs ---------------- */
  $$('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.tab').forEach(t => t.classList.remove('is-active'));
      tab.classList.add('is-active');
      state.level = tab.dataset.level;
      render();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });

  renderStats();
  render();
  renderRoadmap();
})();
