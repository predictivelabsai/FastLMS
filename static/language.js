(() => {
  "use strict";

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-speak]");
    if (!button || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(button.dataset.speak || "");
    utterance.lang = button.dataset.voice || "en-US";
    utterance.rate = 0.82;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  });
})();
