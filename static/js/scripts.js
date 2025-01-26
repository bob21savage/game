$(document).ready(function() {
    $.ajaxSetup({
        headers: {
            'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
        }
    });
}