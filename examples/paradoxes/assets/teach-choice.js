(() => {
  document.querySelectorAll("[data-teach-choice]").forEach((group) => {
    const feedback = group.querySelector("[data-teach-feedback]");
    group.querySelectorAll("button[data-response]").forEach((button) => {
      button.addEventListener("click", () => {
        group.querySelectorAll("button[data-response]").forEach((peer) => peer.setAttribute("aria-pressed", "false"));
        button.setAttribute("aria-pressed", "true");
        if (feedback) {
          feedback.textContent = button.dataset.response;
          feedback.hidden = false;
        }
      });
    });
  });
})();
