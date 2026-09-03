/**
 * LeakGrader.com - Embeddable 24/7 AI Sales Closer Widget
 * Zero-dependency lightweight embed script for client websites (WordPress, Webflow, Shopify, HTML).
 */

(function() {
  const host = window.location.host;
  const scriptTag = document.currentScript;
  const companyName = (scriptTag && scriptTag.getAttribute('data-company')) || host || 'Your Business';

  const widgetContainer = document.createElement('div');
  widgetContainer.id = 'leakgrader-closer-widget';
  widgetContainer.innerHTML = `
    <style>
      #leakgrader-closer-widget {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }
      .lg-trigger-btn {
        background: linear-gradient(135deg, #0055ff, #38bdf8);
        color: #ffffff;
        border: none;
        border-radius: 999px;
        padding: 12px 20px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 10px 25px rgba(0,85,255,0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .lg-trigger-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 30px rgba(0,85,255,0.5);
      }
      .lg-chat-frame {
        display: none;
        position: absolute;
        bottom: 60px;
        right: 0;
        width: 360px;
        height: 500px;
        background: #08090C;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.8);
        overflow: hidden;
        flex-direction: column;
      }
      .lg-chat-frame.active {
        display: flex;
      }
      .lg-header {
        background: #0d1117;
        padding: 14px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.06);
      }
      .lg-header strong {
        color: #ffffff;
        font-size: 13px;
      }
      .lg-header span {
        font-size: 10px;
        color: #34d399;
      }
      .lg-body {
        flex: 1;
        padding: 16px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
        font-size: 12px;
        color: #e2e8f0;
      }
      .lg-msg {
        background: rgba(255,255,255,0.05);
        padding: 10px 12px;
        border-radius: 10px;
        max-width: 85%;
        line-height: 1.5;
      }
      .lg-footer {
        padding: 10px;
        background: #0d1117;
        display: flex;
        gap: 6px;
        border-top: 1px solid rgba(255,255,255,0.06);
      }
      .lg-footer input {
        flex: 1;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 8px 12px;
        color: #fff;
        font-size: 12px;
        outline: none;
      }
      .lg-footer button {
        background: #0055ff;
        color: #fff;
        border: none;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 700;
        cursor: pointer;
      }
    </style>
    <button class="lg-trigger-btn" id="lg-btn-toggle">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <span>Chat with ${companyName} AI</span>
    </button>
    <div class="lg-chat-frame" id="lg-chat-window">
      <div class="lg-header">
        <div>
          <strong>${companyName} 24/7 AI Closer</strong><br>
          <span>● Online (Instant Reply)</span>
        </div>
        <button id="lg-btn-close" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px;">✕</button>
      </div>
      <div class="lg-body" id="lg-chat-messages">
        <div class="lg-msg">👋 Hi! Welcome to ${companyName}. How can we assist you with our services today?</div>
      </div>
      <form class="lg-footer" id="lg-chat-form">
        <input type="text" id="lg-chat-input" placeholder="Type your inquiry or phone..." required>
        <button type="submit">Send</button>
      </form>
    </div>
  `;

  document.body.appendChild(widgetContainer);

  const btnToggle = document.getElementById('lg-btn-toggle');
  const btnClose = document.getElementById('lg-btn-close');
  const chatWindow = document.getElementById('lg-chat-window');
  const chatForm = document.getElementById('lg-chat-form');
  const chatInput = document.getElementById('lg-chat-input');
  const chatMessages = document.getElementById('lg-chat-messages');

  btnToggle.addEventListener('click', () => chatWindow.classList.toggle('active'));
  btnClose.addEventListener('click', () => chatWindow.classList.remove('active'));

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    const userMsg = document.createElement('div');
    userMsg.className = 'lg-msg';
    userMsg.style.alignSelf = 'flex-end';
    userMsg.style.background = '#0055ff';
    userMsg.style.color = '#fff';
    userMsg.textContent = text;
    chatMessages.appendChild(userMsg);
    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'lg-msg';
    loadingMsg.textContent = 'Thinking...';
    chatMessages.appendChild(loadingMsg);

    try {
      const res = await fetch('https://leakgrader.com/api/booking/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_context: `${companyName}: Enterprise AI & Customer Solutions.`,
          message: text,
          history: []
        })
      });
      const data = await res.json();
      loadingMsg.textContent = data.reply || "Thank you! Our AI team will reach out to qualify your request.";
    } catch (err) {
      loadingMsg.textContent = "Thank you! We've received your message and will contact you in under 60 seconds.";
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
})();
