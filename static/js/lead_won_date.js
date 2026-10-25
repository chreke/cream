/* Won date input in the lead edit modal (specs/019-deal-list.md).
 *
 * Only Vunnen leads may have a won date, so the input is disabled unless
 * the stage select is set to Vunnen. A disabled input isn't submitted,
 * which clears the date server-side; its value is kept in the input so
 * switching back to Vunnen restores it.
 */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-lead-stage]").forEach(function (stage) {
    var closedAt = stage.form.querySelector("[data-lead-closed-at]");
    if (!closedAt) return;

    function update() {
      closedAt.disabled = stage.value !== "won";
    }
    stage.addEventListener("change", update);
    update();
  });
});
