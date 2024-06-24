
$(document).ready(function() {
    $('.option-group').hide(); // Hide all form groups initially
    $('#query-options').show(); // Show the query options form group
    
    $('#query-options select').change(function() {
      var selectedOption = $(this).val();
      $('.option-group').not('#query-options').hide()
      
      if (selectedOption) {
        $('#' + selectedOption).show(); // Show the selected form group
      }
    });
  });
  