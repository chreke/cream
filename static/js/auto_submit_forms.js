/* Submit GET filter forms when one of their select controls changes.
 * Text inputs keep their native behavior: pressing Enter submits the form.
 */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form[data-auto-submit]").forEach(function (form) {
    form.addEventListener("change", function (event) {
      if (event.target instanceof HTMLSelectElement) {
        form.requestSubmit();
      }
    });
  });
});
