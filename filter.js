$(document).ready(function() {
  $('#filter').change(function() {
    var type = $('#filter option:selected').val();
    if (type === '[all types]') {
      $('#plugins tr.plugin').show();
    } else {
      $('#plugins tr.plugin').each(function() {
        if ($(this).find('.type').first().text() !== type) {
          $(this).hide();
        } else {
          $(this).show();
        }
      });
    }
  });
});
