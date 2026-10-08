(function () {
  const TYPING_SPEED_MS = 45;
  const START_DELAY_MS = 500;
  const OUTPUT_DELAY_MS = 300;

  function outputsFor(line) {
    const outputs = [];
    let el = line.nextElementSibling;
    while (el && !el.classList.contains("terminal-line")) {
      if (el.classList.contains("terminal-output")) outputs.push(el);
      el = el.nextElementSibling;
    }
    return outputs;
  }

  function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function run(demo) {
    const lines = Array.from(demo.querySelectorAll(".terminal-line"));
    const steps = lines.map((line) => {
      const command = line.querySelector(".terminal-command");
      const outputs = outputsFor(line);
      const text = command ? command.textContent : "";
      if (command) {
        command.textContent = "";
        command.classList.add("typing");
      }
      outputs.forEach((o) => o.classList.add("pending"));
      return { command, text, outputs };
    });

    await wait(START_DELAY_MS);
    for (const { command, text, outputs } of steps) {
      if (command) {
        for (const ch of text) {
          command.textContent += ch;
          await wait(TYPING_SPEED_MS);
        }
        command.classList.remove("typing");
        await wait(OUTPUT_DELAY_MS);
      }
      outputs.forEach((o) => o.classList.remove("pending"));
    }
  }

  function init() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    document.querySelectorAll(".terminal-demo").forEach(run);
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", init);
  else init();
})();

(function () {
  function isExternal(link) {
    return (
      /^https?:$/.test(link.protocol) && link.host !== window.location.host
    );
  }

  function openExternalLinksInNewTab() {
    document.querySelectorAll("a[href]").forEach((link) => {
      if (!isExternal(link)) return;
      link.target = "_blank";
      link.relList.add("noopener");
    });
  }

  if (window.document$) window.document$.subscribe(openExternalLinksInNewTab);
  else if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", openExternalLinksInNewTab);
  else openExternalLinksInNewTab();
})();
