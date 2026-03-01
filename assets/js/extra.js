document.addEventListener("DOMContentLoaded", function () {
  animateTerminal();
  animateOnScroll(".feature-card", "animate-fade-in");
  setupTabbedInterface();
  setupLightbox();
  setupCopyFeedback();
  highlightActiveNav();
  setupThemeToggleShortcut();
});

function setupThemeToggleShortcut() {
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey && e.key === "\\") {
      e.preventDefault();

      const inputs = document.querySelectorAll("input[name='__palette']");
      for (const input of inputs) {
        if (!input.checked) {
          const label = document.querySelector("label[for='" + input.id + "']");
          if (label) {
            label.click();
            break;
          }
        }
      }
    }
  });
}

function animateTerminal() {
  const terminalDemo = document.querySelector(".terminal-demo");
  if (!terminalDemo) return;

  const commands = terminalDemo.querySelectorAll(".terminal-command");
  let delay = 600;

  commands.forEach((command) => {
    const text = command.textContent;
    command.textContent = "";
    command.style.setProperty("--typing-done", "0");

    const outputEl = command.closest(".terminal-line")?.nextElementSibling;

    if (outputEl?.classList.contains("terminal-output")) {
      outputEl.style.opacity = "0";
      outputEl.style.transition = "opacity 0.4s ease";
    }

    simulateTyping(command, text, 42, delay, () => {
      command.classList.add("typing-done");
      if (outputEl?.classList.contains("terminal-output")) {
        setTimeout(() => {
          outputEl.style.opacity = "1";
        }, 200);
      }
    });

    delay += text.length * 42 + 900;
  });
}

function simulateTyping(element, text, speed, startDelay, callback) {
  setTimeout(() => {
    let i = 0;
    const interval = setInterval(() => {
      element.textContent += text.charAt(i);
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        if (callback) callback();
      }
    }, speed);
  }, startDelay);
}

function animateOnScroll(selector, animClass) {
  const els = document.querySelectorAll(selector);
  if (!els.length) return;

  els.forEach((el, i) => {
    el.classList.add("animate-prepare");
    el.style.animationDelay = `${i * 60}ms`;
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add(animClass);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -40px 0px" },
  );

  els.forEach((el) => observer.observe(el));
}

function setupTabbedInterface() {
  document.querySelectorAll(".tabbed-set").forEach((set) => {
    const tabs = set.querySelectorAll('input[type="radio"]');
    const labels = set.querySelectorAll("label");
    const contents = set.querySelectorAll(".tabbed-content");

    labels.forEach((label, i) => {
      label.addEventListener("click", () => {
        tabs[i].checked = true;
        labels.forEach((l) => l.classList.remove("tabbed-label--active"));
        label.classList.add("tabbed-label--active");
        contents.forEach((c) => c.classList.remove("tabbed-content--active"));
        contents[i].classList.add("tabbed-content--active");
      });
    });

    const checkedIdx = Array.from(tabs).findIndex((t) => t.checked);
    if (checkedIdx >= 0) {
      labels[checkedIdx].classList.add("tabbed-label--active");
      contents[checkedIdx].classList.add("tabbed-content--active");
    }
  });
}

function setupLightbox() {
  const galleryItems = document.querySelectorAll(".gallery-item");
  if (!galleryItems.length) return;

  const lightbox = document.createElement("div");
  lightbox.className = "lightbox";
  lightbox.innerHTML = `
    <div class="lightbox-overlay"></div>
    <div class="lightbox-content">
      <img src="" alt="" class="lightbox-image">
      <button class="lightbox-close" aria-label="Close">✕</button>
    </div>`;
  document.body.appendChild(lightbox);

  const overlay = lightbox.querySelector(".lightbox-overlay");
  const img = lightbox.querySelector(".lightbox-image");
  const closeBtn = lightbox.querySelector(".lightbox-close");

  galleryItems.forEach((item) => {
    const image = item.querySelector("img");
    if (!image) return;
    item.style.cursor = "zoom-in";
    item.addEventListener("click", () => {
      img.src = image.src;
      img.alt = image.alt;
      lightbox.classList.add("lightbox--active");
      document.body.style.overflow = "hidden";
    });
  });

  const close = () => {
    lightbox.classList.remove("lightbox--active");
    document.body.style.overflow = "";
  };

  closeBtn.addEventListener("click", close);
  overlay.addEventListener("click", close);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

function setupCopyFeedback() {
  document.querySelectorAll(".md-clipboard").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.classList.add("copied");
      setTimeout(() => btn.classList.remove("copied"), 1800);
    });
  });
}

function highlightActiveNav() {
  const headings = document.querySelectorAll(".md-content h2, .md-content h3");
  if (!headings.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.id;
        document
          .querySelectorAll('.md-nav__link[href*="#"]')
          .forEach((link) => {
            const active = link.getAttribute("href")?.endsWith("#" + id);
            link.classList.toggle("md-nav__link--active-scroll", active);
          });
      });
    },
    { rootMargin: "-20% 0px -70% 0px" },
  );

  headings.forEach((h) => observer.observe(h));
}

const styles = document.createElement("style");
styles.textContent = `
  .animate-prepare {
    opacity: 0;
    transform: translateY(18px);
    transition: none;
  }

  .animate-fade-in {
    animation: cardRise 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  @keyframes cardRise {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .tabbed-label--active {
    border-bottom-color: var(--md-accent-fg-color) !important;
    color: var(--md-accent-fg-color) !important;
  }

  .tabbed-content {
    display: none;
  }

  .tabbed-content--active {
    display: block;
    animation: fadeUp 0.3s ease both;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .terminal-command.typing-done::after {
    display: none;
  }

  .md-clipboard.copied {
    color: #22c55e !important;
    transition: color 0.2s ease !important;
  }

  .lightbox {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.25s ease;
  }

  .lightbox--active {
    opacity: 1;
    pointer-events: auto;
  }

  .lightbox-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.85);
    backdrop-filter: blur(4px);
  }

  .lightbox-content {
    position: relative;
    z-index: 1;
    max-width: 92vw;
    max-height: 92vh;
    transform: scale(0.96);
    transition: transform 0.25s cubic-bezier(0.16,1,0.3,1);
  }

  .lightbox--active .lightbox-content {
    transform: scale(1);
  }

  .lightbox-image {
    max-width: 100%;
    max-height: 88vh;
    display: block;
    border-radius: 8px;
    box-shadow: 0 32px 80px rgba(0,0,0,0.6);
  }

  .lightbox-close {
    position: absolute;
    top: -44px; right: 0;
    width: 36px; height: 36px;
    border-radius: 50%;
    background: rgba(255,255,255,0.12);
    color: #fff;
    font-size: 18px;
    border: 1px solid rgba(255,255,255,0.2);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s ease;
    backdrop-filter: blur(4px);
  }

  .lightbox-close:hover {
    background: rgba(255,255,255,0.22);
  }

  .md-nav__link--active-scroll {
    color: #22c55e !important;
  }
`;

document.head.appendChild(styles);
