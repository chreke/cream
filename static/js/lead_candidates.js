/* Candidate picker on the lead page (specs/013-lead-candidate-connection.md).
 *
 * Tom Select with server-aided autocomplete: typing queries the ranked
 * candidate search (already-attached candidates excluded server-side);
 * picking an option fills the <select>, and the surrounding form POSTs
 * the attach via the "Lägg till" button.
 */
document.addEventListener("DOMContentLoaded", function () {
  var picker = document.getElementById("candidate-picker");
  if (!picker) return;

  new TomSelect(picker, {
    valueField: "id",
    labelField: "name",
    // The server already filters and ranks; disable client-side scoring
    // and keep the response order.
    searchField: [],
    sortField: [{ field: "$order" }],
    maxOptions: null,
    placeholder: "Sök kandidat...",
    loadThrottle: 300,
    load: function (query, callback) {
      var url =
        picker.dataset.searchUrl + "?q=" + encodeURIComponent(query);
      fetch(url)
        .then(function (response) {
          if (!response.ok) throw new Error("HTTP " + response.status);
          return response.json();
        })
        .then(function (data) {
          callback(data.results);
        })
        .catch(function () {
          callback();
        });
    },
    shouldLoad: function (query) {
      return query.length >= 1;
    },
    render: {
      option: function (item, escape) {
        var context = [item.location, item.skills]
          .filter(Boolean)
          .map(escape)
          .join(" · ");
        return (
          "<div>" +
          escape(item.name) +
          (context
            ? '<div class="text-secondary small">' + context + "</div>"
            : "") +
          "</div>"
        );
      },
    },
  });
});
