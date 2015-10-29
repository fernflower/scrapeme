function get_value_from_hash(key) {
    var arr = window.location.hash.split('&').map(function (x) {
        var res = x.split('='); return {value:res[1], key:res[0].replace('#', '')}});
    var res = arr.filter(function (obj) {
        return obj.key == key});
    if (res.length) {return res[0].value;};
};

function fill_in_token_data() {
    var params = ['access_token', 'user_id', 'expires_in'];
    for (i in params) {
        var key = params[i];
        $('#' + key).val(get_value_from_hash(key));
    };
};

$(document).ready(function() {
    fill_in_token_data();
});
