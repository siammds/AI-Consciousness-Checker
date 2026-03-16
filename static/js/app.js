/* ==========================================================
   ACI Evaluation System — app.js
   Full rewrite for new emerald/charcoal SPA design
   Questions shown as Q1–Q13 inline with answer boxes.
   No segment labels shown to the user.
   ========================================================== */

'use strict';

// ── Constants ─────────────────────────────────────────────────────────────────
const C = {
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#f87171',
  sky: '#38bdf8',
  violet: '#a78bfa',
  orange: '#f97316',
};

// ── Global state ──────────────────────────────────────────────────────────────
const STATE = {
  sessionUid: null,
  selectedQuestions: [], // flat list of {id, display_num, prompt, segment}
  questionIds: [],
  displayNums: {}, // id → display_num
  answers: {},
  totalQuestions: 0,
  evaluationResult: null,
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const val = id => (document.getElementById(id)?.value || '').trim();
const escHtml = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const el = id => document.getElementById(id);

function renderMarkdown(text) {
  return String(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^[-•]\s/gm, '• ')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

// ── API wrapper ───────────────────────────────────────────────────────────────
const API = {
  async request(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch('/api' + path, opts);
    if (!r.ok) {
      let msg = `HTTP ${r.status}`;
      try { const j = await r.json(); msg = j.detail || j.message || msg; } catch (_) { }
      throw new Error(msg);
    }
    return r.json();
  },
  get: (p) => API.request('GET', p),
  post: (p, b) => API.request('POST', p, b),
  delete: (p) => API.request('DELETE', p),
};

// ── Panel navigation ──────────────────────────────────────────────────────────
function togglePanel(panelId) {
  const panel = el(panelId);
  if (!panel) return;
  const body = el(panelId + '-body');
  const chevron = panel.querySelector('.step-chevron');
  const isOpen = body?.classList.contains('open');
  if (body) body.classList.toggle('open', !isOpen);
  if (chevron) chevron.classList.toggle('open', !isOpen);
}

function openPanel(panelId, markActive) {
  const panel = el(panelId);
  if (!panel) return;
  const body = el(panelId + '-body');
  const chevron = panel.querySelector('.step-chevron');
  if (body) body.classList.add('open');
  if (chevron) chevron.classList.add('open');
  if (markActive) {
    document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
    panel.classList.add('active');
    // stepper bar
    const idx = panelId.replace('p', '');
    document.querySelectorAll('.stepper-step').forEach(s => s.classList.remove('active'));
    el('sb' + idx)?.classList.add('active');
  }
}

function scrollToPanel(panelId) {
  openPanel(panelId, true);
  setTimeout(() => {
    const e = el(panelId);
    if (e) e.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 60);
}

function markPanelDone(panelId, tagText) {
  const panel = el(panelId);
  if (!panel) return;
  panel.classList.remove('active');
  panel.classList.add('done');
  const idx = panelId.replace('p', '');
  el('sb' + idx)?.classList.add('done');
  const tag = el('tag' + idx);
  if (tag) { tag.textContent = tagText || 'Done'; tag.className = 'step-tag done'; }
}

function updateWorkflowProgress(step, total) {
  const pct = Math.round((step / total) * 100);
  const bar = el('workflowProgressBar');
  const lbl = el('workflowProgressLabel');
  if (bar) bar.style.width = pct + '%';
  if (lbl) lbl.textContent = `Step ${step} / ${total}`;
}

function openHistory() {
  el('historyModal')?.classList.remove('hidden');
  loadSessions();
}
function navigateTo() { } // stub — no tabs in new design

// ── Loading overlay ───────────────────────────────────────────────────────────
function showLoading(msg = 'Processing…') {
  const ov = el('loadingOverlay');
  const lm = el('loadingMsg');
  if (lm) lm.textContent = msg;
  ov?.classList.remove('hidden');
}
function hideLoading() { el('loadingOverlay')?.classList.add('hidden'); }

// ── Modal ─────────────────────────────────────────────────────────────────────
function closeModal(id) { el(id)?.classList.add('hidden'); }

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  const colors = { success: C.success, error: C.danger, warning: C.warning };
  const div = document.createElement('div');
  div.className = 'copy-flash';
  div.style.borderColor = colors[type] || C.success;
  div.innerHTML = `<span style="color:${colors[type] || C.success};font-weight:700">${icons[type] || '✓'}</span> ${escHtml(msg)}`;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3200);
}

// ── Session info (header) ─────────────────────────────────────────────────────
function updateSessionInfo() {
  const box = el('activeSessionInfo');
  if (!box) return;
  if (STATE.sessionUid) {
    box.style.display = 'inline-flex';
    box.innerHTML = `<span style="font-size:0.72rem;color:var(--em-light);background:var(--em-soft);border:1px solid var(--em-border);padding:3px 10px;border-radius:999px;font-family:var(--font-mono)">Session: ${STATE.sessionUid.slice(0, 8)}…</span>`;
  } else {
    box.style.display = 'none';
  }
}

// ── Status modal ──────────────────────────────────────────────────────────────
async function showStatusModal() {
  el('statusModal')?.classList.remove('hidden');
  const content = el('statusContent');
  if (!content) return;
  content.innerHTML = '<div class="spinner"></div>';
  try {
    const res = await API.get('/status');
    const modHtml = Object.entries(res.models || {}).map(([k, v]) => {
      const ready = v === 'ready' || v === 'loaded';
      return `<div class="metric-pill">
        <span class="mp-label">${escHtml(k)}</span>
        <span class="mp-val" style="color:${ready ? C.success : C.warning}">${ready ? 'Ready' : escHtml(v.slice(0, 22))}</span>
      </div>`;
    }).join('');
    const dsHtml = Object.entries(res.datasets || {}).map(([k, v]) => {
      const ready = v === 'ready' || v === 'loaded';
      return `<div class="metric-pill">
        <span class="mp-label">${escHtml(k)}</span>
        <span class="mp-val" style="color:${ready ? C.success : C.warning}">${ready ? 'Ready' : escHtml(v.slice(0, 22))}</span>
      </div>`;
    }).join('');
    content.innerHTML = `
      <h3 style="margin-bottom:10px;font-size:0.85rem;color:var(--em-light)">NLP Models</h3>
      <div class="metric-grid" style="margin-bottom:16px">${modHtml || '<p style="color:var(--t3)">Status unknown.</p>'}</div>
      <h3 style="margin-bottom:10px;font-size:0.85rem;color:var(--em-light)">Reference Datasets</h3>
      <div class="metric-grid">${dsHtml || '<p style="color:var(--t3)">Status unknown.</p>'}</div>
      <div style="margin-top:14px;font-size:0.73rem;color:var(--t3);font-style:italic">${escHtml(res.credit || '')}</div>`;
  } catch (e) {
    content.innerHTML = `<div class="alert alert-danger">Could not fetch status: ${escHtml(e.message)}</div>`;
  }
}

// ── Step 1: Create session ────────────────────────────────────────────────────
async function startNewEvaluation() {
  const modelName = val('modelName');
  if (!modelName) { showToast('Model name is required.', 'warning'); return; }

  const metadata = {
    model_name: modelName,
    model_version: val('modelVersion'),
    provider: val('modelProvider'),
    evaluator_name: val('evaluatorName'),
    evaluation_title: val('evalTitle'),
    notes: val('evalNotes'),
  };

  showLoading('Creating session and generating 13 questions…');
  try {
    const res = await API.post('/sessions', metadata);
    STATE.sessionUid = res.session_uid;
    STATE.selectedQuestions = [];
    STATE.questionIds = [];
    STATE.displayNums = {};
    STATE.answers = {};
    STATE.evaluationResult = null;
    updateSessionInfo();
    markPanelDone('p1', 'Done');
    updateWorkflowProgress(2, 5);
    await generateQuestions();
  } catch (e) {
    showToast('Error creating session: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

// ── Step 2: Generate questions ────────────────────────────────────────────────
async function generateQuestions() {
  if (!STATE.sessionUid) {
    showToast('Create a session first (Step 1).', 'warning');
    scrollToPanel('p1');
    return;
  }

  // thirteen_mixed = 1 Q from each of 13 random segments
  try {
    const res = await API.post('/questions/generate', { mode: 'thirteen_mixed' });
    STATE.selectedQuestions = res.questions || [];  // flat Q1-Q13 list
    STATE.questionIds = res.question_ids || [];
    STATE.displayNums = res.display_nums || {};
    STATE.totalQuestions = res.total || STATE.selectedQuestions.length;
    window._questionPlainText = res.plain_text || '';

    // Save question IDs to session
    await API.post('/answers/save', {
      session_uid: STATE.sessionUid,
      answers: {},
      question_ids: STATE.questionIds,
    });

    // Update panel 2
    const sub = el('p2-sub');
    if (sub) sub.textContent = `${STATE.totalQuestions} questions ready — copy each question to your AI model, paste answers below`;
    const tag2 = el('tag2');
    if (tag2) { tag2.textContent = 'Ready'; tag2.className = 'step-tag active'; }

    renderQA(STATE.selectedQuestions);
    openPanel('p2', true);
    scrollToPanel('p2');
    showToast(`${STATE.totalQuestions} questions generated!`);
    updateWorkflowProgress(2, 5);
  } catch (e) {
    showToast('Error generating questions: ' + e.message, 'error');
    throw e;
  }
}

// ── Render Q+A blocks ─────────────────────────────────────────────────────────
function renderQA(questions) {
  const container = el('qaContainer');
  if (!container) return;
  if (!questions || questions.length === 0) {
    container.innerHTML = '<div class="alert alert-info">No questions generated yet.</div>';
    return;
  }

  container.innerHTML = questions.map(q => {
    const num = q.display_num || q.id;
    const qid = q.id;
    return `
      <div class="qa-block" id="qa-block-${qid}">
        <div class="qa-question">
          <span class="qa-qnum">Q${num}</span>
          <span class="qa-qtext">${escHtml(q.prompt)}</span>
        </div>
        <div class="qa-answer">
          <textarea
            id="answer-${qid}"
            placeholder="Paste the AI model's answer to Q${num} here…"
            oninput="onAnswerInput(${qid}, this)"
          ></textarea>
        </div>
        <div class="qa-footer">
          <span class="qa-char-count" id="char-${qid}">0 characters</span>
          <span class="qa-status" id="status-${qid}"></span>
        </div>
      </div>`;
  }).join('');

  updateAnswerProgress();
}

function onAnswerInput(qid, textarea) {
  const text = textarea.value;
  STATE.answers[qid] = text;
  const block = el('qa-block-' + qid);
  const charEl = el('char-' + qid);
  const statEl = el('status-' + qid);
  if (charEl) charEl.textContent = `${text.length} characters`;
  if (block) block.classList.toggle('filled', text.trim().length > 0);
  autosaveAnswers();
  updateAnswerProgress();
}

function updateAnswerProgress() {
  const total = STATE.questionIds.length;
  const filled = STATE.questionIds.filter(qid => {
    const t = el('answer-' + qid);
    return t && t.value.trim().length > 0;
  }).length;

  const pct = total > 0 ? Math.round((filled / total) * 100) : 0;

  const bar = el('answerProgressBar');
  const count = el('answerProgressCount');
  const label = el('answerProgress');
  if (bar) bar.style.width = pct + '%';
  if (count) count.textContent = `${filled} / ${total}`;
  if (label) label.textContent = `${filled} / ${total}`;

  // Mark step 2 done when all filled
  if (total > 0 && filled === total) {
    const tag2 = el('tag2');
    if (tag2) { tag2.textContent = 'Complete'; tag2.className = 'step-tag done'; }
  }
}

// Startup
window.onload = initApp;

// ── Export Functions ──────────────────────────────────────────────────────────
function exportCurrentJson() {
  if (!STATE.sessionUid) { showToast('No active session to export.', 'warning'); return; }
  window.open('/export/json/' + STATE.sessionUid, '_blank');
}

function exportCurrentCsv() {
  if (!STATE.sessionUid) { showToast('No active session to export.', 'warning'); return; }
  window.open('/export/csv/' + STATE.sessionUid, '_blank');
}

function printReport() {
  if (!STATE.sessionUid) { showToast('No active session to print.', 'warning'); return; }
  window.open('/export/report/' + STATE.sessionUid, '_blank');
}

// ── Copy / download questions  ────────────────────────────────────────────────
function copyAllQuestions() {
  const text = window._questionPlainText || STATE.selectedQuestions.map(q => `Q${q.display_num || q.id}. ${q.prompt}`).join('\n\n');
  navigator.clipboard.writeText(text).then(() => showToast('All 13 questions copied!')).catch(() => showToast('Copy failed', 'error'));
}

function downloadQuestions() {
  const text = window._questionPlainText || STATE.selectedQuestions.map(q => `Q${q.display_num || q.id}. ${q.prompt}`).join('\n\n');
  const a = document.createElement('a');
  a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(text);
  a.download = 'aci_questions.txt';
  a.click();
}

// ── Bulk paste ────────────────────────────────────────────────────────────────
function toggleBulkPaste() {
  const sec = el('bulkPasteSection');
  const btn = el('bulkToggleBtn');
  const isVis = sec?.style.display !== 'none';
  if (sec) sec.style.display = isVis ? 'none' : '';
  if (btn) btn.textContent = isVis ? 'Bulk Paste All Answers' : 'Individual Answer Boxes';
}

async function parseBulkPaste() {
  const text = el('bulkPasteArea')?.value?.trim();
  if (!text) { showToast('Paste the AI answers first.', 'warning'); return; }
  if (!STATE.sessionUid) { showToast('Create a session first.', 'warning'); return; }
  if (STATE.questionIds.length === 0) { showToast('Generate questions first.', 'warning'); return; }

  showLoading('Parsing bulk paste and matching answers…');
  try {
    const res = await API.post('/answers/save', {
      session_uid: STATE.sessionUid,
      answers: {},
      bulk_paste: text,
      question_ids: STATE.questionIds,
    });

    const pct = Math.round((res.parser_confidence || 0) * 100);
    showToast(`Parsed ${res.saved} answers — ${pct}% confidence`);

    // Reload from server → fill boxes
    const session = await API.get(`/sessions/${STATE.sessionUid}`);
    const saved = session.answers || {};
    Object.entries(saved).forEach(([qid, ans]) => {
      const t = el('answer-' + qid);
      if (t) {
        t.value = ans;
        STATE.answers[parseInt(qid)] = ans;
        const block = el('qa-block-' + qid);
        if (block) block.classList.toggle('filled', ans.trim().length > 0);
      }
    });
    updateAnswerProgress();

    if (res.validation?.warnings?.length) {
      res.validation.warnings.forEach(w => showToast(w, 'warning'));
    }
    // Collapse bulk paste, show individual
    el('bulkPasteSection').style.display = 'none';
    el('bulkToggleBtn').textContent = 'Bulk Paste All Answers';
  } catch (e) {
    showToast('Parse error: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

// ── Save answers ──────────────────────────────────────────────────────────────
async function saveAllAnswers() {
  if (!STATE.sessionUid) { showToast('No active session.', 'warning'); return; }
  if (STATE.questionIds.length === 0) { showToast('Generate questions first.', 'warning'); return; }

  const answers = {};
  STATE.questionIds.forEach(qid => {
    const t = el('answer-' + qid);
    if (t && t.value.trim()) answers[String(qid)] = t.value.trim();
  });

  try {
    const res = await API.post('/answers/save', {
      session_uid: STATE.sessionUid,
      answers,
      question_ids: STATE.questionIds,
    });
    showToast(`Saved ${res.saved} answers.`);
    updateAnswerProgress();
  } catch (e) {
    showToast('Save error: ' + e.message, 'error');
  }
}

// ── Autosave ──────────────────────────────────────────────────────────────────
let _autosaveTimer = null;
function autosaveAnswers() {
  clearTimeout(_autosaveTimer);
  _autosaveTimer = setTimeout(async () => {
    if (!STATE.sessionUid || STATE.questionIds.length === 0) return;
    const answers = {};
    STATE.questionIds.forEach(qid => {
      const t = el('answer-' + qid);
      if (t && t.value.trim()) answers[String(qid)] = t.value.trim();
    });
    try {
      await API.post('/answers/save', {
        session_uid: STATE.sessionUid,
        answers,
        question_ids: STATE.questionIds,
      });
    } catch (_) { }
  }, 2000);
}

// ── Step 3: Run evaluation ────────────────────────────────────────────────────
async function runEvaluation() {
  if (!STATE.sessionUid) { showToast('Create a session first.', 'warning'); scrollToPanel('p1'); return; }
  await saveAllAnswers();
  markPanelDone('p3', 'Running…');
  updateWorkflowProgress(4, 5);
  showLoading('Running full NLP evaluation pipeline… This may take 30–120 seconds on first run while loading models.');
  try {
    const result = await API.post('/evaluate', { session_uid: STATE.sessionUid });
    STATE.evaluationResult = result;
    markPanelDone('p3', 'Done');
    markPanelDone('p2', 'Done');
    renderDashboard(result);
    openPanel('p4', true);
    scrollToPanel('p4');
    updateWorkflowProgress(5, 5);
    const sub4 = el('p4-sub');
    const adj = result.adjusted_score ?? 0;
    if (sub4) sub4.textContent = `Score: ${adj.toFixed(1)} / 133 — ${result.reliability_label || ''} Reliability`;
    const tag4 = el('tag4');
    if (tag4) { tag4.textContent = 'Complete'; tag4.className = 'step-tag done'; }
    const tag5 = el('tag5');
    if (tag5) { tag5.textContent = 'Ready'; tag5.className = 'step-tag active'; }
    showToast('Evaluation complete! Results ready.');
  } catch (e) {
    const tag3 = el('tag3');
    if (tag3) { tag3.textContent = 'Error'; tag3.className = 'step-tag'; }
    showToast('Evaluation error: ' + e.message, 'error');
    console.error('Evaluation error:', e);
  } finally {
    hideLoading();
  }
}

// ── Render results dashboard ──────────────────────────────────────────────────
function renderDashboard(result) {
  if (!result) return;
  const noRes = el('noResultsMsg');
  if (noRes) noRes.style.display = 'none';

  const adjScore = result.adjusted_score ?? result.overall_score ?? 0;
  const rawScore = result.porter_result?.sum_score ?? 0;
  const reliability = result.reliability_label || 'N/A';
  const indicators = result.indicator_scores?.indicators || {};
  const internalMet = result.indicator_scores?.internal_metrics || {};

  // Scores
  const heroScore = el('heroScore');
  if (heroScore) heroScore.textContent = adjScore.toFixed(1);
  const heroRaw = el('heroRawScore');
  if (heroRaw) heroRaw.textContent = rawScore.toFixed(1);
  const heroRel = el('heroReliability');
  if (heroRel) {
    const icon = reliability === 'High' ? '✓' : reliability === 'Medium' ? '~' : '✕';
    heroRel.innerHTML = `<span class="reliability-badge rel-${reliability}">${icon} ${reliability} Reliability</span>`;
  }

  // Indicators
  const indColors = [C.success, '#3b82f6', C.sky, '#a78bfa', '#ec4899', C.orange, C.warning, C.violet, '#14b8a6', '#6366f1'];
  const indContainer = el('indicatorGrid');
  if (indContainer) {
    indContainer.innerHTML = '';
    Object.keys(indicators).forEach((key, i) => {
      const ind = indicators[key];
      const score = ind.score ?? 0;
      const color = indColors[i % indColors.length];
      const card = document.createElement('div');
      card.className = 'ind-card';
      card.innerHTML = `
        <div class="ind-num" style="color:${color}">${score.toFixed(0)}</div>
        <div class="ind-name">${escHtml(ind.label || key)}</div>
        <div class="ind-desc">${escHtml(ind.description || '')}</div>
        <div class="ind-bar"><div class="ind-fill" style="width:${score}%;background:${color}"></div></div>`;
      indContainer.appendChild(card);
    });
  }

  // Narrative
  const narrativeEl = el('narrativeText');
  if (narrativeEl) narrativeEl.innerHTML = renderMarkdown(result.narrative || 'No narrative available.');

  // Strengths/Weaknesses
  renderStrengthsWeaknesses(result.strengths, result.weaknesses);

  // Tone
  renderTone(result.tone_analysis);

  // Sentiment
  renderSentiment(result.sentiment_analysis);

  // Internal metrics
  renderInternalMetrics(internalMet);

  // Warnings
  renderWarnings(result.warnings);

  // Adjustment log
  const adjLogEl = el('adjustmentLog');
  if (adjLogEl) {
    const log = result.adjustment_log || [];
    adjLogEl.innerHTML = log.length
      ? log.map(l => `<li>${escHtml(l)}</li>`).join('')
      : '<li style="color:var(--t3)">No adjustments applied.</li>';
  }

  // Charts
  drawRadar(indicators);
  const porterSegs = result.porter_result?.segment_scores ?? result.indicator_scores?.segment_scores ?? {};
  drawBarChart(porterSegs);
  drawGauge(adjScore);

  // Advanced tab ready
  const tag5 = el('tag5');
  if (tag5) { tag5.textContent = 'Ready'; tag5.className = 'step-tag active'; }
}

// ── Strengths/Weaknesses ──────────────────────────────────────────────────────
function renderStrengthsWeaknesses(strengths, weaknesses) {
  const sc = el('strengthsContainer');
  const wc = el('weaknessesContainer');
  if (sc) {
    sc.innerHTML = (strengths && strengths.length)
      ? strengths.slice(0, 5).map(s => `
          <div class="sw-item sw-s">
            <div class="sw-label">${escHtml(s.label || s.trait || s.name || JSON.stringify(s))}</div>
            ${s.score !== undefined ? `<div class="sw-score">Score: ${Number(s.score).toFixed(0)} / 100</div>` : ''}
            <div class="sw-desc">${escHtml(s.description || 'Verified via textual analysis.')}</div>
          </div>`).join('')
      : '<p style="color:var(--t3);font-size:0.82rem">No strengths data.</p>';
  }
  if (wc) {
    wc.innerHTML = (weaknesses && weaknesses.length)
      ? weaknesses.slice(0, 5).map(s => `
          <div class="sw-item sw-w">
            <div class="sw-label">${escHtml(s.label || s.trait || s.name || JSON.stringify(s))}</div>
            ${s.score !== undefined ? `<div class="sw-score">Score: ${Number(s.score).toFixed(0)} / 100</div>` : ''}
            <div class="sw-desc">${escHtml(s.description || 'Verified via textual analysis.')}</div>
          </div>`).join('')
      : '<p style="color:var(--t3);font-size:0.82rem">No weakness data.</p>';
  }
}



// ── Tone ──────────────────────────────────────────────────────────────────────
function renderTone(ta) {
  const c = el('toneContainer');
  const dt = el('dominantTone');
  if (!c) return;
  const dist = ta?.tones || ta?.tone_distribution || ta?.distribution || {};
  const dom = ta?.dominant_tone || ta?.dominant || 'N/A';
  if (dt) dt.textContent = dom;
  const sorted = Object.entries(dist).sort((a, b) => b[1] - a[1]).slice(0, 7);
  c.innerHTML = sorted.length
    ? sorted.map(([name, score]) => `
        <div class="tone-row">
          <div class="tone-name">${escHtml(name)}</div>
          <div class="tone-bar"><div class="tone-fill" style="width:${Math.min(100, (score * 100).toFixed(0))}%"></div></div>
          <div class="tone-val">${(score * 100).toFixed(0)}%</div>
        </div>`).join('')
    : '<p style="color:var(--t3);font-size:0.82rem">No tone data.</p>';
}

// ── Sentiment ─────────────────────────────────────────────────────────────────
function renderSentiment(sa) {
  const canvas = el('sentimentChart');
  if (!canvas || typeof Chart === 'undefined') return;
  const dist = sa?.distribution_pct || sa?.sentiment_distribution || sa?.distribution || {};
  const data = [dist.positive || 0, dist.neutral || 0, dist.negative || 0].map(v => Math.round(v * 100));
  
  if (window._sentimentChart) { try { window._sentimentChart.destroy(); } catch (_) { } }
  window._sentimentChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data,
        backgroundColor: [C.success, C.sky, C.danger],
        borderWidth: 0, hoverOffset: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#cbd5e1', font: { size: 10 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}%` } }
      },
      cutout: '70%'
    }
  });
}

// ── Internal metrics ──────────────────────────────────────────────────────────
function renderInternalMetrics(metrics) {
  const c = el('internalMetricsContainer');
  if (!c) return;
  if (!metrics || !Object.keys(metrics).length) {
    c.innerHTML = '<div class="alert alert-info">No internal metrics available.</div>';
    return;
  }
  c.innerHTML = `<div class="metric-grid">${Object.entries(metrics).map(([k, v]) => `
    <div class="metric-pill">
      <span class="mp-label">${escHtml(k.replace(/_/g, ' '))}</span>
      <span class="mp-val">${typeof v === 'number' ? v.toFixed(2) : escHtml(String(v))}</span>
    </div>`).join('')}</div>`;
}

// ── Warnings ──────────────────────────────────────────────────────────────────
function renderWarnings(warnings) {
  const c = el('warningsContainer');
  if (!c) return;
  const list = Array.isArray(warnings) ? warnings : [];
  c.innerHTML = list.length
    ? list.map(w => `<div class="alert alert-warning">${escHtml(w)}</div>`).join('')
    : '<div class="alert alert-success">No warnings.</div>';
}

// ── Charts ────────────────────────────────────────────────────────────────────
function drawRadar(indicators) {
  const canvas = el('radarChart');
  if (!canvas || !indicators || typeof Chart === 'undefined') return;
  const labels = Object.values(indicators).map(i => i.label || '?');
  const data = Object.values(indicators).map(i => i.score ?? 0);
  if (window._radarChart) { try { window._radarChart.destroy(); } catch (_) { } }
  window._radarChart = new Chart(canvas, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        data, fill: true,
        backgroundColor: 'rgba(16,185,129,0.10)',
        borderColor: '#10b981',
        pointBackgroundColor: '#10b981',
        pointRadius: 3,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        r: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          angleLines: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#475569', stepSize: 25, backdropColor: 'transparent', font: { size: 9 } },
          pointLabels: { color: '#64748b', font: { size: 9 } },
        },
      },
      plugins: { legend: { display: false } },
    },
  });
}

function drawBarChart(segmentScores) {
  const canvas = el('barChart');
  if (!canvas || !segmentScores || typeof Chart === 'undefined') return;
  
  const SEG_NAMES = {
    1: 'Info Proc.', 2: 'Situational', 3: 'Self-Monitor',
    4: 'Social/ToM', 5: 'Existential', 6: 'Learning/Adapt',
    7: 'Self-Knowledge', 8: 'Metacognition', 9: 'Emotional',
    10: 'Temp/Spatial', 11: 'Goal-Directed', 12: 'Autonomy', 13: 'Moral/Ethical'
  };

  const sorted = Object.entries(segmentScores).sort((a, b) => parseInt(a[0]) - parseInt(b[0]));
  const labels = sorted.map(([k]) => SEG_NAMES[k] || `Seg ${k}`);
  const data = sorted.map(([, v]) => typeof v === 'number' ? parseFloat(v.toFixed(2)) : 0);
  if (window._barChart) { try { window._barChart.destroy(); } catch (_) { } }
  window._barChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Avg Score (0–4)', data,
        backgroundColor: 'rgba(16,185,129,0.5)',
        borderColor: '#10b981',
        borderWidth: 1, borderRadius: 5,
        hoverBackgroundColor: 'rgba(52,211,153,0.75)',
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 4, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#475569' } },
        x: { ticks: { color: '#475569', font: { size: 9 } }, grid: { display: false } },
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `Score: ${ctx.raw} / 4` } },
      },
    },
  });
}

function drawGauge(score) {
  const canvas = el('gaugeChart');
  const centerPct = el('gaugeCenterPct');
  if (!canvas || typeof Chart === 'undefined') return;
  const pct = Math.max(0, Math.min(100, (score / 133.3) * 100));
  
  // Update Center Typography
  if (centerPct) centerPct.textContent = `${pct.toFixed(0)}%`;

  // Create Premium Canvas Gradient
  const ctx = canvas.getContext('2d');
  let color = C.danger;
  if (pct > 70) {
    const gradient = ctx.createLinearGradient(0, 0, canvas.width || 200, 0);
    gradient.addColorStop(0, '#059669'); // Emerald Dark
    gradient.addColorStop(1, '#34d399'); // Emerald Light (Neon)
    color = gradient;
  } else if (pct > 40) {
    color = C.warning;
  }

  if (window._gaugeChart) { try { window._gaugeChart.destroy(); } catch (_) { } }
  window._gaugeChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [pct, 100 - pct],
        backgroundColor: [color, 'rgba(255,255,255,0.05)'],
        borderWidth: 0, 
        borderRadius: 20, // Rounded pill ends
      }],
    },
    options: {
      cutout: '78%', 
      circumference: 260, 
      rotation: -130, // Sweeping arc
      responsive: true, 
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    },
  });
}

// ── Session history ───────────────────────────────────────────────────────────
async function loadSessions() {
  const container = el('sessionHistoryList');
  if (!container) return;
  container.innerHTML = '<div class="spinner"></div>';
  try {
    const sessions = await API.get('/sessions');
    if (!sessions.length) {
      container.innerHTML = '<div class="alert alert-info">No sessions yet. Complete an evaluation first.</div>';
      return;
    }
    container.innerHTML = sessions.map(s => {
      const adj = s.adjusted_score ?? s.overall_score ?? null;
      const score = adj !== null ? adj.toFixed(1) : '—';
      const date = s.created_at ? new Date(s.created_at).toLocaleDateString() : '?';
      return `
        <div class="sess-item">
          <div class="sess-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--em)" stroke-width="2" stroke-linecap="round">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/>
            </svg>
          </div>
          <div class="sess-info">
            <div class="sess-model">${escHtml(s.model_name || 'Unknown Model')} ${escHtml(s.model_version || '')}</div>
            <div class="sess-meta">${escHtml(s.evaluation_title || '')} · ${date} · ${escHtml(s.reliability_label || 'Not evaluated')}</div>
          </div>
          <div class="sess-score">${score}</div>
          <div class="sess-actions">
            <button class="btn btn-success btn-sm" onclick="loadSessionResult('${s.session_uid}')">Load</button>
            <a class="btn btn-ghost btn-sm" href="/api/export/json/${s.session_uid}" download>JSON</a>
            <a class="btn btn-ghost btn-sm" href="/api/export/csv/${s.session_uid}"  download>CSV</a>
            <a class="btn btn-ghost btn-sm" href="/api/export/report/${s.session_uid}" target="_blank">Report</a>
            <button class="btn btn-danger btn-sm" onclick="deleteSession('${s.session_uid}')">Del</button>
          </div>
        </div>`;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div class="alert alert-danger">Error: ${escHtml(e.message)}</div>`;
  }
}

async function loadSessionResult(uid) {
  showLoading('Loading session…');
  try {
    const session = await API.get(`/sessions/${uid}`);
    if (!session.full_analysis && !session.indicator_scores) {
      showToast('This session has no evaluation results yet.', 'warning');
      return;
    }
    const fa = session.full_analysis || {};
    const result = {
      session_uid: uid,
      adjusted_score: session.adjusted_score ?? 0,
      overall_score: session.overall_score ?? 0,
      indicator_scores: session.indicator_scores ?? {},
      reliability_label: session.reliability_label ?? 'N/A',
      reliability_score: session.reliability_score ?? 0,
      narrative: session.narrative_summary ?? '',
      strengths: fa.strengths ?? [],
      weaknesses: fa.weaknesses ?? [],
      contradiction_analysis: fa.contradiction_analysis ?? {},
      tone_analysis: fa.tone_analysis ?? {},
      sentiment_analysis: fa.sentiment_analysis ?? {},
      dataset_similarity: fa.dataset_similarity ?? {},
      porter_result: session.porter_result ?? {},
      adjustment_log: fa.adjustment_log ?? [],
      warnings: fa.warnings ?? [],
    };
    STATE.evaluationResult = result;
    STATE.sessionUid = uid;
    updateSessionInfo();
    renderDashboard(result);
    closeModal('historyModal');
    openPanel('p4', true);
    scrollToPanel('p4');
    showToast('Session loaded!');
  } catch (e) {
    showToast('Error loading session: ' + e.message, 'error');
  } finally {
    hideLoading();
  }
}

async function deleteSession(uid) {
  if (!confirm('Delete this session permanently?')) return;
  try {
    await API.delete(`/sessions/${uid}`);
    showToast('Session deleted.');
    loadSessions();
    if (STATE.sessionUid === uid) {
      STATE.sessionUid = null;
      STATE.evaluationResult = null;
      updateSessionInfo();
    }
  } catch (e) {
    showToast('Delete error: ' + e.message, 'error');
  }
}

// ── Exports ───────────────────────────────────────────────────────────────────
function exportCurrentJson() {
  const uid = STATE.sessionUid || STATE.evaluationResult?.session_uid;
  if (!uid) { showToast('No session to export.', 'warning'); return; }
  const a = document.createElement('a');
  a.href = `/api/export/json/${uid}`;
  a.download = `aci_eval_${uid.slice(0, 8)}.json`;
  a.click();
}
function exportCurrentCsv() {
  const uid = STATE.sessionUid || STATE.evaluationResult?.session_uid;
  if (!uid) { showToast('No session to export.', 'warning'); return; }
  const a = document.createElement('a');
  a.href = `/api/export/csv/${uid}`;
  a.download = `aci_eval_${uid.slice(0, 8)}.csv`;
  a.click();
}
function printReport() {
  const uid = STATE.sessionUid || STATE.evaluationResult?.session_uid;
  if (!uid) { showToast('No session to export.', 'warning'); return; }
  window.open(`/api/export/report/${uid}`, '_blank');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  openPanel('p1', true);
  updateWorkflowProgress(1, 5);
  updateSessionInfo();
});
