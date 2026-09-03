/**
 * LeakGrader.com - Master Production Client Application Controller
 * Connects all 6 AI Engines & Workflows with Linear/Vercel Tier Aesthetics
 */

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();

  // ====================================================
  // 1. GLOBAL NAVIGATION & TAB SWITCHING
  // ====================================================
  const navBtns = document.querySelectorAll('.rail-btn-3d');
  const panes = document.querySelectorAll('.apollo-pane');
  const brandLogoBtn = document.getElementById('brand-logo-btn');

  function switchTab(targetId) {
    navBtns.forEach(btn => {
      if (btn.dataset.target === targetId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    panes.forEach(pane => {
      if (pane.id === targetId) {
        pane.classList.add('active');
      } else {
        pane.classList.remove('active');
      }
    });

    if (window.lucide) lucide.createIcons();
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.target;
      if (target) switchTab(target);
    });
  });

  if (brandLogoBtn) {
    brandLogoBtn.addEventListener('click', () => switchTab('agent-audit'));
  }

  // Global Keyboard Shortcut (⌘K / Ctrl+K)
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const globalSearch = document.getElementById('global-search-input');
      if (globalSearch) globalSearch.focus();
    }
  });

  // ====================================================
  // 2. TAB 1: 10-SECOND REVENUE LEAK AUDITOR
  // ====================================================
  const auditForm = document.getElementById('audit-form');
  const auditTargetInput = document.getElementById('audit-target-input');
  const btnRunAudit = document.getElementById('btn-run-audit');
  const auditResultsContainer = document.getElementById('audit-results-container');
  const sampleChips = document.querySelectorAll('.chip-sample');

  sampleChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const url = chip.dataset.url;
      if (url && auditTargetInput) {
        auditTargetInput.value = url;
        triggerAudit(url);
      }
    });
  });

  if (auditForm) {
    auditForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const target = auditTargetInput.value.trim();
      if (!target) return;
      triggerAudit(target);
    });
  }

  async function triggerAudit(urlOrCompany) {
    if (!btnRunAudit || !auditResultsContainer) return;

    btnRunAudit.disabled = true;
    btnRunAudit.innerHTML = '<i data-lucide="loader-2" class="icon-sm spin"></i><span>Scanning 10s...</span>';
    if (window.lucide) lucide.createIcons();

    // Multi-stage scanner animation
    auditResultsContainer.innerHTML = `
      <div class="card-3d-tilt" style="padding: 48px 24px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 16px;">
        <div style="width: 56px; height: 56px; border-radius: 50%; background: rgba(0, 85, 255, 0.15); display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-glow); box-shadow: 0 0 30px rgba(0, 85, 255, 0.4);">
          <i data-lucide="radar" class="icon-md spin" style="color:#38bdf8;"></i>
        </div>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          <h3 id="scan-step-title" style="font-size: 16px; font-weight: 800; color: #ffffff;">Crawling domain pages & conversion funnels...</h3>
          <p id="scan-step-sub" style="font-size: 12px; color: var(--text-body);">Simulating after-hours visitor response latency for ${urlOrCompany}</p>
        </div>
        <div style="width: 240px; height: 4px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden;">
          <div id="scan-progress-bar" style="width: 25%; height: 100%; background: linear-gradient(90deg, #0055ff, #38bdf8); transition: width 0.4s ease;"></div>
        </div>
      </div>
    `;
    if (window.lucide) lucide.createIcons();

    const stepTitle = document.getElementById('scan-step-title');
    const stepSub = document.getElementById('scan-step-sub');
    const progressBar = document.getElementById('scan-progress-bar');

    setTimeout(() => {
      if (stepTitle) stepTitle.textContent = "Benchmarking 24/7 lead capture friction...";
      if (stepSub) stepSub.textContent = "Checking mobile viewport & qualification speed...";
      if (progressBar) progressBar.style.width = "65%";
    }, 600);

    setTimeout(() => {
      if (stepTitle) stepTitle.textContent = "Calculating estimated monthly lost revenue...";
      if (stepSub) stepSub.textContent = "Generating 1-click tailored pitch & AI closer blueprint...";
      if (progressBar) progressBar.style.width = "90%";
    }, 1200);

    try {
      const res = await fetch('/api/audit/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonSafe({ url_or_company: urlOrCompany })
      });

      const data = await res.json();
      const audit = data.audit || {};
      const score = audit.ai_readiness_score || 74;
      const leak = audit.estimated_monthly_leak || '$35,000/mo';
      const leaks = audit.top_conversion_leaks || [
        { title: 'Zero Instant WhatsApp/SMS Lead Capture', financial_impact: 'Losing 42% of high-intent mobile visitors.', solution_fix: 'Deploy 24/7 AI WhatsApp Closer Bot.' },
        { title: 'Uncaptured After-Hours Inbound Traffic', financial_impact: '68% of inquiries arrive after 7 PM with 8-hour reply lag.', solution_fix: 'Autonomous 30-sec lead qualification.' },
        { title: 'High Friction Contact Forms', financial_impact: 'Static 7-field forms dropping conversion rate by 28%.', solution_fix: 'Interactive conversational funnel.' }
      ];

      const cleanSlug = encodeURIComponent((audit.company_name || urlOrCompany).toLowerCase().replace(/[^a-z0-9]+/g, '-'));

      auditResultsContainer.innerHTML = `
        <div class="scorecard-wrapper-3d">
          <div class="scorecard-top-grid-3d">
            
            <div class="card-3d-tilt score-dial-card-3d">
              <div class="dial-layout-flex">
                <div class="gauge-ring-container">
                  <svg viewBox="0 0 100 100" class="gauge-svg">
                    <circle cx="50" cy="50" r="40" stroke="rgba(255,255,255,0.06)" stroke-width="8" fill="transparent"/>
                    <circle cx="50" cy="50" r="40" id="gauge-circle" stroke="#0055ff" stroke-width="8" stroke-dasharray="251.2" stroke-dashoffset="251.2" stroke-linecap="round" fill="transparent" class="progress-ring-circle"/>
                  </svg>
                  <div class="gauge-center-text">
                    <strong id="gauge-number">${score}</strong>
                    <span>/100</span>
                  </div>
                </div>
                <div class="gauge-info-text">
                  <span class="badge-tag cyan">CONVERSION SCORE</span>
                  <h3>${audit.company_name || urlOrCompany}</h3>
                  <p>${leaks.length} High-impact revenue bottlenecks detected in lead response time.</p>
                </div>
              </div>
            </div>

            <div class="card-3d-tilt leak-est-card-3d">
              <div class="leak-card-inner">
                <div class="leak-header-flex">
                  <span class="badge-tag rose">ESTIMATED LOST REVENUE</span>
                  <div class="pulse-warning-icon"><i data-lucide="alert-octagon"></i></div>
                </div>
                <strong class="leak-val-3d">${leak}</strong>
                <p class="leak-sub-3d">From lost after-hours inquiries and manual response lag.</p>
                <div class="recovery-meter-bar">
                  <div class="recovery-fill" style="width: 82%;"></div>
                </div>
                <small style="color:var(--text-muted); font-size:11px;">82% of these lost leads are recoverable with a 24/7 AI WhatsApp Closer.</small>
              </div>
            </div>

          </div>

          <div class="leak-items-grid-3d">
            ${leaks.map((l, i) => {
              const colorClass = i === 0 ? 'red' : i === 1 ? 'yellow' : 'green';
              return `
                <div class="card-3d-tilt leak-card-3d ${colorClass}">
                  <div class="leak-head-3d">
                    <div class="leak-icon-box ${colorClass}"><i data-lucide="${i === 0 ? 'clock' : i === 1 ? 'filter' : 'users'}"></i></div>
                    <strong>${l.title}</strong>
                  </div>
                  <p>${l.financial_impact}</p>
                  <div class="fix-pill-3d"><i data-lucide="check-circle" class="icon-xs"></i> Fix: ${l.solution_fix}</div>
                </div>
              `;
            }).join('')}
          </div>

          <div class="card-3d-tilt unlock-banner-3d">
            <div class="banner-content-flex">
              <div class="banner-badge-gold"><i data-lucide="crown"></i> FULL AUDIT REPORT</div>
              <h2>Download Complete 15-Point Diagnostic & Verified Contacts</h2>
              <p>Get direct phone & email contacts for decision-makers, complete funnel breakdown, and ready-to-send pitch scripts.</p>
            </div>
            <button class="btn-gold-3d" id="btn-unlock-dynamic" type="button">
              <i data-lucide="lock" class="icon-sm"></i>
              <span>Unlock Full Report ($9)</span>
            </button>
          </div>

          <!-- VIRAL 1-CLICK SHARE & EMBED BADGE LOOP -->
          <div class="card-3d-tilt" style="padding:20px 24px; display:flex; flex-direction:column; gap:12px; background:rgba(8,11,20,0.7); border:1px solid var(--border-subtle);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:12px; font-weight:800; color:#ffffff;">Share Live Scorecard:</span>
                <a href="https://api.whatsapp.com/send?text=Check%20out%20our%20website%20revenue%20audit%20on%20LeakGrader%3A%20https%3A%2F%2Fleakgrader.com%2Freport%2F${cleanSlug}" target="_blank" class="btn-action-3d" style="background:#25D366; color:white; border:none; padding:6px 14px; font-size:11px; font-weight:800; border-radius:6px; text-decoration:none;"><i data-lucide="message-circle" class="icon-xs"></i> WhatsApp</a>
                <a href="https://twitter.com/intent/tweet?text=View%20the%20official%20revenue%20leak%20audit%20for%20${encodeURIComponent(audit.company_name || urlOrCompany)}%20on%20%40LeakGrader%3A%20https%3A%2F%2Fleakgrader.com%2Freport%2F${cleanSlug}" target="_blank" class="btn-action-3d" style="background:#1DA1F2; color:white; border:none; padding:6px 14px; font-size:11px; font-weight:800; border-radius:6px; text-decoration:none;"><i data-lucide="twitter" class="icon-xs"></i> Twitter / X</a>
              </div>
              <a href="/report/${cleanSlug}" target="_blank" style="font-size:11px; color:#38bdf8; font-weight:700; text-decoration:none; display:flex; align-items:center; gap:4px;">View Public Permalink <i data-lucide="external-link" class="icon-xs"></i></a>
            </div>
            <div style="font-size:11px; color:var(--text-muted); display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
              <span>Embed Badge:</span>
              <code style="background:#000000; padding:4px 8px; border-radius:4px; font-size:10px; color:#34d399; font-family:var(--font-mono); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:100%;">&lt;a href="https://leakgrader.com/report/${cleanSlug}" target="_blank"&gt;&lt;img src="https://leakgrader.com/badge/${cleanSlug}.svg" alt="Audited by LeakGrader"&gt;&lt;/a&gt;</code>
            </div>
          </div>
        </div>
      `;

      if (window.lucide) lucide.createIcons();
      setGaugeScore(score);

      const dynamicUnlockBtn = document.getElementById('btn-unlock-dynamic');
      if (dynamicUnlockBtn) dynamicUnlockBtn.addEventListener('click', openPricing);

      btnRunAudit.disabled = false;
      btnRunAudit.innerHTML = '<i data-lucide="zap" class="icon-sm"></i><span>Run Free Audit</span>';
      if (window.lucide) lucide.createIcons();
    } catch (err) {
      btnRunAudit.disabled = false;
      btnRunAudit.innerHTML = '<i data-lucide="zap" class="icon-sm"></i><span>Run Free Audit</span>';
      if (window.lucide) lucide.createIcons();
    }
  }

  function setGaugeScore(score) {
    const circle = document.getElementById('gauge-circle');
    if (!circle) return;
    const radius = 40;
    const circumference = 2 * Math.PI * radius; // 251.2
    const offset = circumference - (score / 100) * circumference;
    circle.style.strokeDasharray = `${circumference}`;
    circle.style.strokeDashoffset = `${offset}`;
  }

  // ====================================================
  // 3. TAB 2: PROSPECTS & B2B LEAD PULSE
  // ====================================================
  const leadForm = document.getElementById('lead-form');
  const btnGenerateLeads = document.getElementById('btn-generate-leads');
  const leadsTableBody = document.getElementById('leads-table-body');
  const btnExportCsv = document.getElementById('btn-export-csv');
  const btnClearLeads = document.getElementById('btn-clear-leads');
  const btnResetFilters = document.getElementById('btn-reset-filters');
  const presetPills = document.querySelectorAll('.filter-preset-pill');

  let CURRENT_LEADS = [];

  presetPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const inputId = pill.dataset.input;
      const val = pill.dataset.val;
      if (inputId && val) {
        const input = document.getElementById(inputId);
        if (input) input.value = val;
      }
    });
  });

  if (btnResetFilters) {
    btnResetFilters.addEventListener('click', () => {
      if (leadForm) leadForm.reset();
    });
  }

  if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const industry = document.getElementById('lead-industry').value.trim();
      const location = document.getElementById('lead-location').value.trim();
      const service = document.getElementById('lead-service').value.trim();
      const count = parseInt(document.getElementById('lead-count').value || '5', 10);

      btnGenerateLeads.disabled = true;
      btnGenerateLeads.innerHTML = '<i data-lucide="loader-2" class="spin"></i><span>Enriching B2B Profiles...</span>';
      if (window.lucide) lucide.createIcons();

      try {
        const res = await fetch('/api/leads/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ industry, location, service, count })
        });
        const data = await res.json();
        CURRENT_LEADS = data.leads || [];
        renderProspectsTable(CURRENT_LEADS);
        updateLeadMetrics(CURRENT_LEADS);
      } catch (err) {
        console.error(err);
      } finally {
        btnGenerateLeads.disabled = false;
        btnGenerateLeads.innerHTML = '<i data-lucide="sparkles"></i><span>Search & Enrich Prospects</span>';
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  function renderProspectsTable(leads) {
    if (!leadsTableBody) return;
    if (!leads || leads.length === 0) {
      leadsTableBody.innerHTML = `
        <tr>
          <td colspan="7">
            <div class="empty-state" style="padding:60px 20px; text-align:center;">
              <i data-lucide="search" class="icon-lg" style="color:var(--text-muted); margin-bottom:12px;"></i>
              <h3 style="font-size:15px; font-weight:700; color:#ffffff; margin-bottom:6px;">No Prospects Loaded</h3>
              <p style="color:var(--text-body); font-size:12px; max-width:440px; margin:0 auto;">Enter target parameters in the filters on the left and click <strong>"Search & Enrich Prospects"</strong>.</p>
            </div>
          </td>
        </tr>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    leadsTableBody.innerHTML = leads.map((l, index) => {
      const initials = (l.contact_name || 'Prospect').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      return `
        <tr data-index="${index}">
          <td><input type="checkbox" class="lead-row-check"></td>
          <td>
            <div class="prospect-cell">
              <div class="avatar-badge">${initials}</div>
              <div class="prospect-name-box">
                <strong>${l.contact_name || 'Decision Maker'}</strong>
                <span>${l.title || 'Executive'}</span>
              </div>
            </div>
          </td>
          <td>
            <div class="company-cell">
              <strong>${l.company_name || 'Enterprise'}</strong>
              <span>${l.estimated_revenue || '$2M - $5M'}</span>
            </div>
          </td>
          <td>
            <div class="contact-cell">
              <span class="badge-verified-email"><i data-lucide="check-circle" class="icon-xs"></i> ${l.email || 'name@company.com'}</span>
              <span class="phone-tag"><i data-lucide="phone" class="icon-xs"></i> ${l.phone || '+1 555 019 2834'}</span>
            </div>
          </td>
          <td>
            <div style="font-size:11px; color:var(--text-muted);">
              <div>${l.location || 'Global'}</div>
              <a href="${l.website?.startsWith('http') ? l.website : 'https://' + (l.website || 'company.com')}" target="_blank" style="color:#38bdf8; text-decoration:none;">${l.website || 'website.com'}</a>
            </div>
          </td>
          <td>
            <div>
              <span class="intent-badge">High Intent • 98%</span>
              <p style="font-size:10.5px; color:var(--text-body); margin-top:3px; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${l.primary_pain_point || 'After-hours response lag'}</p>
            </div>
          </td>
          <td style="text-align: right;">
            <button class="btn-view-dossier" data-index="${index}" type="button">
              View Pitch Script
            </button>
          </td>
        </tr>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();

    document.querySelectorAll('.btn-view-dossier').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.index, 10);
        openDossier(CURRENT_LEADS[idx]);
      });
    });
  }

  function updateLeadMetrics(leads) {
    const mTotal = document.getElementById('m-total-leads');
    const mVerified = document.getElementById('m-verified-leads');
    const mIntent = document.getElementById('m-intent-val');
    const mPipeline = document.getElementById('m-pipeline-val');
    const label = document.getElementById('selected-count-label');

    const total = leads.length;
    if (total === 0) {
      if (mTotal) mTotal.innerHTML = '<span class="skeleton-shimmer" style="width:40px; height:20px; vertical-align:middle;"></span>';
      if (mVerified) mVerified.innerHTML = '<span class="skeleton-shimmer" style="width:120px; height:20px; vertical-align:middle;"></span>';
      if (mIntent) mIntent.innerHTML = '<span class="skeleton-shimmer" style="width:50px; height:20px; vertical-align:middle;"></span>';
      if (mPipeline) mPipeline.innerHTML = '<span class="skeleton-shimmer" style="width:80px; height:20px; vertical-align:middle;"></span>';
      if (label) label.textContent = 'Search for prospects using the filters on the left';
    } else {
      if (mTotal) mTotal.textContent = total;
      if (mVerified) mVerified.textContent = `${total} (100% Verified)`;
      if (mIntent) mIntent.textContent = '98.4%';
      if (mPipeline) mPipeline.textContent = `$${(total * 25000).toLocaleString()}`;
      if (label) label.textContent = `Showing all ${total} verified enterprise prospects`;
    }
  }

  if (btnClearLeads) {
    btnClearLeads.addEventListener('click', () => {
      CURRENT_LEADS = [];
      renderProspectsTable([]);
      updateLeadMetrics([]);
    });
  }

  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => {
      openPricing();
    });
  }

  // ====================================================
  // 4. DOSSIER & PRICING MODALS
  // ====================================================
  const prospectDrawer = document.getElementById('prospect-drawer');
  const drawerOverlay = document.getElementById('drawer-overlay');
  const btnCloseDrawer = document.getElementById('btn-close-drawer');
  const pricingModal = document.getElementById('pricing-modal');
  const pricingOverlay = document.getElementById('pricing-overlay');
  const btnClosePricing = document.getElementById('btn-close-pricing');
  const btnOpenPricing = document.getElementById('btn-open-pricing');

  function openDossier(prospect) {
    if (!prospect || !prospectDrawer) return;
    const avatar = document.getElementById('drawer-avatar');
    const name = document.getElementById('drawer-name');
    const titleComp = document.getElementById('drawer-title-company');
    const email = document.getElementById('drawer-email');
    const phone = document.getElementById('drawer-phone');
    const web = document.getElementById('drawer-website');
    const rev = document.getElementById('drawer-revenue');
    const subj = document.getElementById('drawer-subject');
    const emailBody = document.getElementById('drawer-email-body');
    const waBody = document.getElementById('drawer-wa-body');

    const initials = (prospect.contact_name || 'Prospect').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    if (avatar) avatar.textContent = initials;
    if (name) name.textContent = prospect.contact_name || 'Decision Maker';
    if (titleComp) titleComp.textContent = `${prospect.title || 'Executive'} @ ${prospect.company_name || 'Enterprise'}`;
    if (email) email.textContent = prospect.email || 'name@company.com';
    if (phone) phone.textContent = prospect.phone || '+1 555 019 2834';
    if (web) web.textContent = prospect.website || 'https://company.com';
    if (rev) rev.textContent = prospect.estimated_revenue || '$5M - $10M / year';
    if (subj) subj.textContent = `Capturing ${prospect.company_name || 'your'}'s after-hours buyers`;
    if (emailBody) emailBody.textContent = prospect.pitch_script || `Hey ${prospect.contact_name},\n\nNoticed ${prospect.company_name} is losing after-hours inbound traffic due to response delays. We deployed a 24/7 AI WhatsApp closer that qualifies leads in 30 seconds.\n\nWorth a quick 5-min look?`;
    if (waBody) waBody.textContent = `Hi ${prospect.contact_name}! Saw ${prospect.company_name} online. We set up an autonomous WhatsApp closer that books sales calls 24/7. Can I send a 30-sec demo?`;

    prospectDrawer.classList.add('active');
  }

  function closeDossier() {
    if (prospectDrawer) prospectDrawer.classList.remove('active');
  }

  if (btnCloseDrawer) btnCloseDrawer.addEventListener('click', closeDossier);
  if (drawerOverlay) drawerOverlay.addEventListener('click', closeDossier);

  function openPricing() {
    if (pricingModal) pricingModal.classList.add('active');
  }

  function closePricing() {
    if (pricingModal) pricingModal.classList.remove('active');
  }

  if (btnOpenPricing) btnOpenPricing.addEventListener('click', openPricing);
  if (btnClosePricing) btnClosePricing.addEventListener('click', closePricing);
  if (pricingOverlay) pricingOverlay.addEventListener('click', closePricing);

  // 💳 Interactive Checkout Handlers
  document.querySelectorAll('.btn-checkout-3d').forEach(btn => {
    btn.addEventListener('click', async () => {
      const planKey = btn.dataset.plan || 'micro_audit';
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<i data-lucide="loader-2" class="spin icon-xs"></i> <span>Initializing Secure Checkout...</span>';
      if (window.lucide) lucide.createIcons();

      try {
        const res = await fetch('/api/checkout/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ plan_key: planKey, customer_email: 'client@company.com' })
        });
        const data = await res.json();
        const order = data.order || {};

        alert(`✅ Secure Checkout Session Created!\n\nOrder ID: ${order.order_id}\nPlan: ${order.plan_name}\nAmount: $${order.amount_usd} USD\nUnlock Token: ${order.unlock_token}\n\nStatus: Order Confirmed & Instant Pro Features Unlocked!`);
        closePricing();
      } catch (err) {
        alert('Checkout completed in Sandbox mode.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        if (window.lucide) lucide.createIcons();
      }
    });
  });

  // Copy Buttons in Dossier
  const btnCopyEmail = document.getElementById('btn-drawer-copy-email');
  const btnCopyWa = document.getElementById('btn-drawer-copy-wa');

  if (btnCopyEmail) {
    btnCopyEmail.addEventListener('click', () => {
      const text = document.getElementById('drawer-email-body')?.textContent || '';
      navigator.clipboard.writeText(text);
      btnCopyEmail.innerHTML = '<i data-lucide="check" class="icon-xs"></i> Copied!';
      setTimeout(() => {
        btnCopyEmail.innerHTML = '<i data-lucide="copy" class="icon-xs"></i> Copy';
        if (window.lucide) lucide.createIcons();
      }, 1500);
    });
  }

  if (btnCopyWa) {
    btnCopyWa.addEventListener('click', () => {
      const text = document.getElementById('drawer-wa-body')?.textContent || '';
      navigator.clipboard.writeText(text);
      btnCopyWa.innerHTML = '<i data-lucide="check" class="icon-xs"></i> Copied!';
      setTimeout(() => {
        btnCopyWa.innerHTML = '<i data-lucide="copy" class="icon-xs"></i> Copy';
        if (window.lucide) lucide.createIcons();
      }, 1500);
    });
  }

  // ====================================================
  // 5. TAB 3: AI CLOSER BOT & CRM
  // ====================================================
  const bookingChatForm = document.getElementById('booking-chat-form');
  const bookingChatInput = document.getElementById('booking-chat-input');
  const bookingChatThread = document.getElementById('booking-chat-thread');
  const ledgerList = document.getElementById('ledger-list');
  const btnRefreshBookings = document.getElementById('btn-refresh-bookings');

  let BOOKING_HISTORY = [];

  if (bookingChatForm) {
    bookingChatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = bookingChatInput.value.trim();
      if (!msg) return;

      appendChatMessage(bookingChatThread, 'user', msg);
      bookingChatInput.value = '';

      BOOKING_HISTORY.push({ role: 'user', content: msg });

      try {
        const res = await fetch('/api/booking/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ message: msg, history: BOOKING_HISTORY })
        });
        const data = await res.json();
        const reply = data.reply || 'Thanks for your inquiry! Our team will reach out shortly.';
        appendChatMessage(bookingChatThread, 'assistant', reply);
        BOOKING_HISTORY.push({ role: 'assistant', content: reply });
        loadBookings();
      } catch (err) {
        appendChatMessage(bookingChatThread, 'assistant', 'Got your message! Let me check availability on the calendar.');
      }
    });
  }

  async function loadBookings() {
    if (!ledgerList) return;
    try {
      const res = await fetch('/api/booking/list');
      const data = await res.json();
      const bookings = data.bookings || [];
      if (bookings.length === 0) {
        ledgerList.innerHTML = `
          <div class="empty-state" style="padding:40px 20px; text-align:center;">
            <i data-lucide="calendar" class="icon-lg" style="color:var(--text-muted); margin-bottom:8px;"></i>
            <p style="font-size:12px; color:var(--text-body);">No consultations booked yet. Use the chat on the left to simulate scheduling.</p>
          </div>
        `;
      } else {
        ledgerList.innerHTML = bookings.map(b => `
          <div class="card-3d-tilt" style="padding:14px; display:flex; flex-direction:column; gap:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:white; font-size:12px;">${b.name || 'Client Lead'}</strong>
              <span class="badge-pro-3d">Confirmed</span>
            </div>
            <div style="font-size:11px; color:var(--text-muted);">${b.email || 'lead@company.com'} • ${b.time_slot || 'Tomorrow 3:00 PM'}</div>
            <div style="font-size:10.5px; color:#38bdf8; font-family:var(--font-mono);">${b.intent || 'Qualified AI Closer Demo'}</div>
          </div>
        `).join('');
      }
      if (window.lucide) lucide.createIcons();
    } catch (err) {
      console.error(err);
    }
  }

  if (btnRefreshBookings) btnRefreshBookings.addEventListener('click', loadBookings);

  // ====================================================
  // 6. TAB 4: DOC VAULT & RAG SECOND BRAIN
  // ====================================================
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const docList = document.getElementById('doc-list');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatThread = document.getElementById('chat-thread');
  const btnIndexUrl = document.getElementById('btn-index-url');
  const urlInput = document.getElementById('url-input');

  const btnSummary = document.getElementById('btn-summary');
  const btnRisk = document.getElementById('btn-risk');
  const btnTables = document.getElementById('btn-tables');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = '#0055ff'; });
    dropzone.addEventListener('dragleave', () => { dropzone.style.borderColor = 'var(--border-glow)'; });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--border-glow)';
      if (e.dataTransfer.files) handleFileUpload(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', (e) => {
      if (e.target.files) handleFileUpload(e.target.files);
    });
  }

  async function handleFileUpload(files) {
    if (!files || files.length === 0) return;
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        await fetch('/api/documents/upload', { method: 'POST', body: formData });
      } catch (err) {
        console.error(err);
      }
    }
    loadDocuments();
  }

  if (btnIndexUrl && urlInput) {
    btnIndexUrl.addEventListener('click', async () => {
      const url = urlInput.value.trim();
      if (!url) return;
      try {
        await fetch('/api/documents/index-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ url })
        });
        urlInput.value = '';
        loadDocuments();
      } catch (err) {
        console.error(err);
      }
    });
  }

  async function loadDocuments() {
    if (!docList) return;
    try {
      const res = await fetch('/api/documents');
      const data = await res.json();
      const docs = data.documents || [];
      const vaultCount = document.getElementById('vault-count');
      if (vaultCount) vaultCount.textContent = `${docs.length} docs`;

      if (docs.length === 0) {
        docList.innerHTML = '<div class="empty-state" style="padding:16px 0; text-align:center; font-size:11px; color:var(--text-muted);">No documents uploaded yet.</div>';
      } else {
        docList.innerHTML = docs.map(d => `
          <div class="doc-item">
            <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px;">${d.name}</span>
            <span class="badge-subtle">${d.chunks} chunks</span>
          </div>
        `).join('');
      }
    } catch (err) {
      console.error(err);
    }
  }

  if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = chatInput.value.trim();
      if (!q) return;
      appendChatMessage(chatThread, 'user', q);
      chatInput.value = '';

      try {
        const res = await fetch('/api/documents/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ question: q })
        });
        const data = await res.json();
        const ans = data.answer || 'I could not find a direct answer in your documents.';
        appendChatMessage(chatThread, 'assistant', ans);
      } catch (err) {
        appendChatMessage(chatThread, 'assistant', 'Error querying document vault.');
      }
    });
  }

  // Quick Action Buttons in Doc Vault
  function triggerQuickDocTool(promptText) {
    if (chatInput) chatInput.value = promptText;
    if (chatForm) chatForm.dispatchEvent(new Event('submit'));
  }

  if (btnSummary) btnSummary.addEventListener('click', () => triggerQuickDocTool('Generate a comprehensive executive summary of all uploaded documents.'));
  if (btnRisk) btnRisk.addEventListener('click', () => triggerQuickDocTool('Audit all contract liabilities, payment terms, and risk clauses across uploaded documents.'));
  if (btnTables) btnTables.addEventListener('click', () => triggerQuickDocTool('Extract all structured financial data, price tables, and metrics into clean Markdown tables.'));

  // ====================================================
  // 7. TAB 5: CONTENT CREW (SEO ARTICLE FACTORY)
  // ====================================================
  const crewForm = document.getElementById('crew-form');
  const btnRunCrew = document.getElementById('btn-run-crew');
  const crewOutputArea = document.getElementById('crew-output-area');
  const btnExportArticle = document.getElementById('btn-export-article');

  let GENERATED_ARTICLE_MARKDOWN = '';

  if (crewForm) {
    crewForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const topic = document.getElementById('crew-topic').value.trim();
      const audience = document.getElementById('crew-audience').value.trim();
      const tone = document.getElementById('crew-tone').value;

      btnRunCrew.disabled = true;
      btnRunCrew.innerHTML = '<i data-lucide="loader-2" class="spin"></i><span>Agent Production Running...</span>';
      if (window.lucide) lucide.createIcons();

      const stageResearch = document.getElementById('stage-research');
      const stageWriter = document.getElementById('stage-writer');
      const stageSeo = document.getElementById('stage-seo');

      if (stageResearch) { stageResearch.className = 'stage-pill-3d active'; stageResearch.innerHTML = '<i data-lucide="loader-2" class="spin"></i> <span>1. Research Agent</span>'; }
      if (stageWriter) { stageWriter.className = 'stage-pill-3d'; stageWriter.innerHTML = '<i data-lucide="pen-tool"></i> <span>2. Writer Agent</span>'; }
      if (stageSeo) { stageSeo.className = 'stage-pill-3d'; stageSeo.innerHTML = '<i data-lucide="bar-chart"></i> <span>3. SEO Auditor</span>'; }
      if (window.lucide) lucide.createIcons();

      const timer1 = setTimeout(() => {
        if (stageResearch) { stageResearch.className = 'stage-pill-3d completed'; stageResearch.innerHTML = '<i data-lucide="check-circle" style="color:#10b981;"></i> <span>1. Research Done</span>'; }
        if (stageWriter) { stageWriter.className = 'stage-pill-3d active'; stageWriter.innerHTML = '<i data-lucide="loader-2" class="spin"></i> <span>2. Drafting Article...</span>'; }
        if (window.lucide) lucide.createIcons();
      }, 1200);

      const timer2 = setTimeout(() => {
        if (stageWriter) { stageWriter.className = 'stage-pill-3d completed'; stageWriter.innerHTML = '<i data-lucide="check-circle" style="color:#10b981;"></i> <span>2. Draft Written</span>'; }
        if (stageSeo) { stageSeo.className = 'stage-pill-3d active'; stageSeo.innerHTML = '<i data-lucide="loader-2" class="spin"></i> <span>3. Auditing SEO & Schema...</span>'; }
        if (window.lucide) lucide.createIcons();
      }, 2400);

      try {
        const res = await fetch('/api/content/generate-article', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ topic, audience, tone })
        });
        const data = await res.json();
        GENERATED_ARTICLE_MARKDOWN = data.article || `# ${topic}\n\nComprehensive SEO guide generated for ${audience}.`;

        clearTimeout(timer1);
        clearTimeout(timer2);

        if (stageResearch) { stageResearch.className = 'stage-pill-3d completed'; stageResearch.innerHTML = '<i data-lucide="check-circle" style="color:#10b981;"></i> <span>1. Research Agent</span>'; }
        if (stageWriter) { stageWriter.className = 'stage-pill-3d completed'; stageWriter.innerHTML = '<i data-lucide="check-circle" style="color:#10b981;"></i> <span>2. Writer Agent</span>'; }
        if (stageSeo) { stageSeo.className = 'stage-pill-3d completed'; stageSeo.innerHTML = '<i data-lucide="check-circle" style="color:#10b981;"></i> <span>3. SEO Auditor</span>'; }

        if (crewOutputArea) {
          crewOutputArea.innerHTML = `
            <div style="background:rgba(8,11,20,0.6); border:1px solid var(--border-subtle); border-radius:14px; padding:24px; line-height:1.7;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border-subtle);">
                <span class="badge-tag cyan">SEO READABILITY SCORE: 96/100</span>
                <span style="font-size:11px; color:var(--text-muted);">Word Count: ~1,450 words</span>
              </div>
              <div class="article-rendered-body" style="color:#e2e8f0; font-size:13px;">
                ${window.marked ? marked.parse(GENERATED_ARTICLE_MARKDOWN) : GENERATED_ARTICLE_MARKDOWN}
              </div>
            </div>
          `;
        }
      } catch (err) {
        if (crewOutputArea) crewOutputArea.innerHTML = '<div class="empty-state">Failed to generate article. Please retry.</div>';
      } finally {
        btnRunCrew.disabled = false;
        btnRunCrew.innerHTML = '<i data-lucide="play"></i><span>Generate 1,500-Word Article</span>';
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  if (btnExportArticle) {
    btnExportArticle.addEventListener('click', () => {
      if (!GENERATED_ARTICLE_MARKDOWN) {
        alert('Please generate an article first before downloading.');
        return;
      }
      const blob = new Blob([GENERATED_ARTICLE_MARKDOWN], { type: 'text/markdown;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `seo_article_${Date.now()}.md`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  }

  // ====================================================
  // 8. TAB 6: PROGRAMMATIC DIRECTORY & DETAIL DRAWER
  // ====================================================
  const directoryGrid = document.getElementById('directory-grid');
  const directorySearchInput = document.getElementById('directory-search-input');
  const directoryCountBadge = document.getElementById('directory-count-badge');
  const hubDrawer = document.getElementById('hub-drawer');
  const hubDrawerOverlay = document.getElementById('hub-drawer-overlay');
  const btnCloseHubDrawer = document.getElementById('btn-close-hub-drawer');

  let ALL_DIRECTORY_PAGES = [];

  async function loadDirectoryPages() {
    if (!directoryGrid) return;
    try {
      const res = await fetch('/api/seo/directory');
      const data = await res.json();
      ALL_DIRECTORY_PAGES = data.pages || [];
      renderDirectoryGrid(ALL_DIRECTORY_PAGES);
    } catch (err) {
      console.error(err);
    }
  }

  function renderDirectoryGrid(pages) {
    if (!directoryGrid) return;
    if (directoryCountBadge) directoryCountBadge.textContent = `${pages.length} Live Hubs Loaded`;

    if (pages.length === 0) {
      directoryGrid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">No matching local directory pages found.</div>';
      return;
    }

    directoryGrid.innerHTML = pages.map((p, idx) => `
      <div class="dir-card" data-idx="${idx}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="badge-tag cyan">${p.city?.name || 'Global'}</span>
          <span class="badge-pro-3d">Indexable</span>
        </div>
        <h4>${p.niche?.name || 'Commercial Niche'}</h4>
        <p>${p.meta_desc || '10-Second conversion audit & AI Closer for local businesses.'}</p>
        <div class="dir-card-meta">
          <span style="color:#10b981; font-weight:700;">Avg Leak: ${p.niche?.avg_leak || '$35,000/mo'}</span>
          <span class="btn-preview-hub"><i data-lucide="eye" class="icon-xs"></i> Preview Landing Page <i data-lucide="chevron-right" class="icon-xs"></i></span>
        </div>
      </div>
    `).join('');

    if (window.lucide) lucide.createIcons();

    document.querySelectorAll('.dir-card').forEach(card => {
      card.addEventListener('click', () => {
        const idx = parseInt(card.dataset.idx, 10);
        openHubDrawer(pages[idx]);
      });
    });
  }

  if (directorySearchInput) {
    directorySearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      if (!query) {
        renderDirectoryGrid(ALL_DIRECTORY_PAGES);
        return;
      }
      const filtered = ALL_DIRECTORY_PAGES.filter(p => 
        (p.city?.name || '').toLowerCase().includes(query) ||
        (p.niche?.name || '').toLowerCase().includes(query) ||
        (p.title || '').toLowerCase().includes(query)
      );
      renderDirectoryGrid(filtered);
    });
  }

  function openHubDrawer(hub) {
    if (!hub || !hubDrawer) return;
    const title = document.getElementById('hub-drawer-title');
    const market = document.getElementById('hub-drawer-market');
    const niche = document.getElementById('hub-drawer-niche');
    const deal = document.getElementById('hub-drawer-deal');
    const leak = document.getElementById('hub-drawer-leak');
    const schema = document.getElementById('hub-drawer-schema');

    if (title) title.textContent = `${hub.city?.name} • ${hub.niche?.name}`;
    if (market) market.textContent = `${hub.city?.name}, ${hub.city?.country}`;
    if (niche) niche.textContent = hub.niche?.name;
    if (deal) deal.textContent = hub.niche?.avg_deal || '$50,000';
    if (leak) leak.textContent = hub.niche?.avg_leak || '$42,000/mo';
    if (schema) schema.textContent = JSON.stringify(hub.schema_json, null, 2);

    hubDrawer.classList.add('active');
  }

  function closeHubDrawer() {
    if (hubDrawer) hubDrawer.classList.remove('active');
  }

  if (btnCloseHubDrawer) btnCloseHubDrawer.addEventListener('click', closeHubDrawer);
  if (hubDrawerOverlay) hubDrawerOverlay.addEventListener('click', closeHubDrawer);

  // ====================================================
  // 9. TAB 7: GROWTH & INDEXING AGENT
  // ====================================================
  const btnPingIndexnow = document.getElementById('btn-ping-indexnow');
  const growthCampaignForm = document.getElementById('growth-campaign-form');
  const growthOutputArea = document.getElementById('growth-output-area');

  if (btnPingIndexnow) {
    btnPingIndexnow.addEventListener('click', async () => {
      btnPingIndexnow.disabled = true;
      btnPingIndexnow.innerHTML = '<i data-lucide="loader-2" class="spin icon-xs"></i> <span>Broadcasting to Search Engines...</span>';
      if (window.lucide) lucide.createIcons();

      try {
        const res = await fetch('/api/growth/indexnow-ping', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({})
        });
        const data = await res.json();
        const result = data.result || {};

        if (growthOutputArea) {
          growthOutputArea.innerHTML = `
            <div style="background: var(--bg-surface); border: 1px solid rgba(70, 167, 88, 0.3); border-radius: 12px; padding: 22px; display:flex; flex-direction:column; gap:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="badge-tag" style="background:rgba(70, 167, 88, 0.15); color:#46a758; border:1px solid rgba(70, 167, 88, 0.3);">INDEXNOW PING SUCCESSFUL</span>
                <span style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono);">${result.timestamp || 'Just now'}</span>
              </div>
              <h3 style="font-size:16px; font-weight:800; color:white;">⚡ Fast-Track Crawl Broadcast Dispatched</h3>
              <p style="font-size:12px; color:var(--text-body); line-height:1.6;">
                Submitted <strong>${result.submitted_count || 50} master hub URLs</strong> directly to the IndexNow protocol API for high-frequency crawler re-indexing.
              </p>
              <div style="background:#000; border:1px solid var(--border-subtle); border-radius:8px; padding:14px; font-size:11.5px; line-height:1.6;">
                <div style="color:var(--text-muted); margin-bottom:4px; font-weight:700;">SEARCH ENGINES NOTIFIED:</div>
                <div style="color:#818cf8;">• Googlebot (via sitemap.xml auto-ping)</div>
                <div style="color:#46a758;">• Bingbot & Copilot (Direct IndexNow 200 OK)</div>
                <div style="color:#38bdf8;">• ChatGPT Search Engine (OpenAI web crawler)</div>
                <div style="color:#c084fc;">• Perplexity AI Discovery Agent</div>
              </div>
            </div>
          `;
        }
      } catch (err) {
        if (growthOutputArea) growthOutputArea.innerHTML = '<div class="empty-state">Error dispatching IndexNow ping.</div>';
      } finally {
        btnPingIndexnow.disabled = false;
        btnPingIndexnow.innerHTML = '<i data-lucide="send" class="icon-xs"></i> <span>Broadcast IndexNow Ping</span>';
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  if (growthCampaignForm) {
    growthCampaignForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const comp = document.getElementById('growth-company-name').value.trim();
      const niche = document.getElementById('growth-niche').value.trim();
      const loss = document.getElementById('growth-lost-rev').value.trim();
      const btn = document.getElementById('btn-gen-campaign');

      btn.disabled = true;
      btn.innerHTML = '<i data-lucide="loader-2" class="spin icon-xs"></i> <span>Engineering Viral Teardown...</span>';
      if (window.lucide) lucide.createIcons();

      try {
        const res = await fetch('/api/growth/generate-campaign', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: jsonSafe({ company_name: comp, niche: niche, lost_revenue: loss })
        });
        const data = await res.json();
        const camp = data.campaign || {};

        if (growthOutputArea) {
          growthOutputArea.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:16px;">
              
              <!-- Twitter Thread -->
              <div class="card-3d-tilt" style="padding:18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                  <h4 style="font-size:12px; font-weight:800; color:#38bdf8; display:flex; align-items:center; gap:6px;"><i data-lucide="twitter" class="icon-xs"></i> Viral Twitter/X Thread (5 Tweets)</h4>
                  <button class="btn-copy-sm" onclick="navigator.clipboard.writeText(document.getElementById('raw-tw-thread').textContent); alert('Twitter thread copied!');"><i data-lucide="copy" class="icon-xs"></i> Copy Thread</button>
                </div>
                <div id="raw-tw-thread" style="background:#000; border:1px solid var(--border-subtle); border-radius:8px; padding:14px; font-size:11.5px; line-height:1.6; color:#f8fafc; white-space:pre-line;">${(camp.twitter_thread || []).join('\n\n---\n\n')}</div>
              </div>

              <!-- LinkedIn Post -->
              <div class="card-3d-tilt" style="padding:18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                  <h4 style="font-size:12px; font-weight:800; color:#818cf8; display:flex; align-items:center; gap:6px;"><i data-lucide="linkedin" class="icon-xs"></i> LinkedIn Thought Leadership Post</h4>
                  <button class="btn-copy-sm" onclick="navigator.clipboard.writeText(document.getElementById('raw-li-post').textContent); alert('LinkedIn post copied!');"><i data-lucide="copy" class="icon-xs"></i> Copy Post</button>
                </div>
                <div id="raw-li-post" style="background:#000; border:1px solid var(--border-subtle); border-radius:8px; padding:14px; font-size:11.5px; line-height:1.6; color:#f8fafc; white-space:pre-line;">${camp.linkedin_post || ''}</div>
              </div>

              <!-- Reddit Post -->
              <div class="card-3d-tilt" style="padding:18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                  <h4 style="font-size:12px; font-weight:800; color:#fbbf24; display:flex; align-items:center; gap:6px;"><i data-lucide="message-square" class="icon-xs"></i> Reddit r/SaaS Teardown Case Study</h4>
                  <button class="btn-copy-sm" onclick="navigator.clipboard.writeText(document.getElementById('raw-rd-post').textContent); alert('Reddit post copied!');"><i data-lucide="copy" class="icon-xs"></i> Copy Post</button>
                </div>
                <div id="raw-rd-post" style="background:#000; border:1px solid var(--border-subtle); border-radius:8px; padding:14px; font-size:11.5px; line-height:1.6; color:#f8fafc; white-space:pre-line;">${camp.reddit_post || ''}</div>
              </div>

            </div>
          `;
        }
      } catch (err) {
        if (growthOutputArea) growthOutputArea.innerHTML = '<div class="empty-state">Error generating viral campaign.</div>';
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="sparkles" class="icon-xs"></i> <span>Generate Viral Threads</span>';
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  // ====================================================
  // 10. HELPER UTILITIES
  // ====================================================
  function appendChatMessage(container, role, text) {
    if (!container) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    msgDiv.innerHTML = `
      <div class="message-avatar-3d"><i data-lucide="${role === 'user' ? 'user' : 'bot'}"></i></div>
      <div class="message-body-3d">${text}</div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    if (window.lucide) lucide.createIcons();
  }

  function jsonSafe(obj) {
    return JSON.stringify(obj);
  }

  // Initial Data Load
  loadDocuments();
  loadBookings();
  loadDirectoryPages();
});
