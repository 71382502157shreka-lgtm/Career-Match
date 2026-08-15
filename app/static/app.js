const API_BASE = '/api/v1';

// Global Application State
let token = localStorage.getItem('jwt_token') || null;
let currentUser = null;
let currentAuthMode = 'login';
let currentAuthRole = 'candidate';
let candidateTab = 'recommendations';
let allJobsCache = [];
let selectedWorkplaceFilter = 'All';

// Notification State
let userNotifications = [
  { id: 1, text: "🚀 Your application for Senior AI/ML Engineer was received by Google AI Labs", time: "10 mins ago", read: false },
  { id: 2, text: "⚡ New 85% Match: Backend Software Engineer @ CloudScale Inc", time: "1 hour ago", read: false },
  { id: 3, text: "📄 Resume Parser successfully updated 12 skills on your profile", time: "3 hours ago", read: false }
];

// Visual Mode Switcher for Landing Page
function switchVisualMode(modeName, tabBtn) {
  document.querySelectorAll('.mode-tab').forEach(b => b.classList.remove('active'));
  if (tabBtn) tabBtn.classList.add('active');

  const modes = ['map', 'metro', 'compass', 'constellation', 'target', 'puzzle'];
  modes.forEach(m => {
    const el = document.getElementById(`visual-${m}`);
    if (el) {
      if (m === modeName) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });
}

// DOM Ready Init
document.addEventListener('DOMContentLoaded', async () => {
  setupDragAndDrop();
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);

  if (token) {
    await loadCurrentUser();
  } else {
    showAuthView();
  }
});

// REST API Helper
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, config);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'API Error');
    }
    return data;
  } catch (err) {
    console.error('Fetch Error:', err);
    throw err;
  }
}

// User Session Loader
async function loadCurrentUser() {
  try {
    currentUser = await apiFetch('/users/me');
    updateNavUI();
    
    if (currentUser.role === 'recruiter') {
      showRecruiterView();
    } else {
      showCandidateView();
    }
  } catch (err) {
    console.warn('Session expired or invalid token');
    logout();
  }
}

// Nav UI Updater
function updateNavUI() {
  const navInfo = document.getElementById('nav-user-info');
  if (!currentUser) {
    navInfo.classList.add('hidden');
    return;
  }

  navInfo.classList.remove('hidden');
  document.getElementById('nav-user-name').textContent = currentUser.full_name;
  document.getElementById('nav-avatar').textContent = currentUser.full_name.charAt(0).toUpperCase();

  const roleBadge = document.getElementById('nav-role-badge');
  roleBadge.textContent = currentUser.role === 'recruiter' ? 'EMPLOYER' : 'CANDIDATE';
  roleBadge.className = `role-badge ${currentUser.role}`;

  renderNotifications();
}

// View Controllers
function showAuthView() {
  document.getElementById('auth-section').classList.remove('hidden');
  document.getElementById('candidate-section').classList.add('hidden');
  document.getElementById('recruiter-section').classList.add('hidden');
  document.getElementById('nav-user-info').classList.add('hidden');
}

function showCandidateView() {
  document.getElementById('auth-section').classList.add('hidden');
  document.getElementById('candidate-section').classList.remove('hidden');
  document.getElementById('recruiter-section').classList.add('hidden');

  // Populate Greeting Banner
  const greetingEl = document.getElementById('greeting-name');
  if (greetingEl) greetingEl.textContent = `Welcome back, ${currentUser.full_name} 👋`;

  // Populate Sidebar Details
  document.getElementById('profile-name').textContent = currentUser.full_name;
  document.getElementById('profile-email').textContent = currentUser.email;
  document.getElementById('profile-avatar').textContent = currentUser.full_name.charAt(0).toUpperCase();

  const headlineEl = document.getElementById('profile-headline');
  if (headlineEl) {
    headlineEl.textContent = currentUser.headline || (currentUser.current_company ? `Works at ${currentUser.current_company}` : 'Professional Candidate');
  }

  const ageEl = document.getElementById('profile-age');
  if (ageEl) ageEl.textContent = currentUser.age ? `🎂 ${currentUser.age} Yrs` : '🎂 26 Yrs';

  const locEl = document.getElementById('profile-location');
  if (locEl) locEl.textContent = currentUser.location ? `📍 ${currentUser.location}` : '📍 Remote';

  const degEl = document.getElementById('profile-degree');
  if (degEl) degEl.innerHTML = `🎓 <strong>Degree:</strong> ${escapeHtml(currentUser.degree || currentUser.education || 'B.Tech / Bachelor')}`;

  const expEl = document.getElementById('profile-experience');
  if (expEl) expEl.innerHTML = `💼 <strong>Experience:</strong> ${currentUser.experience_years ? currentUser.experience_years + '+ Years' : 'Entry Level'}`;

  const salEl = document.getElementById('profile-salary');
  if (salEl) salEl.innerHTML = `💰 <strong>Expected Sal:</strong> ${currentUser.expected_salary ? '₹' + (currentUser.expected_salary / 100000).toFixed(1) + ' Lakhs / yr' : 'Flexible'}`;

  const linkedinBtn = document.getElementById('profile-linkedin-link');
  if (linkedinBtn) {
    if (currentUser.linkedin_url) {
      linkedinBtn.href = currentUser.linkedin_url;
      linkedinBtn.classList.remove('hidden');
    } else {
      linkedinBtn.classList.add('hidden');
    }
  }

  const githubBtn = document.getElementById('profile-github-link');
  if (githubBtn) {
    if (currentUser.github_url) {
      githubBtn.href = currentUser.github_url;
      githubBtn.classList.remove('hidden');
    } else {
      githubBtn.classList.add('hidden');
    }
  }

  renderSkillsPills(currentUser.skills);
  switchCandidateTab('recommendations');
}

function showRecruiterView() {
  document.getElementById('auth-section').classList.add('hidden');
  document.getElementById('candidate-section').classList.add('hidden');
  document.getElementById('recruiter-section').classList.remove('hidden');

  document.getElementById('recruiter-name').textContent = currentUser.full_name;
  document.getElementById('recruiter-email').textContent = currentUser.email;
  document.getElementById('recruiter-avatar').textContent = currentUser.full_name.charAt(0).toUpperCase();

  loadRecruiterJobs();
}

// Auth Handlers & Mode Switch
function switchAuthTab(mode) {
  currentAuthMode = mode;
  document.getElementById('tab-login-btn').classList.toggle('active', mode === 'login');
  document.getElementById('tab-register-btn').classList.toggle('active', mode === 'register');

  document.getElementById('auth-title').textContent = mode === 'login' ? 'Welcome Back 👋' : 'Create an Account';
  document.getElementById('auth-submit-btn').textContent = mode === 'login' ? 'Login' : 'Create Account';

  document.getElementById('reg-name-group').classList.toggle('hidden', mode === 'login');
  document.getElementById('reg-role-group').classList.toggle('hidden', mode === 'login');
  document.getElementById('reg-skills-group').classList.toggle('hidden', mode === 'login');
  document.getElementById('login-options').classList.toggle('hidden', mode === 'register');

  const promptText = document.getElementById('auth-toggle-prompt');
  const toggleLink = document.getElementById('auth-toggle-link');
  if (promptText && toggleLink) {
    promptText.textContent = mode === 'login' ? "Don't have an account?" : "Already have an account?";
    toggleLink.textContent = mode === 'login' ? "Sign Up" : "Sign In";
  }
}

function toggleAuthMode(e) {
  if (e) e.preventDefault();
  switchAuthTab(currentAuthMode === 'login' ? 'register' : 'login');
}

function selectRole(role) {
  currentAuthRole = role;
  document.getElementById('role-candidate-btn').classList.toggle('selected', role === 'candidate');
  document.getElementById('role-recruiter-btn').classList.toggle('selected', role === 'recruiter');
}

function handleForgotPassword(e) {
  if (e) e.preventDefault();
  const email = document.getElementById('auth-email').value || 'your email';
  showToast(`Password reset link sent to ${email}`, 'info');
}

function socialLogin(provider) {
  showToast(`Continuing with ${provider}...`, 'info');
  setTimeout(() => {
    // Quick demo login
    document.getElementById('auth-email').value = 'ahashmicheals@gmail.com';
    document.getElementById('auth-password').value = '12345678';
    document.getElementById('auth-form').dispatchEvent(new Event('submit'));
  }, 800);
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  const email = document.getElementById('auth-email').value;
  const password = document.getElementById('auth-password').value;

  try {
    if (currentAuthMode === 'register') {
      const full_name = document.getElementById('reg-name').value;
      const skills = document.getElementById('reg-skills').value;
      await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ full_name, email, password, role: currentAuthRole, skills })
      });
      showToast('Account created successfully! Signing in...', 'success');
    }

    const tokenData = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    token = tokenData.access_token;
    localStorage.setItem('jwt_token', token);
    await loadCurrentUser();
    showToast('Signed in successfully!', 'success');

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem('jwt_token');
  showAuthView();
  showToast('Logged out', 'info');
}

// SKILLS & PROFILE MANAGERS
function renderSkillsPills(skillsCsv) {
  const container = document.getElementById('profile-skills-list');
  container.innerHTML = '';
  if (!skillsCsv) {
    container.innerHTML = '<span style="font-size:0.8rem; color:var(--text-muted);">No skills added yet</span>';
    return;
  }

  const skills = skillsCsv.split(',').map(s => s.trim()).filter(Boolean);
  skills.forEach(skill => {
    const pill = document.createElement('span');
    pill.className = 'skill-pill';
    pill.innerHTML = `${escapeHtml(skill)} <span style="cursor:pointer; opacity:0.6;" onclick="removeSkill('${escapeHtml(skill)}')">&times;</span>`;
    container.appendChild(pill);
  });
}

async function updateUserSkills(newSkillsCsv) {
  try {
    currentUser = await apiFetch('/users/me', {
      method: 'PATCH',
      body: JSON.stringify({ skills: newSkillsCsv })
    });
    renderSkillsPills(currentUser.skills);
    showToast('Skills matrix updated', 'success');
    if (candidateTab === 'recommendations') loadCandidateJobs();
  } catch (err) {
    showToast('Failed to update skills', 'error');
  }
}

function handleAddSkillKey(event) {
  if (event.key === 'Enter') {
    event.preventDefault();
    const input = document.getElementById('add-skill-input');
    const val = input.value.trim();
    if (!val) return;

    const currentArr = currentUser.skills ? currentUser.skills.split(',').map(s => s.trim()) : [];
    if (!currentArr.includes(val)) {
      currentArr.push(val);
      updateUserSkills(currentArr.join(', '));
    }
    input.value = '';
  }
}

function removeSkill(skillToRemove) {
  if (!currentUser.skills) return;
  const newArr = currentUser.skills.split(',').map(s => s.trim()).filter(s => s !== skillToRemove);
  updateUserSkills(newArr.join(', '));
}

// RESUME DRAG AND DROP
function setupDragAndDrop() {
  const dropzone = document.getElementById('resume-dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) uploadResumeFile(files[0]);
  });
}

function handleResumeUpload(event) {
  const files = event.target.files;
  if (files.length > 0) uploadResumeFile(files[0]);
}

async function uploadResumeFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Please upload a PDF file', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  const statusEl = document.getElementById('resume-upload-status');
  statusEl.textContent = 'Parsing resume text & skills...';

  try {
    currentUser = await apiFetch('/users/me/resume', {
      method: 'POST',
      body: formData
    });
    renderSkillsPills(currentUser.skills);
    statusEl.textContent = '✅ Resume parsed & skills updated!';
    showToast('Resume parsed! Job compatibility index updated.', 'success');
    if (candidateTab === 'recommendations') loadCandidateJobs();
  } catch (err) {
    statusEl.textContent = '';
    showToast(err.message, 'error');
  }
}

// CANDIDATE JOBS & SEARCH FILTERS
function switchCandidateTab(tab) {
  candidateTab = tab;
  document.getElementById('tab-recommendations-btn').classList.toggle('active', tab === 'recommendations');
  document.getElementById('tab-all-jobs-btn').classList.toggle('active', tab === 'all');
  loadCandidateJobs();
}

async function loadCandidateJobs() {
  const container = document.getElementById('candidate-jobs-container');
  container.innerHTML = '<div style="text-align:center; padding:3rem; color:var(--text-muted);">Loading recommendations...</div>';

  try {
    if (candidateTab === 'recommendations') {
      allJobsCache = await apiFetch('/recommendations');
    } else {
      allJobsCache = await apiFetch('/jobs/');
    }

    // Update Circular Match Score Gauge Chart
    if (allJobsCache.length > 0 && allJobsCache[0].match_score !== undefined) {
      updateMatchScoreGauge(allJobsCache[0].match_score);
    } else {
      updateMatchScoreGauge(88.0);
    }

    applySearchAndWorkplaceFilters();
  } catch (err) {
    container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--danger);">${err.message}</div>`;
  }
}

function updateMatchScoreGauge(scoreVal) {
  const rounded = Math.round(scoreVal);
  const textEl = document.getElementById('gauge-score-text');
  const circleEl = document.getElementById('gauge-circle');

  if (textEl) textEl.textContent = `${rounded}%`;
  if (circleEl) circleEl.setAttribute('stroke-dasharray', `${rounded}, 100`);
}

function handleSearchFilter() {
  applySearchAndWorkplaceFilters();
}

function filterWorkplace(workplaceType, chipBtn) {
  selectedWorkplaceFilter = workplaceType;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  if (chipBtn) chipBtn.classList.add('active');
  applySearchAndWorkplaceFilters();
}

function applySearchAndWorkplaceFilters() {
  const searchTerm = (document.getElementById('job-search-input')?.value || '').toLowerCase();
  
  let filtered = allJobsCache.filter(j => {
    const matchesSearch = !searchTerm || 
      j.title.toLowerCase().includes(searchTerm) || 
      j.company.toLowerCase().includes(searchTerm) || 
      j.required_skills.toLowerCase().includes(searchTerm);

    const matchesWorkplace = selectedWorkplaceFilter === 'All' || 
      (j.workplace_type || 'Hybrid').toLowerCase() === selectedWorkplaceFilter.toLowerCase();

    return matchesSearch && matchesWorkplace;
  });

  renderCandidateJobs(filtered, candidateTab === 'recommendations');
}

function renderCandidateJobs(jobs, isRecommendation) {
  const container = document.getElementById('candidate-jobs-container');
  container.innerHTML = '';

  if (jobs.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:3rem;" class="glass-panel">
      <h3>No Matching Jobs Found</h3>
      <p style="color:var(--text-muted); margin-top:0.5rem;">Try refining your search text or selected workplace arrangement filter.</p>
    </div>`;
    return;
  }

  jobs.forEach(job => {
    const card = document.createElement('div');
    card.className = 'job-card glass-panel';

    const matchScore = job.match_score !== undefined ? job.match_score : null;
    let badgeClass = 'low';
    if (matchScore >= 70) badgeClass = 'high';
    else if (matchScore >= 45) badgeClass = 'mid';

    const skillsPills = job.required_skills ? job.required_skills.split(',').map(s => `<span class="skill-pill">${s.trim()}</span>`).join('') : '';
    const workplace = job.workplace_type || 'Hybrid';
    const workplaceClass = workplace.toLowerCase().replace(/[^a-z]/g, '');
    const jobType = job.job_type || 'Full-time';
    const logoHtml = job.company_logo_url ? `<img src="${job.company_logo_url}" class="company-logo-img" alt="${escapeHtml(job.company)} logo" />` : '<span style="font-size:1.5rem;">🏢</span>';

    const salaryText = (job.salary_min && job.salary_max) 
      ? `₹${(job.salary_min / 100000).toFixed(1)}L - ₹${(job.salary_max / 100000).toFixed(1)}L / yr`
      : 'Competitive Package';

    const linkedinLinkHtml = job.linkedin_url ? `
      <a href="${job.linkedin_url}" target="_blank" class="linkedin-easy-apply" title="View Application Details">
        Apply External ↗
      </a>
    ` : '';

    // "Why this job?" Explanation Box
    const aiExplanationHtml = matchScore !== null ? `
      <div class="ai-explanation-box">
        💡 <strong>Why this opportunity?</strong> Ranked <strong>${matchScore}%</strong> compatible due to high match in <em>${escapeHtml(job.required_skills.split(',').slice(0, 3).join(', '))}</em>.
      </div>
    ` : '';

    card.innerHTML = `
      <div class="job-card-top">
        <div style="display:flex; gap:0.9rem; align-items:flex-start;">
          ${logoHtml}
          <div>
            <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.25rem;">
              <h3 class="job-title" style="margin-bottom:0;">${escapeHtml(job.title)}</h3>
              <span class="workplace-pill ${workplaceClass}">${escapeHtml(workplace)}</span>
              <span class="skill-pill" style="font-size:0.75rem;">${escapeHtml(jobType)}</span>
              ${linkedinLinkHtml}
            </div>
            <div class="job-company-info">
              <span><strong>${escapeHtml(job.company)}</strong></span>
              <span>• 📍 ${escapeHtml(job.location)}</span>
              <span>• 💼 ${job.experience_years ? job.experience_years + '+ yrs exp' : 'Entry Level'}</span>
              <span>• 💰 ${salaryText}</span>
            </div>
          </div>
        </div>
        ${matchScore !== null ? `<div class="job-match-badge ${badgeClass}">⚡ ${matchScore}% Match</div>` : ''}
      </div>

      ${aiExplanationHtml}

      <p class="job-description">${escapeHtml(job.description)}</p>

      <div style="margin-bottom: 1.25rem;">
        <div style="font-size:0.85rem; font-weight:600; color:var(--dark-charcoal); margin-bottom:0.4rem;">Required Skills:</div>
        <div class="skills-container">${skillsPills}</div>
      </div>

      <div class="job-card-footer">
        <button class="btn btn-secondary btn-sm" onclick="showSkillGap(${job.id}, '${escapeHtml(job.title)}')">⚡ Skill Compatibility</button>
        <button class="btn btn-primary btn-sm" onclick="applyToJob(${job.id})">Apply Now</button>
      </div>
    `;
    container.appendChild(card);
  });
}

// Skill Gap Modal with Interactive Progress Bar
async function showSkillGap(jobId, jobTitle) {
  document.getElementById('gap-job-title').textContent = jobTitle;
  const container = document.getElementById('gap-missing-skills');
  const progressContainer = document.getElementById('skill-gap-progress-container');
  container.innerHTML = 'Analyzing skill compatibility...';

  openModal('skill-gap-modal');

  try {
    const res = await apiFetch(`/jobs/${jobId}/skill-gap`);
    container.innerHTML = '';
    
    const missingCount = res.missing_skills ? res.missing_skills.length : 0;
    const matchPct = Math.max(20, 100 - (missingCount * 20));

    if (progressContainer) {
      progressContainer.innerHTML = `
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:600;">
          <span>Skill Qualification Match</span>
          <span style="color:var(--primary-sage);">${matchPct}% Match</span>
        </div>
        <div class="skill-bar-outer">
          <div class="skill-bar-inner" style="width: ${matchPct}%;"></div>
        </div>
      `;
    }

    if (!res.missing_skills || res.missing_skills.length === 0) {
      container.innerHTML = '<span style="color:var(--primary-sage); font-weight:600;">✨ Great news! Your active profile satisfies all skill requirements for this position.</span>';
    } else {
      res.missing_skills.forEach(skill => {
        container.innerHTML += `<span class="skill-pill missing">❌ ${escapeHtml(skill)}</span>`;
      });
    }
  } catch (err) {
    container.innerHTML = `<span style="color:var(--danger);">${err.message}</span>`;
  }
}

// Apply Handler
async function applyToJob(jobId) {
  try {
    await apiFetch(`/jobs/${jobId}/apply`, { method: 'POST' });
    showToast('Application submitted successfully!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// RECRUITER LOGIC
async function loadRecruiterJobs() {
  const container = document.getElementById('recruiter-jobs-container');
  container.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--text-muted);">Loading posted positions...</div>';

  try {
    const allJobs = await apiFetch('/jobs/');
    const myJobs = allJobs.filter(j => j.posted_by === currentUser.id);
    renderRecruiterJobs(myJobs);
  } catch (err) {
    container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--danger);">${err.message}</div>`;
  }
}

function renderRecruiterJobs(jobs) {
  const container = document.getElementById('recruiter-jobs-container');
  container.innerHTML = '';

  if (jobs.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:3rem;" class="glass-panel">
      <h3>No Active Job Opportunities</h3>
      <p style="color:var(--text-muted); margin-top:0.5rem;">Click "Post New Job Opportunity" to post a position!</p>
    </div>`;
    return;
  }

  jobs.forEach(job => {
    const card = document.createElement('div');
    card.className = 'job-card glass-panel';

    const skillsPills = job.required_skills ? job.required_skills.split(',').map(s => `<span class="skill-pill">${s.trim()}</span>`).join('') : '';

    card.innerHTML = `
      <div class="job-card-top">
        <div>
          <h3 class="job-title">${escapeHtml(job.title)}</h3>
          <div class="job-company-info">
            <span>🏢 ${escapeHtml(job.company)}</span>
            <span>📍 ${escapeHtml(job.location)}</span>
          </div>
        </div>
      </div>

      <p class="job-description">${escapeHtml(job.description)}</p>

      <div style="margin-bottom: 1.25rem;">
        <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.4rem;">Required Skills:</div>
        <div class="skills-container">${skillsPills}</div>
      </div>

      <div class="job-card-footer">
        <button class="btn btn-danger btn-sm" onclick="deleteJob(${job.id})">Delete</button>
        <button class="btn btn-primary btn-sm" onclick="viewRankedCandidates(${job.id}, '${escapeHtml(job.title)}')">🏆 View Applicants</button>
      </div>
    `;
    container.appendChild(card);
  });
}

async function handlePostJobSubmit(event) {
  event.preventDefault();
  const title = document.getElementById('job-title-input').value;
  const company = document.getElementById('job-company-input').value;
  const location = document.getElementById('job-location-input').value;
  const workplace_type = document.getElementById('job-workplace-input').value;
  const job_type = document.getElementById('job-type-input').value;
  const linkedin_url = document.getElementById('job-linkedin-input').value;
  const required_skills = document.getElementById('job-skills-input').value;
  const description = document.getElementById('job-desc-input').value;

  try {
    await apiFetch('/jobs/', {
      method: 'POST',
      body: JSON.stringify({ title, company, location, workplace_type, job_type, linkedin_url, required_skills, description })
    });

    closeModal('post-job-modal');
    document.getElementById('post-job-form').reset();
    showToast('Job opportunity posted successfully!', 'success');
    loadRecruiterJobs();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteJob(jobId) {
  if (!confirm('Are you sure you want to remove this job posting?')) return;
  try {
    await apiFetch(`/jobs/${jobId}`, { method: 'DELETE' });
    showToast('Job posting removed', 'info');
    loadRecruiterJobs();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function viewRankedCandidates(jobId, jobTitle) {
  document.getElementById('candidates-job-title').textContent = jobTitle;
  const container = document.getElementById('candidates-list-container');
  container.innerHTML = '<div style="text-align:center; padding:1.5rem;">Evaluating & Ranking Candidates...</div>';

  openModal('candidates-modal');

  try {
    const candidates = await apiFetch(`/jobs/${jobId}/candidates`);
    container.innerHTML = '';

    if (!candidates || candidates.length === 0) {
      container.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding:1rem;">No applications submitted yet for this position.</div>';
      return;
    }

    candidates.forEach((c, index) => {
      let badgeClass = 'low';
      if (c.match_score >= 70) badgeClass = 'high';
      else if (c.match_score >= 45) badgeClass = 'mid';

      const item = document.createElement('div');
      item.className = 'candidate-item';
      item.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.75rem;">
          <div style="font-weight:700; color:var(--primary-sage); font-size:1.1rem;">#${index + 1}</div>
          <div>
            <div style="font-weight:700; color:var(--dark-charcoal);">${escapeHtml(c.full_name)}</div>
            <div style="font-size:0.8rem; color:var(--text-muted);">${escapeHtml(c.email)}</div>
          </div>
        </div>
        <div class="job-match-badge ${badgeClass}">⚡ ${c.match_score}% Match</div>
      `;
      container.appendChild(item);
    });
  } catch (err) {
    container.innerHTML = `<div style="color:var(--danger); text-align:center;">${err.message}</div>`;
  }
}

// Edit Profile Handler
async function handleProfileUpdateSubmit(event) {
  event.preventDefault();
  const full_name = document.getElementById('edit-name').value;
  const age = document.getElementById('edit-age').value ? parseInt(document.getElementById('edit-age').value) : null;
  const location = document.getElementById('edit-location').value;
  const degree = document.getElementById('edit-degree').value;
  const experience_years = document.getElementById('edit-experience').value ? parseInt(document.getElementById('edit-experience').value) : 0;
  const expected_salary = document.getElementById('edit-salary').value ? parseFloat(document.getElementById('edit-salary').value) : null;
  const headline = document.getElementById('edit-headline').value;
  const current_company = document.getElementById('edit-company').value;
  const education = document.getElementById('edit-education').value;
  const linkedin_url = document.getElementById('edit-linkedin').value;
  const github_url = document.getElementById('edit-github').value;

  try {
    currentUser = await apiFetch('/users/me', {
      method: 'PATCH',
      body: JSON.stringify({ full_name, age, location, degree, experience_years, expected_salary, headline, current_company, education, linkedin_url, github_url })
    });

    closeModal('edit-profile-modal');
    showToast('Profile details updated successfully!', 'success');
    if (currentUser.role === 'candidate') {
      showCandidateView();
    } else {
      showRecruiterView();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Modal Helpers
function openModal(id) {
  if (id === 'edit-profile-modal' && currentUser) {
    document.getElementById('edit-name').value = currentUser.full_name || '';
    document.getElementById('edit-age').value = currentUser.age || '';
    document.getElementById('edit-location').value = currentUser.location || '';
    document.getElementById('edit-degree').value = currentUser.degree || '';
    document.getElementById('edit-experience').value = currentUser.experience_years !== undefined ? currentUser.experience_years : '';
    document.getElementById('edit-salary').value = currentUser.expected_salary || '';
    document.getElementById('edit-headline').value = currentUser.headline || '';
    document.getElementById('edit-company').value = currentUser.current_company || '';
    document.getElementById('edit-education').value = currentUser.education || '';
    document.getElementById('edit-linkedin').value = currentUser.linkedin_url || '';
    document.getElementById('edit-github').value = currentUser.github_url || '';
  }
  document.getElementById(id).classList.add('active');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

function closeModalOnBackdrop(e, id) {
  if (e.target.id === id) closeModal(id);
}

function openPostJobModal() {
  openModal('post-job-modal');
}

// NOTIFICATION LOGIC
function toggleNotifications(event) {
  if (event) event.stopPropagation();
  const dropdown = document.getElementById('notification-dropdown');
  if (!dropdown) return;
  
  const isHidden = dropdown.classList.contains('hidden');
  if (isHidden) {
    renderNotifications();
    dropdown.classList.remove('hidden');
  } else {
    dropdown.classList.add('hidden');
  }
}

function renderNotifications() {
  const container = document.getElementById('notification-list');
  const countEl = document.getElementById('notification-count');
  if (!container) return;

  container.innerHTML = '';
  const unreadCount = userNotifications.filter(n => !n.read).length;
  
  if (countEl) {
    countEl.textContent = unreadCount;
    countEl.style.display = unreadCount > 0 ? 'flex' : 'none';
  }

  if (userNotifications.length === 0) {
    container.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding:1rem; font-size:0.85rem;">No new notifications</div>';
    return;
  }

  userNotifications.forEach(n => {
    const item = document.createElement('div');
    item.className = 'notification-item';
    item.innerHTML = `
      <div>${escapeHtml(n.text)}</div>
      <div class="time" style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">${escapeHtml(n.time)}</div>
    `;
    container.appendChild(item);
  });
}

function clearNotifications() {
  userNotifications = [];
  renderNotifications();
  showToast('Notifications cleared', 'info');
}

document.addEventListener('click', (e) => {
  const dropdown = document.getElementById('notification-dropdown');
  const btn = document.getElementById('notification-btn');
  if (dropdown && !dropdown.classList.contains('hidden')) {
    if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
      dropdown.classList.add('hidden');
    }
  }
});

// FLOATING CAREER COACH CHATBOT
function toggleChatbot() {
  const panel = document.getElementById('chatbot-panel');
  if (panel) panel.classList.toggle('hidden');
}

function handleChatbotSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('chatbot-input');
  const msgText = input.value.trim();
  if (!msgText) return;

  const messagesContainer = document.getElementById('chatbot-messages');

  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'chat-msg user';
  userMsgEl.textContent = msgText;
  messagesContainer.appendChild(userMsgEl);

  input.value = '';
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  setTimeout(() => {
    let botReply = "🌱 Based on your active profile skills, expanding PyTorch and Docker competencies will improve your match score across technical positions.";
    if (msgText.toLowerCase().includes('resume')) {
      botReply = "📄 Tip: Structuring your PDF resume with clear sections for Skills, Experience, and Education ensures maximum parsing accuracy!";
    } else if (msgText.toLowerCase().includes('score') || msgText.toLowerCase().includes('match')) {
      botReply = "⚡ Match compatibility indices are calculated using skill overlap weighting and natural language TF-IDF similarity.";
    }

    const botMsgEl = document.createElement('div');
    botMsgEl.className = 'chat-msg bot';
    botMsgEl.textContent = botReply;
    messagesContainer.appendChild(botMsgEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }, 600);
}

// Toast Helper
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast-notification');
  toast.textContent = message;
  toast.className = `alert-toast ${type}`;
  toast.classList.remove('hidden');

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
