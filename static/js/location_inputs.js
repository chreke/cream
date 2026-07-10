/* Tom Select on the location inputs (companies + candidates).
 *
 * Replaces the old <datalist> autocomplete: suggestions come from the
 * #location-options json_script blob (existing locations from both
 * models), but the field stays free text — anything typed can be created
 * as a new value. Without JS it degrades to a plain text input.
 */
document.addEventListener("DOMContentLoaded", function () {
  var blob = document.getElementById("location-options");
  if (!blob) return;
  var locations = JSON.parse(blob.textContent);

  document
    .querySelectorAll("input[data-location-input]")
    .forEach(function (input) {
      new TomSelect(input, {
        options: locations.map(function (location) {
          return { value: location, text: location };
        }),
        maxItems: 1,
        create: true,
        createOnBlur: true,
        // Created values are transient suggestions, not saved options.
        persist: false,
        render: {
          // Swedish label instead of the default "Add ...".
          option_create: function (data, escape) {
            return (
              '<div class="create">Lägg till <strong>' +
              escape(data.input) +
              "</strong></div>"
            );
          },
        },
      });
    });
});
