"use strict";
// The fragment swaps the composition, while the surrounding navigation persists.
document.addEventListener("htmx:afterSwap", () => {
  const active = document.querySelector("#policy-content")?.dataset.policyType;
  document.querySelectorAll(".policy-tabs a").forEach((link) => {
    const selected = new URL(link.href).searchParams.get("type") === active;
    link.classList.toggle("selected", selected);
    if (selected) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
});
