/* ===== CHARTS.JS — Analytics Dashboard Charts ===== */

// Color palette for charts
const COLORS = {
  accent:  '#6C63FF',
  teal:    '#4ECDC4',
  green:   '#4CD964',
  amber:   '#F5A623',
  coral:   '#FF6B6B',
  blue:    '#4DA6FF',
  purple:  '#BD93F9',
  border:  'rgba(255,255,255,0.07)',
  text2:   '#9395A5',
};

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: COLORS.border }, ticks: { color: COLORS.text2, font: { size: 11 } } },
    y: { grid: { color: COLORS.border }, ticks: { color: COLORS.text2, font: { size: 11 } } },
  },
};

// Mock data (would come from backend API in production)
const MOCK_DATA = {
  atsScore: 87,
  keywordMatch: 78,
  skillMatch: 92,
  experienceMatch: 74,
  formattingScore: 96,

  matchedKeywords: ['Python', 'FastAPI', 'REST API', 'PostgreSQL', 'Git', 'Docker Compose', 'Data Analysis', 'Machine Learning', 'Pandas', 'NumPy'],
  missingKeywords: ['Kubernetes', 'Terraform', 'AWS Lambda', 'CI/CD', 'Redis', 'GraphQL'],

  skillCategories: {
    labels: ['Programming', 'Frameworks', 'Databases', 'Cloud', 'Tools', 'Soft Skills'],
    resume:  [90, 85, 70, 45, 80, 88],
    jd:      [95, 90, 80, 75, 85, 80],
  },

  sectionScores: {
    labels: ['Summary', 'Experience', 'Skills', 'Education', 'Projects', 'Formatting'],
    scores: [72, 88, 80, 95, 76, 96],
  },

  improvements: [
    { type: 'warn', icon: '⚠', title: 'Missing Cloud Skills (Kubernetes, AWS)', detail: 'The job requires cloud orchestration experience. Add Kubernetes and AWS to your skills and mention any cloud deployment work in your experience section.' },
    { type: 'err',  icon: '✕', title: 'Weak Quantification in Experience', detail: 'Your bullet points lack numbers. Replace "improved system performance" with "improved system performance by 40%, reducing latency from 200ms to 120ms".' },
    { type: 'info', icon: 'i', title: 'Add a Technical Summary', detail: 'The role expects a concise technical summary. A 2-3 sentence professional summary mentioning your stack and impact will improve ATS scoring by ~8 points.' },
    { type: 'warn', icon: '⚠', title: 'CI/CD Keywords Missing', detail: 'The job description mentions CI/CD pipelines 4 times. If you have any pipeline experience (GitHub Actions, Jenkins, GitLab CI), add it to your resume.' },
  ],
};

function initDashboard() {
  animateScoreCards();
  renderKeywords();
  renderImprovements();
  initATSRing();

  // Charts
  initSkillRadarChart();
  initSectionBarChart();
  initKeywordDonutChart();
  initExperienceTimelineChart();
}

// Animate score card numbers and bars
function animateScoreCards() {
  const cards = {
    'sc-ats':        { value: MOCK_DATA.atsScore,        color: '#6C63FF', suffix: '%' },
    'sc-keyword':    { value: MOCK_DATA.keywordMatch,    color: '#4ECDC4', suffix: '%' },
    'sc-skill':      { value: MOCK_DATA.skillMatch,      color: '#4CD964', suffix: '%' },
    'sc-experience': { value: MOCK_DATA.experienceMatch, color: '#F5A623', suffix: '%' },
  };

  Object.entries(cards).forEach(([id, cfg]) => {
    const valueEl = document.getElementById(`${id}-value`);
    const fillEl  = document.getElementById(`${id}-fill`);
    if (valueEl) animateNumber(valueEl, cfg.value, cfg.suffix);
    if (fillEl) {
      fillEl.style.background = cfg.color;
      setTimeout(() => { fillEl.style.width = `${cfg.value}%`; }, 300);
    }
  });
}

function animateNumber(el, target, suffix = '', duration = 1500) {
  const start = Date.now();
  function update() {
    const progress = Math.min((Date.now() - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * eased) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function initATSRing() {
  const ring = document.getElementById('ats-ring-path');
  const scoreEl = document.getElementById('ats-ring-score');
  if (!ring || !scoreEl) return;

  const circumference = 2 * Math.PI * 45; // r=45
  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = circumference;
  ring.style.transition = 'stroke-dashoffset 1.8s cubic-bezier(0.4,0,0.2,1)';

  const score = MOCK_DATA.atsScore;
  const color = score >= 80 ? '#4CD964' : score >= 60 ? '#F5A623' : '#FF6B6B';
  ring.style.stroke = color;

  setTimeout(() => {
    ring.style.strokeDashoffset = circumference * (1 - score / 100);
    animateNumber(scoreEl, score, '%');
  }, 500);
}

function renderKeywords() {
  const matchedEl = document.getElementById('matched-keywords');
  const missingEl = document.getElementById('missing-keywords');

  if (matchedEl) {
    matchedEl.innerHTML = MOCK_DATA.matchedKeywords.map((kw, i) =>
      `<span class="kw-tag matched" style="animation-delay:${i * 50}ms">${kw}</span>`
    ).join('');
  }
  if (missingEl) {
    missingEl.innerHTML = MOCK_DATA.missingKeywords.map((kw, i) =>
      `<span class="kw-tag missing" style="animation-delay:${i * 50}ms">${kw}</span>`
    ).join('');
  }
}

function renderImprovements() {
  const container = document.getElementById('improvements-list');
  if (!container) return;
  container.innerHTML = MOCK_DATA.improvements.map((imp, i) => `
    <div class="improvement-item" style="animation-delay:${i * 80}ms">
      <div class="imp-icon ${imp.type}"><span style="font-size:14px">${imp.icon}</span></div>
      <div class="imp-content">
        <h4>${imp.title}</h4>
        <p>${imp.detail}</p>
      </div>
    </div>
  `).join('');
}

// Skill Radar → using Bar Chart (Chart.js radar in dark mode can be tricky)
function initSkillRadarChart() {
  const ctx = document.getElementById('skill-chart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: MOCK_DATA.skillCategories.labels,
      datasets: [
        {
          label: 'Your Resume',
          data: MOCK_DATA.skillCategories.resume,
          backgroundColor: 'rgba(108,99,255,0.7)',
          borderRadius: 6,
          borderSkipped: false,
        },
        {
          label: 'Job Requires',
          data: MOCK_DATA.skillCategories.jd,
          backgroundColor: 'rgba(78,205,196,0.3)',
          borderColor: 'rgba(78,205,196,0.6)',
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        x: { grid: { color: COLORS.border }, ticks: { color: COLORS.text2, font: { size: 11 } } },
        y: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.text2, font: { size: 11 }, callback: v => v + '%' },
          min: 0, max: 100,
        },
      },
    }
  });
}

// Section Score horizontal bar chart
function initSectionBarChart() {
  const ctx = document.getElementById('section-chart');
  if (!ctx) return;

  const sectionColors = MOCK_DATA.sectionScores.scores.map(s =>
    s >= 85 ? COLORS.green : s >= 70 ? COLORS.amber : COLORS.coral
  );

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: MOCK_DATA.sectionScores.labels,
      datasets: [{
        data: MOCK_DATA.sectionScores.scores,
        backgroundColor: sectionColors,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: 'y',
      scales: {
        x: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.text2, font: { size: 11 }, callback: v => v + '%' },
          min: 0, max: 100,
        },
        y: { grid: { color: 'transparent' }, ticks: { color: COLORS.text2, font: { size: 12 } } },
      },
    }
  });
}

// Keyword match donut
function initKeywordDonutChart() {
  const ctx = document.getElementById('keyword-donut');
  if (!ctx) return;

  const matched = MOCK_DATA.matchedKeywords.length;
  const missing = MOCK_DATA.missingKeywords.length;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Matched', 'Missing'],
      datasets: [{
        data: [matched, missing],
        backgroundColor: [COLORS.green, COLORS.coral],
        borderWidth: 0,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw} keywords`
          }
        }
      }
    }
  });

  // Custom legend
  const legend = document.getElementById('donut-legend');
  if (legend) {
    legend.innerHTML = `
      <div class="rl-item"><div class="rl-dot" style="background:${COLORS.green}"></div> Matched: ${matched}</div>
      <div class="rl-item"><div class="rl-dot" style="background:${COLORS.coral}"></div> Missing: ${missing}</div>
    `;
  }
}

// Experience relevance timeline (line chart)
function initExperienceTimelineChart() {
  const ctx = document.getElementById('experience-chart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['2019', '2020', '2021', '2022', '2023', '2024'],
      datasets: [{
        label: 'Relevance Score',
        data: [40, 55, 62, 71, 80, 88],
        borderColor: COLORS.accent,
        backgroundColor: 'rgba(108,99,255,0.08)',
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: COLORS.accent,
        tension: 0.4,
        fill: true,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        x: { grid: { color: COLORS.border }, ticks: { color: COLORS.text2, font: { size: 11 } } },
        y: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.text2, font: { size: 11 }, callback: v => v + '%' },
          min: 0, max: 100,
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` Relevance: ${ctx.raw}%` } }
      }
    }
  });
}

// Download handlers
function downloadPDF() {
  showToast('Generating PDF resume... Download will start shortly.');
  // In production: calls backend /api/download/pdf endpoint
  setTimeout(() => showToast('PDF ready! Check your downloads.'), 2000);
}

function downloadDOCX() {
  showToast('Generating DOCX resume... Download will start shortly.');
  setTimeout(() => showToast('DOCX ready! Check your downloads.'), 2000);
}

window.downloadPDF  = downloadPDF;
window.downloadDOCX = downloadDOCX;

// Init on page load
if (document.getElementById('ats-ring-path')) {
  initDashboard();
}