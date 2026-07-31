/* Tom Select controls for assigning tags to companies and filtering the list. */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("select[data-tag-input]").forEach(function (select) {
    new TomSelect(select, {
      plugins: {
        remove_button: { title: "Ta bort" },
      },
      create: true,
      createOnBlur: true,
      persist: false,
      render: {
        option_create: function (data, escape) {
          return (
            '<div class="create">Skapa <strong>' +
            escape(data.input) +
            "</strong></div>"
          );
        },
      },
    });
  });

  document.querySelectorAll("select[data-tag-filter]").forEach(function (select) {
    new TomSelect(select, {
      plugins: {
        remove_button: { title: "Ta bort" },
      },
      create: false,
      placeholder: select.dataset.placeholder,
    });
  });
});
