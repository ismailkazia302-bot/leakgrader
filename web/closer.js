/**
 * LeakGrader.com - 24/7 Autonomous AI Sales Closer & WhatsApp Booking Widget
 * Embed snippet: <script src="https://leakgrader.com/closer.js" async></script>
 */
(function() {
  if (window.__leakgrader_closer_initialized) return;
  window.__leakgrader_closer_initialized = true;

  const API_ENDPOINT = 'https://leakgrader.com/api/booking/chat';

  // Inject CSS Styles
  const style = document.createElement('style');
  style.innerHTML = 
    .lg-closer-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      background: linear-gradient(135deg, #0284c7, #0055ff);
      color: #ffffff;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 999px;
      padding: 12px 20px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 13.5px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 10px 30px rgba(0, 85, 255, 0.4), 0 4px 10px rgba(0,0,0,0.5);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .lg-closer-btn:hover {
      transform: translateY(-2px) scale(1.03);
      box-shadow: 0 14px 36px rgba(0, 85, 255, 0.55);
    }
    .lg-closer-pulse {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #34d399;
      box-shadow: 0 0 8px #34d399;
      animation: lg-pulse-anim 2s infinite;
    }
    @keyframes lg-pulse-anim {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 14px #34d399; }
      100% { transform: scale(0.95); opacity: 0.8; }
    }
    .lg-modal {
      position: fixed;
      bottom: 84px;
      right: 24px;
      width: 360px;
      max-width: calc(100vw - 32px);
      height: 520px;
      max-height: calc(100vh - 120px);
      background: #090d18;
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 16px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(0, 85, 255, 0.2);
      z-index: 999999;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .lg-modal-header {
      padding: 14px 18px;
      background: rgba(12, 16, 28, 0.95);
      border-bottom: 1px solid rgba(255,255,255,0.08);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .lg-modal-body {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .lg-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 12.5px;
      line-height: 1.5;
    }
    .lg-msg-assistant {
      align-self: flex-start;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.1);
      color: #f1f5f9;
    }
    .lg-msg-user {
      align-self: flex-end;
      background: #0284c7;
      color: #ffffff;
    }
    .lg-modal-footer {
      padding: 12px 14px;
      background: rgba(12, 16, 28, 0.95);
      border-top: 1px solid rgba(255,255,255,0.08);
      display: flex;
      gap: 8px;
    }
    .lg-input {
      flex: 1;
      background: #000000;
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 8px;
      padding: 8px 12px;
      color: #ffffff;
      font-size: 12.5px;
      outline: none;
    }
    .lg-send-btn {
      background: #0055ff;
      border: none;
      color: #ffffff;
      padding: 8px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 700;
      font-size: 12px;
    }
  `;
  document.head.appendChild(style);

  // Create Button
  const btn = document.createElement('div');
  btn.className = 'lg-closer-btn leakgrader-closer-launcher';
  btn.innerHTML = `
    <span class="lg-closer-pulse"></span>
    <span>24/7 AI Closer</span>
  `;
  document.body.appendChild(btn);

  // Create Modal
  const modal = document.createElement('div');
  modal.className = 'lg-modal';
  modal.innerHTML = `
    <div class="lg-modal-header">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:16px;">⚡</span>
        <div>
          <strong style="color:#ffffff; font-size:13px; display:block;">LeakGrader Closer Bot</strong>
          <span style="color:#34d399; font-size:10.5px;">● Online & Instant Reply</span>
        </div>
      </div>
      <button type="button" id="lg-close-btn" style="background:transparent; border:none; color:#94a3b8; font-size:18px; cursor:pointer;">&times;</button>
    </div>
    <div class="lg-modal-body" id="lg-chat-body">
      <div class="lg-msg lg-msg-assistant">
        Hello! I am your <strong>24/7 AI Sales Closer</strong>. Ask me anything about our services or request a consultation call.
      </div>
    </div>
    <form class="lg-modal-footer" id="lg-chat-form">
      <input type="text" class="lg-input" id="lg-chat-input" placeholder="Type a message..." autocomplete="off" required>
      <button type="submit" class="lg-send-btn">Send</button>
    </form>
  ;
  document.body.appendChild(modal);

  let isOpen = false;
  btn.addEventListener('click', () => {
    isOpen = !isOpen;
    modal.style.display = isOpen ? 'flex' : 'none';
  });

  document.getElementById('lg-close-btn').addEventListener('click', () => {
    isOpen = false;
    modal.style.display = 'none';
  });

  const chatForm = document.getElementById('lg-chat-form');
  const chatInput = document.getElementById('lg-chat-input');
  const chatBody = document.getElementById('lg-chat-body');
  const chatHistory = [];

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Append user message
    const uMsg = document.createElement('div');
    uMsg.className = 'lg-msg lg-msg-user';
    uMsg.textContent = msg;
    chatBody.appendChild(uMsg);
    chatInput.value = '';
    chatBody.scrollTop = chatBody.scrollHeight;

    chatHistory.push({ role: 'user', content: msg });

    try {
      const res = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: chatHistory })
      });
      const data = await res.json();
      const aMsg = document.createElement('div');
      aMsg.className = 'lg-msg lg-msg-assistant';
      aMsg.innerHTML = (data.reply || 'Thanks for reaching out! We will contact you shortly.').replace(/\n/g, '<br>');
      chatBody.appendChild(aMsg);
      chatHistory.push({ role: 'assistant', content: data.reply || '' });
    } catch (err) {
      const eMsg = document.createElement('div');
      eMsg.className = 'lg-msg lg-msg-assistant';
      eMsg.textContent = 'Thank you! Your message has been received. Our team will follow up in 30 seconds.';
      chatBody.appendChild(eMsg);
    }
    chatBody.scrollTop = chatBody.scrollHeight;
  });
})();
