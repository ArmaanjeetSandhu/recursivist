document.addEventListener("DOMContentLoaded", function () {
  animateTerminal();
  animateOnScroll(".feature-card", "animate-fade-in");
  setupTabbedInterface();
  setupLightbox();
});

function animateTerminal() {
  const terminalDemo = document.querySelector(".terminal-demo");
  if (!terminalDemo) return;

  const commands = terminalDemo.querySelectorAll(".terminal-command");
  let delay = 500;

  commands.forEach((command, index) => {
    const text = command.textContent;
    command.textContent = "";
    const outputElement = command.closest(".terminal-line").nextElementSibling;

    simulateTyping(command, text, 50, delay, () => {
      if (
        outputElement &&
        outputElement.classList.contains("terminal-output")
      ) {
        outputElement.style.display = "none";
        setTimeout(() => {
          outputElement.style.display = "block";
        }, 300);
      }
    });

    delay += text.length * 50 + 1000;
  });
}

/**
 * Simulates typing text character by character
 * @param {HTMLElement} element - The element to type into
 * @param {string} text - The text to type
 * @param {number} speed - Typing speed in milliseconds per character
 * @param {number} startDelay - Delay before starting to type
 * @param {Function} callback - Function to call when typing is complete
 */
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

function animateOnScroll(selector, animationClass) {
  const elements = document.querySelectorAll(selector);
  if (!elements.length) return;

  elements.forEach((element) => {
    element.classList.add("animate-prepare");
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add(animationClass);
          observer.unobserve(entry.target);
        }
      });
    },
    {
      root: null,
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    }
  );

  elements.forEach((element) => {
    observer.observe(element);
  });
}

function setupTabbedInterface() {
  const tabbedSets = document.querySelectorAll(".tabbed-set");
  if (!tabbedSets.length) return;

  tabbedSets.forEach((tabbedSet) => {
    const tabs = tabbedSet.querySelectorAll('input[type="radio"]');
    const labels = tabbedSet.querySelectorAll("label");
    const contents = tabbedSet.querySelectorAll(".tabbed-content");

    labels.forEach((label, index) => {
      label.addEventListener("click", () => {
        tabs[index].checked = true;

        labels.forEach((l) => l.classList.remove("tabbed-label--active"));
        label.classList.add("tabbed-label--active");

        contents.forEach((content) => {
          content.classList.remove("tabbed-content--active");
        });
        contents[index].classList.add("tabbed-content--active");
      });
    });

    const checkedIndex = Array.from(tabs).findIndex((tab) => tab.checked);
    if (checkedIndex >= 0) {
      labels[checkedIndex].classList.add("tabbed-label--active");
      contents[checkedIndex].classList.add("tabbed-content--active");
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
        <img src="" alt="Lightbox image" class="lightbox-image">
        <button class="lightbox-close">×</button>
      </div>
    `;
  document.body.appendChild(lightbox);

  const lightboxOverlay = lightbox.querySelector(".lightbox-overlay");
  const lightboxContent = lightbox.querySelector(".lightbox-content");
  const lightboxImage = lightbox.querySelector(".lightbox-image");
  const lightboxClose = lightbox.querySelector(".lightbox-close");

  galleryItems.forEach((item) => {
    const image = item.querySelector("img");
    if (!image) return;

    item.addEventListener("click", () => {
      lightboxImage.src = image.src;
      lightboxImage.alt = image.alt;

      lightbox.classList.add("lightbox--active");
      document.body.style.overflow = "hidden";
    });
  });

  lightboxClose.addEventListener("click", closeLightbox);
  lightboxOverlay.addEventListener("click", closeLightbox);

  function closeLightbox() {
    lightbox.classList.remove("lightbox--active");
    document.body.style.overflow = "";
  }
}

const animationStyles = document.createElement("style");
animationStyles.textContent = `
    /* Base animation class to hide elements before animation */
    .animate-prepare {
      opacity: 0;
      transform: translateY(20px);
    }

    /* Fade in animation */
    .animate-fade-in {
      animation: fadeIn 0.6s ease forwards;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* Tabbed interface animations */
    .tabbed-label--active {
      border-bottom-color: var(--md-primary-fg-color) !important;
      font-weight: 700 !important;
    }

    .tabbed-content {
      opacity: 0;
      height: 0;
      overflow: hidden;
      transition: opacity 0.3s ease;
    }

    .tabbed-content--active {
      opacity: 1;
      height: auto;
      overflow: visible;
    }

    /* Lightbox styles */
    .lightbox {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
    }

    .lightbox--active {
      opacity: 1;
      pointer-events: auto;
    }

    .lightbox-overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.8);
    }

    .lightbox-content {
      position: relative;
      max-width: 90%;
      max-height: 90%;
      z-index: 1;
    }

    .lightbox-image {
      max-width: 100%;
      max-height: 90vh;
      display: block;
      border-radius: 4px;
      box-shadow: 0 5px 30px rgba(0, 0, 0, 0.3);
    }

    .lightbox-close {
      position: absolute;
      top: -40px;
      right: -40px;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-color: rgba(0, 0, 0, 0.5);
      color: white;
      font-size: 24px;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.3s ease;
    }

    .lightbox-close:hover {
      background-color: rgba(0, 0, 0, 0.8);
    }
  `;

document.head.appendChild(animationStyles);
