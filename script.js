const DATA_SOURCES = {
  hip: './output/hip_provincial.json', knee: './output/knee_provincial.json',
  hipRegional: './output/hip_regional.json', kneeRegional: './output/knee_regional.json',
};
const ZONE_CARD_SELECTOR = (zone) => `.zone-card.${zone}`;
const ns = 'http://www.w3.org/2000/svg';

function el(tag, attrs) {
  const e = document.createElementNS(ns, tag);
  Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
  return e;
}

async function loadDatasets() {
  const [hip, knee, hipRegional, kneeRegional] = await Promise.all([
    fetch(DATA_SOURCES.hip).then((r) => r.json()),
    fetch(DATA_SOURCES.knee).then((r) => r.json()),
    fetch(DATA_SOURCES.hipRegional).then((r) => r.json()),
    fetch(DATA_SOURCES.kneeRegional).then((r) => r.json()),
  ]);
  return { hip, knee, hipRegional, kneeRegional };
}

function init(datasets) {
  const state = {
    procedure: 'hip',
    year: null,
    province: null,
    showReferenceContext: true,
  };

  const svg = document.getElementById('chart');
  const tooltip = document.getElementById('tooltip');
  const chartPanel = document.querySelector('.chart-panel');
  const toggleButton = document.getElementById('referenceToggle');
  const procedureToggle = document.getElementById('procedureToggle');
  const yearTabs = document.getElementById('yearTabs');
  const provinceTabs = document.getElementById('provinceTabs');
  const zonesContainer = document.querySelector('.zones');

  function years() {
    return Object.keys(datasets[state.procedure].years).sort((a, b) => Number(a) - Number(b));
  }

  function currentPayload() {
    return datasets[state.procedure].years[state.year];
  }

  function currentRegionalPayload() {
    if (!state.province) return null;
    const key = state.procedure === 'hip' ? 'hipRegional' : 'kneeRegional';
    const yearBlock = datasets[key].years[state.year];
    return (yearBlock && yearBlock[state.province]) || null;
  }

  function buildProcedureToggle() {
    procedureToggle.querySelectorAll('.seg-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.procedure === state.procedure);
      btn.onclick = () => {
        state.procedure = btn.dataset.procedure;
        if (!years().includes(state.year)) state.year = years()[years().length - 1];
        render();
      };
    });
  }

  function buildYearTabs() {
    yearTabs.innerHTML = '';
    years().forEach((y) => {
      const btn = document.createElement('button');
      btn.className = 'seg-btn' + (y === state.year ? ' active' : '');
      btn.textContent = y;
      btn.onclick = () => { state.year = y; render(); };
      yearTabs.appendChild(btn);
    });
  }

  function buildProvinceTabs() {
    const payload = currentPayload();
    const provinces = [...payload.hospitals].sort((a, b) => a.name.localeCompare(b.name));
    provinceTabs.innerHTML = '';
    provinces.forEach((p) => {
      const btn = document.createElement('button');
      btn.className = 'province-tab' + (p.name === state.province ? ' active' : '');
      btn.textContent = p.name;
      btn.setAttribute('role', 'tab');
      btn.onclick = () => {
        state.province = state.province === p.name ? null : p.name;
        render();
      };
      provinceTabs.appendChild(btn);
    });
  }

  function renderChart() {
    const regionalPayload = currentRegionalPayload();
    const inRegionMode = !!regionalPayload;
    const payload = inRegionMode ? regionalPayload : currentPayload();
    const hospitals = payload.hospitals;
    const summary = payload.summary;
    const chart = payload.meta.chart;

    const caption = document.getElementById('chartCaption');
    if (caption) {
      caption.textContent = inRegionMode
        ? `Showing ${hospitals.length} CIHI health region${hospitals.length === 1 ? '' : 's'} within ${state.province} — click ${state.province} again to return to the provincial view.`
        : '';
    }

    svg.innerHTML = '';
    const referenceContextElements = [];

    const margin = chart.margin;
    const plotW = chart.plotWidth;
    const plotH = chart.plotHeight;
    const capExtent = chart.capExtent;
    const demExtent = chart.demExtent;
    const medCapacity = summary.medianCapacity;
    const medDemand = summary.medianDemand;
    const W = chart.width;
    const H = chart.height;

    const zTL = el('rect', { x: margin.left, y: margin.top, width: (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (demExtent[1] - medDemand) / (demExtent[1] - demExtent[0]) * plotH, fill: '#F7ECEA' });
    const zTR = el('rect', { x: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y: margin.top, width: plotW - (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (demExtent[1] - medDemand) / (demExtent[1] - demExtent[0]) * plotH, fill: '#EDEFF5' });
    const zBL = el('rect', { x: margin.left, y: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, width: (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, fill: '#F5F1E7' });
    const zBR = el('rect', { x: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, width: plotW - (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, fill: '#EAF3F0' });
    [zTL, zTR, zBL, zBR].forEach((r) => {
      r.classList.add('reference-context');
      r.setAttribute('opacity', '0.55');
      referenceContextElements.push(r);
      svg.appendChild(r);
    });

    const capStep = (capExtent[1] - capExtent[0]) / 5;
    for (let i = 1; i < 5; i += 1) {
      const v = capExtent[0] + capStep * i;
      const x = margin.left + (v - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW;
      svg.appendChild(el('line', { class: 'gridline', x1: x, x2: x, y1: margin.top, y2: margin.top + plotH }));
      svg.appendChild(Object.assign(el('text', { class: 'axis-label', x, y: margin.top + plotH + 20, 'text-anchor': 'middle' }), { textContent: v.toFixed(0) }));
    }

    const demStep = (demExtent[1] - demExtent[0]) / 5;
    for (let i = 1; i < 5; i += 1) {
      const v = demExtent[0] + demStep * i;
      const y = margin.top + plotH - (v - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH;
      svg.appendChild(el('line', { class: 'gridline', x1: margin.left, x2: margin.left + plotW, y1: y, y2: y }));
      svg.appendChild(Object.assign(el('text', { class: 'axis-label', x: margin.left - 12, y: y + 4, 'text-anchor': 'end' }), { textContent: v.toFixed(1) }));
    }

    const xt = el('text', { class: 'axis-label', x: margin.left + plotW / 2, y: H - 14, 'text-anchor': 'middle' });
    xt.textContent = inRegionMode
      ? `CAPACITY — ${state.procedure} replacements completed (regional volume)`
      : `CAPACITY — ${state.procedure} replacements per 100k (65+)`;
    xt.style.fontWeight = 500;
    svg.appendChild(xt);

    const yt = el('text', { class: 'axis-label', x: -(margin.top + plotH / 2), y: 18, 'text-anchor': 'middle', transform: 'rotate(-90)' });
    yt.textContent = inRegionMode
      ? 'DEMAND — % NOT meeting wait-time benchmark'
      : 'DEMAND — YoY growth of 65+ population (%)';
    svg.appendChild(yt);

    const medianX = el('line', { class: 'median-line reference-context', x1: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, x2: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y1: margin.top, y2: margin.top + plotH });
    const medianY = el('line', { class: 'median-line reference-context', x1: margin.left, x2: margin.left + plotW, y1: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, y2: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH });
    const medianCapacityLabel = Object.assign(el('text', { class: 'median-label reference-context', x: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW + 5, y: margin.top + 12 }), { textContent: `median capacity (${medCapacity.toFixed(0)})` });
    const medianDemandLabel = Object.assign(el('text', { class: 'median-label reference-context', x: margin.left + 6, y: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH - 6 }), { textContent: `median demand (${medDemand.toFixed(inRegionMode ? 1 : 2)}%)` });
    [medianX, medianY, medianCapacityLabel, medianDemandLabel].forEach((node) => {
      referenceContextElements.push(node);
      svg.appendChild(node);
    });

    const zoneLabelTL = Object.assign(el('text', { class: 'zone-label reference-context', x: margin.left + 14, y: margin.top + 20, fill: '#B45309' }), { textContent: 'STRUCTURAL BOTTLENECK' });
    const zoneLabelTR = Object.assign(el('text', { class: 'zone-label reference-context', x: margin.left + plotW - 14, y: margin.top + 20, 'text-anchor': 'end', fill: '#3949AB' }), { textContent: 'PRESSURE COOKER' });
    const zoneLabelBL = Object.assign(el('text', { class: 'zone-label reference-context', x: margin.left + 14, y: margin.top + plotH - 12, fill: '#92702B' }), { textContent: 'LOW-CAPACITY EQUILIBRIUM' });
    const zoneLabelBR = Object.assign(el('text', { class: 'zone-label reference-context', x: margin.left + plotW - 14, y: margin.top + plotH - 12, 'text-anchor': 'end', fill: '#1F7A5C' }), { textContent: 'HAS SLACK' });
    [zoneLabelTL, zoneLabelTR, zoneLabelBL, zoneLabelBR].forEach((node) => {
      referenceContextElements.push(node);
      svg.appendChild(node);
    });

    hospitals.forEach((h) => {
      if (h.flagged) {
        svg.appendChild(el('circle', { class: 'flag-ring', cx: h.cx, cy: h.cy, r: h.radius + 5, 'stroke-width': 1.5 + h.flagIntensity * 3.5, 'stroke-dasharray': '2.5 2.5', opacity: 0.55 + 0.45 * h.flagIntensity }));
      }

      if (h.name === state.province) {
        svg.appendChild(el('circle', { class: 'select-ring', cx: h.cx, cy: h.cy, r: h.radius + 8 }));
      }

      const dot = el('circle', { class: 'dot' + (!inRegionMode && h.name === state.province ? ' selected' : ''), cx: h.cx, cy: h.cy, r: h.radius, fill: h.color });
      dot.addEventListener('mousemove', (e) => {
        const rect = chartPanel.getBoundingClientRect();
        tooltip.style.left = `${e.clientX - rect.left + 16}px`;
        tooltip.style.top = `${e.clientY - rect.top - 10}px`;
        tooltip.style.opacity = 1;
        const demandLine = inRegionMode
          ? `demand: ${h.demand.toFixed(1)}% not meeting benchmark (${h.demand > medDemand ? 'above' : 'below'} median)<br>`
          : `demand: ${h.demand.toFixed(2)}% pop. growth (${h.demand > medDemand ? 'above' : 'below'} median)<br>`;
        const capacityLine = inRegionMode
          ? `capacity: ${h.capacity.toFixed(0)} surgeries (${h.capacity > medCapacity ? 'above' : 'below'} median)<br>`
          : `capacity: ${h.capacity.toFixed(1)} / 100k (65+) (${h.capacity > medCapacity ? 'above' : 'below'} median)<br>`;
        tooltip.innerHTML = `<span class="t-name">${h.name}</span>
          ${capacityLine}
          ${demandLine}
          pressureIndex: ${h.pressureIndex.toFixed(4)}<br>
          wait P50: ${h.wait50}d (expected ${h.expected50.toFixed(0)}d)<br>
          residual P50: ${h.resid50 > 0 ? '+' : ''}${h.resid50.toFixed(0)}d<br>
          residual P90: ${h.resid90 > 0 ? '+' : ''}${h.resid90.toFixed(0)}d ${h.flagged ? '⚑' : ''}<br>
          % meeting benchmark: ${h.pctBenchmark != null ? h.pctBenchmark.toFixed(1) + '%' : 'n/a'}<br>
          volume: ${h.volume} / year`;
      });
      dot.addEventListener('mouseleave', () => { tooltip.style.opacity = 0; });
      if (!inRegionMode) {
        dot.addEventListener('click', () => {
          state.province = state.province === h.name ? null : h.name;
          render();
        });
      }
      svg.appendChild(dot);

      const label = el('text', { class: 'name-label', x: h.cx, y: h.cy - h.radius - 6, 'text-anchor': 'middle' });
      label.textContent = h.name.split(' ')[0];
      svg.appendChild(label);
    });

    referenceContextElements.forEach((node) => {
      node.style.display = state.showReferenceContext ? '' : 'none';
    });

    const worst = [...hospitals].sort((a, b) => b.resid50 - a.resid50)[0];
    const best = [...hospitals].sort((a, b) => a.resid50 - b.resid50)[0];
    document.getElementById('summaryStats').innerHTML = `
      <div class="stat-line"><span class="stat-name">${inRegionMode ? 'Regions shown' : 'Provinces shown'}</span><span class="stat-val">${summary.hospitalsShown}</span></div>
      <div class="stat-line"><span class="stat-name">Structural bottleneck zone</span><span class="stat-val">${summary.bottleneckCount}</span></div>
      <div class="stat-line"><span class="stat-name">Tail-flagged (P90)</span><span class="stat-val">${summary.flaggedCount}</span></div>
      <div class="stat-line"><span class="stat-name">Worst residual</span><span class="stat-val">${worst.name.split(' ')[0]} (+${worst.resid50.toFixed(0)}d)</span></div>
      <div class="stat-line"><span class="stat-name">Best residual</span><span class="stat-val">${best.name.split(' ')[0]} (${best.resid50.toFixed(0)}d)</span></div>
    `;
  }

  function applyZoneHighlight() {
    const payload = currentPayload();
    ['z1', 'z2', 'z3', 'z4'].forEach((z) => {
      const card = document.querySelector(ZONE_CARD_SELECTOR(z));
      if (card) card.classList.remove('active-zone');
    });
    if (!state.province) return;
    const hospital = payload.hospitals.find((h) => h.name === state.province);
    if (!hospital) return;
    const card = document.querySelector(ZONE_CARD_SELECTOR(hospital.zone));
    if (card) card.classList.add('active-zone');
  }

  function renderProvinceDetail() {
    const body = document.getElementById('provinceDetailBody');
    if (!state.province) {
      body.innerHTML = 'Click a province tab above to see its 2021–2025 wait-time trend.';
      return;
    }
    const yrs = years();
    const series = yrs
      .map((y) => {
        const payload = datasets[state.procedure].years[y];
        const h = payload.hospitals.find((r) => r.name === state.province);
        return h ? { year: y, wait50: h.wait50, wait90: h.wait90 } : null;
      })
      .filter(Boolean);

    const current = series.find((s) => s.year === state.year) || series[series.length - 1];
    const w = 210, h = 60, pad = 6;
    const allWaits = series.flatMap((s) => [s.wait50, s.wait90]);
    const lo = Math.min(...allWaits), hi = Math.max(...allWaits);
    const sx = (i) => pad + (i / (series.length - 1 || 1)) * (w - pad * 2);
    const sy = (v) => h - pad - (hi === lo ? 0.5 : (v - lo) / (hi - lo)) * (h - pad * 2);
    const path50 = series.map((s, i) => `${i === 0 ? 'M' : 'L'}${sx(i)},${sy(s.wait50)}`).join(' ');
    const path90 = series.map((s, i) => `${i === 0 ? 'M' : 'L'}${sx(i)},${sy(s.wait90)}`).join(' ');

    body.innerHTML = `
      <div class="detail-stat"><span class="k">Province</span><span class="v">${state.province}</span></div>
      <div class="detail-stat"><span class="k">Wait P50 (${current.year})</span><span class="v">${current.wait50}d</span></div>
      <div class="detail-stat"><span class="k">Wait P90 (${current.year})</span><span class="v">${current.wait90}d</span></div>
      <div class="sparkline-wrap">
        <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">
          <path d="${path50}" fill="none" stroke="var(--ink)" stroke-width="1.6"/>
          <path d="${path90}" fill="none" stroke="var(--flag)" stroke-width="1.4" stroke-dasharray="3 2"/>
        </svg>
        <div class="spark-legend">
          <span><span class="sw" style="background:var(--ink)"></span>P50</span>
          <span><span class="sw" style="background:var(--flag)"></span>P90</span>
          <span>${series[0].year}–${series[series.length - 1].year}</span>
        </div>
      </div>
    `;
  }

  function render() {
    buildProcedureToggle();
    buildYearTabs();
    buildProvinceTabs();
    renderChart();
    applyZoneHighlight();
    renderProvinceDetail();
    if (zonesContainer) zonesContainer.classList.toggle('is-hidden', !state.showReferenceContext);
  }

  toggleButton.addEventListener('click', () => {
    state.showReferenceContext = !state.showReferenceContext;
    toggleButton.classList.toggle('active', state.showReferenceContext);
    toggleButton.setAttribute('aria-pressed', String(state.showReferenceContext));
    const label = toggleButton.querySelector('.toggle-label');
    if (label) label.textContent = state.showReferenceContext ? 'Hide median reference context' : 'Show median reference context';
    render();
  });

  state.year = years()[years().length - 1];
  render();
}

loadDatasets().then(init).catch((error) => {
  console.error('Unable to render chart', error);
});
