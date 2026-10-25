/* Submit GET filter forms when one of their select or checkbox controls
 * changes. Text inputs keep their native behavior: pressing Enter submits
 * the form.
 */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form[data-auto-submit]").forEach(function (form) {
    form.addEventListener("change", function (event) {
      var target = event.target;
      if (
        target instanceof HTMLSelectElement ||
        (target instanceof HTMLInputElement && target.type === "checkbox")
      ) {
        form.requestSubmit();
      }
    });
  });
});
