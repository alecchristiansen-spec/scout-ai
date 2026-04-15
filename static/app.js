const STRIPE_LINK = "https://buy.stripe.com/cNi7sMdnR71rdIR0Y3dby00";

const form = document.getElementById('chat-form');
const messageInput = document.getElementById('message');
const modeInput = document.getElementById('mode');
const imageInput = document.getElementById('image');
const researchInput = document.getElementById('research');
const responseBox = document.getElementById('response-box');
const errorBox = document.getElementById('error-box');
const emptyState = document.getElementById('empty-state');
const statusPill = document.getElementById('status-pill');
const resetBtn = document.getElementById('reset-btn');
const promptButtons = document.querySelectorAll('.prompt-chip');
const usageText = document.getElementById('usage-text');
const upgradeCta = document.getElementById('upgrade-cta');

const heroUpgradeBtn = document.getElementById('hero-upgrade-btn');
const heroDemoBtn = document.getElementById('hero-demo-btn');
const upgradeBtn = document.getElementById('upgrade-btn');
const pricingModal = document.getElementById('pricing-modal');
const modalBackdrop = document.getElementById('modal-backdrop');
const closeModalBtn = document.getElementById('close-modal-btn');
const closeModalBtn2 = document.getElementById('close-modal-btn-2');
const fakeCheckoutBtn = document.getElementById('fake-checkout-btn');

function setStatus(text, state = 'idle') {
  statusPill.textContent = text;
  statusPill.className = `status-pill ${state}`;
}

function showResponse(text) {
  emptyState.classList.add('hidden');
  errorBox.classList.add('hidden');
  responseBox.classList.remove('hidden');
  responseBox.textContent = text;
}

function showError(text) {
  emptyState.classList.add('hidden');
  responseBox.classList.add('hidden');
  errorBox.classList.remove('hidden');
  errorBox.textContent = text;
}

function updateUsage(data) {
  if (!usageText) return;
  if (typeof data.remaining === 'number' && typeof data.limit === 'number') {
    usageText.textContent = `${data.remaining} of ${data.limit} free requests left`;
  }
}

function maybeShowUpgrade(data) {
  if (!upgradeCta) return;
  if (data && (data.limit_reached || data.remaining === 0)) {
    upgradeCta.classList.remove('hidden');
  } else {
    upgradeCta.classList.add('hidden');
  }
}

async function loadUsage() {
  try {
    const res = await fetch('/api/usage');
    const data = await res.json();
    updateUsage(data);
    maybeShowUpgrade(data);
  } catch (err) {
    console.error('Could not load usage:', err);
  }
}

function openPricingModal() {
  pricingModal?.classList.remove('hidden');
}

function closePricingModal() {
  pricingModal?.classList.add('hidden');
}

form?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData();
  formData.append('message', messageInput.value);
  formData.append('mode', modeInput.value);
  formData.append('research', researchInput.checked ? 'true' : 'false');

  if (imageInput.files[0]) {
    formData.append('image', imageInput.files[0]);
  }

  setStatus('Thinking…', 'loading');
  responseBox.classList.add('hidden');
  errorBox.classList.add('hidden');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Something went wrong.');
    }

    updateUsage(data);
    maybeShowUpgrade(data);

    if (data.limit_reached) {
      showResponse(data.output_text || 'You hit your free limit.');
      setStatus('Limit reached', 'error');
      return;
    }

    showResponse(data.output_text);
    setStatus(data.used_research ? 'Answered with research' : 'Answered', 'success');
  } catch (err) {
    showError(err.message);
    setStatus('Error', 'error');
  }
});

resetBtn?.addEventListener('click', () => {
  form.reset();
  responseBox.classList.add('hidden');
  errorBox.classList.add('hidden');
  emptyState.classList.remove('hidden');
  setStatus('Ready', 'idle');
});

promptButtons.forEach((button) => {
  button.addEventListener('click', () => {
    messageInput.value = button.dataset.prompt;
    messageInput.focus();
  });
});

// Top hero buttons
heroUpgradeBtn?.addEventListener('click', () => {
  window.open(STRIPE_LINK, '_blank');
});

heroDemoBtn?.addEventListener('click', openPricingModal);

// Upgrade CTA after limit
upgradeBtn?.addEventListener('click', () => {
  window.open(STRIPE_LINK, '_blank');
});

// Modal controls
modalBackdrop?.addEventListener('click', closePricingModal);
closeModalBtn?.addEventListener('click', closePricingModal);
closeModalBtn2?.addEventListener('click', closePricingModal);

// Modal checkout button
fakeCheckoutBtn?.addEventListener('click', () => {
  window.open(STRIPE_LINK, '_blank');
});

loadUsage();
