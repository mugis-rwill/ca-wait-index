const syntheticPatients = [
  { name: 'Patient 001', diagnosis: '2025-01-08', surgery: '2025-07-14', ageGroup: '50-60' },
  { name: 'Patient 002', diagnosis: '2025-02-23', surgery: '2025-09-12', ageGroup: '61-70' },
  { name: 'Patient 003', diagnosis: '2025-03-18', surgery: '2025-09-05', ageGroup: '71+' },
  { name: 'Patient 004', diagnosis: '2025-04-01', surgery: '2025-08-22', ageGroup: '50-60' },
  { name: 'Patient 005', diagnosis: '2025-05-15', surgery: '2025-12-04', ageGroup: '61-70' },
  { name: 'Patient 006', diagnosis: '2025-06-20', surgery: '2025-10-28', ageGroup: '71+' },
  { name: 'Patient 007', diagnosis: '2025-07-04', surgery: '2025-11-10', ageGroup: '50-60' },
  { name: 'Patient 008', diagnosis: '2025-08-29', surgery: '2025-12-22', ageGroup: '61-70' }
];

const benchmarkDays = 182;

function parseDate(dateString) {
  return new Date(dateString);
}

function daysBetween(start, end) {
  const msPerDay = 1000 * 60 * 60 * 24;
  return Math.round((end - start) / msPerDay);
}

function patientWaitTime(patient) {
  return daysBetween(parseDate(patient.diagnosis), parseDate(patient.surgery));
}

function buildPatientRecords() {
  return syntheticPatients.map((patient) => ({
    ...patient,
    waitDays: patientWaitTime(patient)
  }));
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

function calculateAggregates(records) {
  const totalWait = records.reduce((sum, row) => sum + row.waitDays, 0);
  const average = Math.round(totalWait / records.length);

  const quarterMap = {
    'Q1 2025': [],
    'Q2 2025': [],
    'Q3 2025': [],
    'Q4 2025': []
  };

  records.forEach((row) => {
    const month = parseDate(row.diagnosis).getMonth();
    if (month <= 2) quarterMap['Q1 2025'].push(row.waitDays);
    else if (month <= 5) quarterMap['Q2 2025'].push(row.waitDays);
    else if (month <= 8) quarterMap['Q3 2025'].push(row.waitDays);
    else quarterMap['Q4 2025'].push(row.waitDays);
  });

  const demographics = {
    '50-60': [],
    '61-70': [],
    '71+': []
  };
  records.forEach((row) => demographics[row.ageGroup].push(row.waitDays));

  return {
    averageWait: average,
    medianByQuarter: Object.entries(quarterMap).map(([key, values]) => ({
      label: key,
      value: values.length ? median(values) : 0
    })),
    demographics: Object.entries(demographics).map(([label, values]) => ({
      label,
      value: values.length ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length) : 0
    }))
  };
}

function renderPatientTable(records) {
  const tbody = document.getElementById('patientTableBody');
  tbody.innerHTML = '';

  const latest = records
    .slice()
    .sort((a, b) => parseDate(b.diagnosis) - parseDate(a.diagnosis))
    .slice(0, 5);

  latest.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.name}</td>
      <td>${row.diagnosis}</td>
      <td>${row.surgery}</td>
      <td>${row.waitDays} days</td>
    `;
    tbody.appendChild(tr);
  });
}

function buildComparisonChart(labels, data) {
  const context = document.getElementById('comparisonChart').getContext('2d');
  return new Chart(context, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Median Wait Time',
          data,
          backgroundColor: 'rgba(14,165,233,0.9)',
          borderRadius: 18,
          maxBarThickness: 44
        },
        {
          label: 'CIHI Target',
          data: labels.map(() => benchmarkDays),
          type: 'line',
          borderColor: '#0ea5e9',
          borderWidth: 3,
          pointRadius: 0,
          fill: false,
          tension: 0.2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `${value}d`
          },
          grid: {
            color: 'rgba(15, 23, 42, 0.08)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          labels: {
            usePointStyle: true,
            pointStyle: 'rectRounded'
          }
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${context.parsed.y} days`
          }
        }
      }
    }
  });
}

function buildDemographicsChart(labels, data) {
  const context = document.getElementById('demographicsChart').getContext('2d');
  return new Chart(context, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Average Wait Time',
        data,
        backgroundColor: ['#38bdf8', '#0ea5e9', '#0284c7'],
        borderRadius: 14,
        maxBarThickness: 38
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `${value}d`
          },
          grid: {
            color: 'rgba(15, 23, 42, 0.08)'
          }
        },
        x: {
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${context.parsed.y} days`
          }
        }
      }
    }
  });
}

function refreshDashboard() {
  const records = buildPatientRecords();
  const aggregates = calculateAggregates(records);

  document.getElementById('avgWaitValue').textContent = `${aggregates.averageWait} Days`;
  renderPatientTable(records);

  const comparisonChartLabels = aggregates.medianByQuarter.map((item) => item.label);
  const comparisonChartData = aggregates.medianByQuarter.map((item) => item.value);
  const demographicsLabels = aggregates.demographics.map((item) => item.label);
  const demographicsData = aggregates.demographics.map((item) => item.value);

  buildComparisonChart(comparisonChartLabels, comparisonChartData);
  buildDemographicsChart(demographicsLabels, demographicsData);
}

window.addEventListener('DOMContentLoaded', () => {
  refreshDashboard();

  document.getElementById('jointSelect').addEventListener('change', () => refreshDashboard());
  document.getElementById('granularitySelect').addEventListener('change', () => refreshDashboard());
  document.getElementById('dataModeToggle').addEventListener('change', () => refreshDashboard());
});
