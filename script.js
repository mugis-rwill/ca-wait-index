async function initChart() {
  const response = await fetch('./output/sample_output.json');
  const payload = await response.json();
  const hospitals = payload.hospitals;
  const summary = payload.summary;
  const chart = payload.meta.chart;

  const svg = document.getElementById('chart');
  const toggleButton = document.getElementById('referenceToggle');
  const zonesContainer = document.querySelector('.zones');
  const ns = 'http://www.w3.org/2000/svg';
  const referenceContextElements = [];
  let showReferenceContext = true;

  function el(tag, attrs) {
    const e = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
    return e;
  }

  const margin = chart.margin;
  const plotW = chart.plotWidth;
  const plotH = chart.plotHeight;
  const capExtent = chart.capExtent;
  const demExtent = chart.demExtent;
  const medCapacity = summary.medianCapacity;
  const medDemand = summary.medianDemand;
  const W = chart.width;
  const H = chart.height;

  const zTL = el('rect', { x: margin.left, y: margin.top, width: (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (chart.demExtent[1] - medDemand) / (demExtent[1] - demExtent[0]) * plotH, fill: '#F7ECEA' });
  const zTR = el('rect', { x: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y: margin.top, width: plotW - (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (chart.demExtent[1] - medDemand) / (demExtent[1] - demExtent[0]) * plotH, fill: '#EDEFF5' });
  const zBL = el('rect', { x: margin.left, y: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, width: (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, fill: '#F5F1E7' });
  const zBR = el('rect', { x: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, width: plotW - (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, height: (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, fill: '#EAF3F0' });
  [zTL, zTR, zBL, zBR].forEach((r) => {
    r.classList.add('reference-context');
    referenceContextElements.push(r);
  });
  [zTL, zTR, zBL, zBR].forEach((r) => {
    r.setAttribute('opacity', '0.55');
    svg.appendChild(r);
  });

  [300, 400, 500, 600, 700].forEach((v) => {
    if (v >= capExtent[0] && v <= capExtent[1]) {
      const x = margin.left + (v - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW;
      svg.appendChild(el('line', { class: 'gridline', x1: x, x2: x, y1: margin.top, y2: margin.top + plotH }));
      svg.appendChild(Object.assign(el('text', { class: 'axis-label', x, y: margin.top + plotH + 20, 'text-anchor': 'middle' }), { textContent: v }));
    }
  });

  [300, 400, 500, 600].forEach((v) => {
    if (v >= demExtent[0] && v <= demExtent[1]) {
      const y = margin.top + plotH - (v - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH;
      svg.appendChild(el('line', { class: 'gridline', x1: margin.left, x2: margin.left + plotW, y1: y, y2: y }));
      svg.appendChild(Object.assign(el('text', { class: 'axis-label', x: margin.left - 12, y: y + 4, 'text-anchor': 'end' }), { textContent: v }));
    }
  });

  const xt = el('text', { class: 'axis-label', x: margin.left + plotW / 2, y: H - 14, 'text-anchor': 'middle' });
  xt.textContent = 'CAPACITY — surgical throughput per 100k (65+)';
  xt.style.fontWeight = 500;
  svg.appendChild(xt);

  const yt = el('text', { class: 'axis-label', x: -(margin.top + plotH / 2), y: 18, 'text-anchor': 'middle', transform: 'rotate(-90)' });
  yt.textContent = 'DEMAND — referrals per 100k (65+)';
  svg.appendChild(yt);

  const lo = Math.max(capExtent[0], demExtent[0]);
  const hi = Math.min(capExtent[1], demExtent[1]);
  svg.appendChild(el('line', { class: 'equilibrium', x1: margin.left + (lo - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y1: margin.top + plotH - (lo - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, x2: margin.left + (hi - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y2: margin.top + plotH - (hi - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH }));
  svg.appendChild(Object.assign(el('text', { class: 'eq-label', x: margin.left + (hi - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW - 4, y: margin.top + plotH - (hi - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH - 8, 'text-anchor': 'end' }), { textContent: 'capacity = demand' }));

  const medianX = el('line', { class: 'median-line reference-context', x1: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, x2: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW, y1: margin.top, y2: margin.top + plotH });
  const medianY = el('line', { class: 'median-line reference-context', x1: margin.left, x2: margin.left + plotW, y1: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH, y2: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH });
  const medianCapacityLabel = Object.assign(el('text', { class: 'median-label reference-context', x: margin.left + (medCapacity - capExtent[0]) / (capExtent[1] - capExtent[0]) * plotW + 5, y: margin.top + 12 }), { textContent: `median capacity (${medCapacity})` });
  const medianDemandLabel = Object.assign(el('text', { class: 'median-label reference-context', x: margin.left + 6, y: margin.top + plotH - (medDemand - demExtent[0]) / (demExtent[1] - demExtent[0]) * plotH - 6 }), { textContent: `median demand (${medDemand})` });
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

  const tooltip = document.getElementById('tooltip');
  const chartPanel = document.querySelector('.chart-panel');

  hospitals.forEach((h) => {
    if (h.flagged) {
      svg.appendChild(el('circle', { class: 'flag-ring', cx: h.cx, cy: h.cy, r: h.radius + 5, 'stroke-width': 1.5 + h.flagIntensity * 3.5, 'stroke-dasharray': '2.5 2.5', opacity: 0.55 + 0.45 * h.flagIntensity }));
    }

    const dot = el('circle', { class: 'dot', cx: h.cx, cy: h.cy, r: h.radius, fill: h.color });
    dot.addEventListener('mousemove', (e) => {
      const rect = chartPanel.getBoundingClientRect();
      tooltip.style.left = `${e.clientX - rect.left + 16}px`;
      tooltip.style.top = `${e.clientY - rect.top - 10}px`;
      tooltip.style.opacity = 1;
      tooltip.innerHTML = `<span class="t-name">${h.name}</span>
        capacity: ${h.capacity} / 100k (${h.capacity > medCapacity ? 'above' : 'below'} median)<br>
        demand: ${h.demand} / 100k (${h.demand > medDemand ? 'above' : 'below'} median)<br>
        utilization: ${h.utilization.toFixed(2)}<br>
        wait P50: ${h.wait50}d (expected ${h.expected50.toFixed(0)}d)<br>
        residual P50: ${h.resid50 > 0 ? '+' : ''}${h.resid50.toFixed(0)}d<br>
        residual P90: ${h.resid90 > 0 ? '+' : ''}${h.resid90.toFixed(0)}d ${h.flagged ? '⚑' : ''}<br>
        volume: ${h.volume} / quarter`;
    });
    dot.addEventListener('mouseleave', () => {
      tooltip.style.opacity = 0;
    });
    svg.appendChild(dot);

    const label = el('text', { class: 'name-label', x: h.cx, y: h.cy - h.radius - 6, 'text-anchor': 'middle' });
    label.textContent = h.name.split(' ')[0];
    svg.appendChild(label);
  });

  function applyReferenceContextVisibility() {
    const shouldShow = showReferenceContext;
    referenceContextElements.forEach((node) => {
      node.style.display = shouldShow ? '' : 'none';
    });
    if (zonesContainer) {
      zonesContainer.classList.toggle('is-hidden', !shouldShow);
    }
    if (toggleButton) {
      toggleButton.classList.toggle('active', shouldShow);
      toggleButton.setAttribute('aria-pressed', String(shouldShow));
      const label = toggleButton.querySelector('.toggle-label');
      if (label) {
        label.textContent = shouldShow ? 'Hide median reference context' : 'Show median reference context';
      }
    }
  }

  if (toggleButton) {
    toggleButton.addEventListener('click', () => {
      showReferenceContext = !showReferenceContext;
      applyReferenceContextVisibility();
    });
  }

  applyReferenceContextVisibility();

  const worst = [...hospitals].sort((a, b) => b.resid50 - a.resid50)[0];
  const best = [...hospitals].sort((a, b) => a.resid50 - b.resid50)[0];
  document.getElementById('summaryStats').innerHTML = `
    <div class="stat-line"><span class="stat-name">Hospitals shown</span><span class="stat-val">${summary.hospitalsShown}</span></div>
    <div class="stat-line"><span class="stat-name">Structural bottleneck zone</span><span class="stat-val">${summary.bottleneckCount}</span></div>
    <div class="stat-line"><span class="stat-name">Tail-flagged (P90)</span><span class="stat-val">${summary.flaggedCount}</span></div>
    <div class="stat-line"><span class="stat-name">Worst residual</span><span class="stat-val">${worst.name.split(' ')[0]} (+${worst.resid50.toFixed(0)}d)</span></div>
    <div class="stat-line"><span class="stat-name">Best residual</span><span class="stat-val">${best.name.split(' ')[0]} (${best.resid50.toFixed(0)}d)</span></div>
  `;
}

initChart().catch((error) => {
  console.error('Unable to render chart', error);
});
