const upload = document.querySelector("form[data-bulk-upload]");
function resetUpload() {
  delete upload.dataset.busy;
  upload.removeAttribute("aria-busy");
  upload.querySelector("[data-working]").hidden = true;
}
window.addEventListener("pageshow", resetUpload);
upload.addEventListener("submit", event => {
  if (upload.dataset.busy) { event.preventDefault(); return; }
  upload.dataset.busy = "1";
  upload.setAttribute("aria-busy", "true");
  const status = upload.querySelector("[data-working]");
  status.querySelector("[data-message]").textContent =
    event.submitter?.value === "import" ? status.dataset.import : status.dataset.check;
  status.hidden = false;
});
