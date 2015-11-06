function get_owner_id() {
    var url = $('#vk_group_url').val();
    if (url == "") {
        return null; 
    };
    var url_arr = url.split('/').filter(function (x) {return x != ""; });
    $.post("/getownerid", {'access_token': $('#access_token').val(), 'url': $('#vk_group_url').val()}, 
            function (data) {$('#owner_id_value').text(data['owner_id'])});
    // set spider name
    $("#spider_name").val(url_arr[url_arr.length - 1]);
};


// inspired by http://www.sanwebe.com/2013/03/addremove-input-fields-dynamically-with-jquery
$(document).ready(function() {
    var max_fields      = 10; //maximum input boxes allowed
    var wrapper         = $(".input_fields_wrap"); //Fields wrapper
    var add_button      = $(".add_field_button"); //Add button ID
   
    var x = 1; //initlal text box count
    $(add_button).click(function(e){ //on add input button click
        e.preventDefault();
        if(x < max_fields){ //max input box allowed
            x++; //text box increment
            $(wrapper).append(
                    '<div>' + 
                    '<input class="form-control input-md" type="text" name="board_url[]"/>' +
                    '<a href="#" class="remove_field">Remove</a>' + 
                    '</div>'); //add input box
        }
    });
   
    $(wrapper).on("click",".remove_field", function(e){ //user click on remove text
        e.preventDefault(); $(this).parent('div').remove(); x--;
    })
});
