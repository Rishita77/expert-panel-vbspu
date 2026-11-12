(() => {
  const field = document.querySelector("[data-manual-password]");
  if (!field) return;
  const form = field.closest("form");
  const password = field.querySelector("input");
  const update = () => {
    const manual = form.querySelector('input[name="method"]:checked')?.value === "set";
    field.hidden = !manual;
    password.disabled = !manual;
    password.required = manual;
    password.autocomplete = "new-password";
    if (!manual) password.value = "";
  };
  form.querySelectorAll('input[name="method"]').forEach(choice => {
    choice.addEventListener("change", update);
  });
  window.addEventListener("pageshow", update);
  update();
})();
