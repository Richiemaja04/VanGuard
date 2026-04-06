/* ===== APP.JS — ResumeIQ Main Logic ===== */

// Navbar scroll effect
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// Hamburger menu
const hamburger = document.getElementById('hamburger');
if (hamburger) {
  hamburger.addEventListener('click', () => {
    document.querySelector('.nav-links')?.classList.toggle('mobile-open');
  });
}

// Animated count-up for hero stats
function animateCount(el, target, suffix = '', duration = 2000) {
  const start = Date.now();
  const startVal = 0;
  const isLarge = target > 1000;
  function update() {
    const elapsed = Date.now() - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startVal + (target - startVal) * eased);
    el.textContent = isLarge ? current.toLocaleString() : current;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

const statNums = document.querySelectorAll('.stat-num');
if (statNums.length > 0) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        animateCount(el, parseInt(el.dataset.count));
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  statNums.forEach(el => observer.observe(el));
}

// Animate progress bars
function animateBars() {
  document.querySelectorAll('.fc-fill, .sc-fill').forEach(bar => {
    const target = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = target; }, 200);
  });
}

// Trigger bar animations on load
window.addEventListener('load', () => {
  setTimeout(animateBars, 400);
});

// Toast notification
function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span style="font-size:16px">${type === 'success' ? '✓' : '✕'}</span>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ===== BUILDER PAGE LOGIC =====

let currentStep = 1;
const totalSteps = 5;
let selectedTemplate = 'classic';
let resumePath = null;
let buildMode = null; // 'upload' or 'scratch'

const stepConfig = [
  { id: 1, label: 'Profile' },
  { id: 2, label: 'Template' },
  { id: 3, label: 'Job Description' },
  { id: 4, label: 'Resume' },
  { id: 5, label: 'Analyze' },
];

function goToStep(n) {
  if (n < 1 || n > totalSteps) return;
  currentStep = n;
  renderProgress();
  document.querySelectorAll('.step-card').forEach((card, i) => {
    card.classList.toggle('active', i + 1 === n);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderProgress() {
  const container = document.getElementById('progress-container');
  if (!container) return;
  container.innerHTML = stepConfig.map((s, i) => `
    <div class="ps">
      <div class="ps-dot ${currentStep > s.id ? 'done' : currentStep === s.id ? 'active' : ''}">
        ${currentStep > s.id ? '✓' : s.id}
      </div>
      <span class="ps-label ${currentStep === s.id ? 'active' : ''}">${s.label}</span>
    </div>
    ${i < stepConfig.length - 1 ? `<div class="ps-line ${currentStep > s.id ? 'done' : ''}"></div>` : ''}
  `).join('');
}

// Template selection
function selectTemplate(name) {
  selectedTemplate = name;
  document.querySelectorAll('.template-card').forEach(card => {
    card.classList.toggle('selected', card.dataset.template === name);
  });
}

// Upload resume
function setupUploadZone() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('resume-file');
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  });

  input.addEventListener('change', () => {
    if (input.files[0]) handleFileUpload(input.files[0]);
  });
}

function handleFileUpload(file) {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  if (!allowed.includes(file.type) && !file.name.endsWith('.pdf') && !file.name.endsWith('.docx')) {
    showToast('Please upload a PDF or DOCX file', 'error');
    return;
  }
  const zone = document.getElementById('upload-zone');
  zone.innerHTML = `
    <div class="upload-icon">📄</div>
    <h3>${file.name}</h3>
    <p style="color: var(--c-green)">${(file.size / 1024).toFixed(1)} KB · Ready to analyze</p>
    <p style="margin-top:8px; font-size:12px; color:var(--c-text2)">Click to change file</p>
    <input type="file" id="resume-file" accept=".pdf,.docx" />
  `;
  setupUploadZone();
  resumePath = file;
  showToast('Resume uploaded successfully!');
}

// Build mode toggle
function selectBuildMode(mode) {
  buildMode = mode;
  document.querySelectorAll('.path-btn').forEach(btn => {
    btn.classList.toggle('selected', btn.dataset.mode === mode);
  });
  document.getElementById('upload-section').style.display = mode === 'upload' ? 'block' : 'none';
  document.getElementById('scratch-section').style.display = mode === 'scratch' ? 'block' : 'none';
}

// Analyze & redirect to dashboard
async function analyzeResume() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('active');

  const steps = document.querySelectorAll('.ls-item');
  const labels = [
    'Extracting text and parsing resume...',
    'Running keyword matching analysis...',
    'Computing semantic similarity score...',
    'Evaluating ATS formatting compliance...',
    'Generating optimized resume with AI...',
  ];

  for (let i = 0; i < steps.length; i++) {
    if (steps[i - 1]) {
      steps[i - 1].classList.remove('active');
      steps[i - 1].classList.add('done');
    }
    steps[i].classList.add('active');
    await delay(900 + Math.random() * 400);
  }
  steps[steps.length - 1].classList.remove('active');
  steps[steps.length - 1].classList.add('done');
  await delay(600);

  // Store mock session data
  const jd = document.getElementById('job-desc')?.value || '';
  sessionStorage.setItem('resumeiq_template', selectedTemplate);
  sessionStorage.setItem('resumeiq_jd', jd.slice(0, 200));
  sessionStorage.setItem('resumeiq_mode', buildMode || 'upload');

  if (overlay) overlay.classList.remove('active');
  window.location.href = 'dashboard.html';
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// Initialize builder if on builder page
if (document.getElementById('progress-container')) {
  renderProgress();
  setupUploadZone();

  // Expose functions
  window.goToStep = goToStep;
  window.selectTemplate = selectTemplate;
  window.selectBuildMode = selectBuildMode;
  window.analyzeResume = analyzeResume;
}

// Expose toast globally
window.showToast = showToast;