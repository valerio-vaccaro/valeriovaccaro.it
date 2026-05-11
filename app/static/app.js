(function () {
  const root = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('theme') || 'light';

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    if (toggle) toggle.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
  }

  applyTheme(savedTheme);

  if (toggle) {
    toggle.addEventListener('click', function () {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      applyTheme(next);
    });
  }

  const inputs = document.querySelectorAll('[data-markdown-input]');
  inputs.forEach(function (input) {
    const targetId = input.getAttribute('data-markdown-input');
    const target = document.getElementById(targetId);
    if (!target) return;

    function render() {
      const text = input.value || '';
      if (window.marked && typeof window.marked.parse === 'function') {
        target.innerHTML = window.marked.parse(text);
      } else {
        target.textContent = text;
      }
    }

    input.addEventListener('input', render);
    render();
  });

  initTagEditors();
  initArticleAssetInsertion();
  initMarkdownCopyButtons();
  initSiteBackgroundCanvas();

  function initTagEditors() {
    const tagInputs = document.querySelectorAll('[data-tag-editor="true"]');
    tagInputs.forEach(function (hiddenInput) {
      const wrapper = document.createElement('div');
      wrapper.className = 'tag-editor';
      const chips = document.createElement('div');
      chips.className = 'tag-editor-chips';
      const entry = document.createElement('input');
      entry.type = 'text';
      entry.className = 'tag-editor-input';
      entry.placeholder = 'Add tag';

      wrapper.appendChild(chips);
      wrapper.appendChild(entry);
      hiddenInput.insertAdjacentElement('afterend', wrapper);
      hiddenInput.classList.add('d-none');

      const tags = new Set();

      function parseExisting(value) {
        return (value || '')
          .split(',')
          .map(function (item) { return item.trim().toLowerCase(); })
          .filter(Boolean);
      }

      function syncHidden() {
        hiddenInput.value = Array.from(tags).join(', ');
      }

      function removeTag(tag) {
        tags.delete(tag);
        renderChips();
      }

      function renderChips() {
        chips.innerHTML = '';
        Array.from(tags).forEach(function (tag) {
          const chip = document.createElement('button');
          chip.type = 'button';
          chip.className = 'tag-chip';
          chip.innerHTML = '<span>#' + tag + '</span><span aria-hidden="true">×</span>';
          chip.addEventListener('click', function () { removeTag(tag); });
          chips.appendChild(chip);
        });
        syncHidden();
      }

      function addTag(raw) {
        const tag = (raw || '').trim().toLowerCase();
        if (!tag) return;
        tags.add(tag);
        renderChips();
      }

      parseExisting(hiddenInput.value).forEach(function (tag) { tags.add(tag); });
      renderChips();

      entry.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ',') {
          event.preventDefault();
          addTag(entry.value);
          entry.value = '';
          return;
        }
        if (event.key === 'Backspace' && !entry.value) {
          const current = Array.from(tags);
          if (current.length > 0) {
            tags.delete(current[current.length - 1]);
            renderChips();
          }
        }
      });

      entry.addEventListener('blur', function () {
        addTag(entry.value);
        entry.value = '';
      });
    });
  }

  function initSiteBackgroundCanvas() {
    const canvas = document.getElementById('siteBackgroundCanvas');
    if (!canvas) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile = window.matchMedia('(max-width: 768px)').matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let rafId = null;
    const particles = [];
    const count = reduceMotion ? 0 : (mobile ? 18 : 34);

    function resize() {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, Math.floor(rect.width));
      height = Math.max(1, Math.floor(rect.height));
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function seed() {
      particles.length = 0;
      for (let i = 0; i < count; i += 1) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          r: 1 + Math.random() * (mobile ? 2.2 : 3.4),
          vx: (Math.random() - 0.5) * (mobile ? 0.25 : 0.4),
          vy: (Math.random() - 0.5) * (mobile ? 0.25 : 0.4)
        });
      }
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);
      const isDark = root.getAttribute('data-theme') === 'dark';
      const dot = isDark ? 'rgba(148, 163, 184, 0.45)' : 'rgba(11, 114, 133, 0.30)';
      const line = isDark ? 'rgba(148, 163, 184, 0.18)' : 'rgba(11, 114, 133, 0.14)';

      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < -20) p.x = width + 20;
        if (p.x > width + 20) p.x = -20;
        if (p.y < -20) p.y = height + 20;
        if (p.y > height + 20) p.y = -20;

        ctx.beginPath();
        ctx.fillStyle = dot;
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j += 1) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const limit = mobile ? 90 : 120;
          if (dist < limit) {
            ctx.beginPath();
            ctx.strokeStyle = line;
            ctx.lineWidth = 1;
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
      }

      rafId = window.requestAnimationFrame(draw);
    }

    resize();
    seed();
    if (!reduceMotion) draw();

    window.addEventListener('resize', function () {
      resize();
      seed();
    }, { passive: true });

    window.addEventListener('pagehide', function () {
      if (rafId) window.cancelAnimationFrame(rafId);
    });
  }

  function initArticleAssetInsertion() {
    const markdownInput = document.querySelector('[data-markdown-input="article-preview"]');
    if (!markdownInput) return;

    const insertButtons = document.querySelectorAll('[data-insert-markdown]');
    insertButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        const snippet = button.getAttribute('data-insert-markdown') || '';
        const start = markdownInput.selectionStart || 0;
        const end = markdownInput.selectionEnd || 0;
        const value = markdownInput.value || '';
        const prefix = value.slice(0, start);
        const suffix = value.slice(end);
        const addNewlineBefore = prefix && !prefix.endsWith('\n') ? '\n' : '';
        const addNewlineAfter = suffix && !suffix.startsWith('\n') ? '\n' : '';
        const inserted = addNewlineBefore + snippet + addNewlineAfter;
        markdownInput.value = prefix + inserted + suffix;
        const cursor = (prefix + inserted).length;
        markdownInput.focus();
        markdownInput.setSelectionRange(cursor, cursor);
        markdownInput.dispatchEvent(new Event('input', { bubbles: true }));
      });
    });
  }

  function initMarkdownCopyButtons() {
    const buttons = document.querySelectorAll('[data-copy-markdown-target]');
    buttons.forEach(function (button) {
      button.addEventListener('click', async function () {
        const targetId = button.getAttribute('data-copy-markdown-target');
        if (!targetId) return;
        const input = document.getElementById(targetId);
        if (!input) return;

        const text = input.value || '';
        const originalLabel = button.textContent;
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
          } else {
            input.focus();
            input.select();
            document.execCommand('copy');
          }
          button.textContent = 'Copied!';
        } catch (error) {
          button.textContent = 'Copy failed';
        }
        window.setTimeout(function () {
          button.textContent = originalLabel;
        }, 1200);
      });
    });
  }
})();
