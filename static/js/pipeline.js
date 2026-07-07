/* Drag & drop for the pipeline board (specs/012-pipeline-drag-drop.md).
 *
 * Dropping a card on another column POSTs the stage change and patches
 * the column-header summaries from the response. Order within a column
 * is not persisted, so error recovery is just "append the card back to
 * the column it came from".
 */
document.addEventListener("DOMContentLoaded", function () {
  // Every page has a CSRF token in the logout form.
  var csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  function flashError() {
    var alert = document.createElement("div");
    alert.className = "alert alert-danger";
    alert.setAttribute("role", "alert");
    alert.textContent = "Kunde inte flytta affären. Ladda om sidan och försök igen.";
    document.querySelector("main").prepend(alert);
  }

  function updateSummaries(summaries) {
    Object.keys(summaries).forEach(function (stage) {
      var el = document.querySelector('[data-stage-summary="' + stage + '"]');
      if (el) el.textContent = summaries[stage];
    });
  }

  document.querySelectorAll("[data-stage]").forEach(function (column) {
    new Sortable(column, {
      group: "pipeline",
      animation: 150,
      onAdd: function (evt) {
        fetch(evt.item.dataset.stageUrl, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({ stage: evt.to.dataset.stage }),
        })
          .then(function (response) {
            if (!response.ok) throw new Error("HTTP " + response.status);
            return response.json();
          })
          .then(function (data) {
            updateSummaries(data.summaries);
          })
          .catch(function () {
            evt.from.appendChild(evt.item);
            flashError();
          });
      },
    });
  });
});
