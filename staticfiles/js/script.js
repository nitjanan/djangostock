$(document).ready(function(){
    var loadForm = function () { 
      var btn = $(this);
      $.ajax({
        url: btn.attr("data-url"),
        type: 'get',
        dataType: 'json',
        beforeSend: function () {
          $("#modal-item .modal-content").html("");
          $("#modal-item").modal("show");
        },
        success: function (data) {
          $("#modal-item .modal-content").html(data.html_form);
        }
      });
    };
    /* Binding */
    $(".js-create-item").click(loadForm);
    $("#modal-item").on("submit", ".js-item-create-form", saveForm);

});

