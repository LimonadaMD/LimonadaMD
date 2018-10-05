// Use Ctrl+F5 to refresh js files on the client side when devellopping
// Ver parameter with date is used in layout.html to avoid confusion when the this file is updated

function url_replace(){
    url =  window.location.href;
    for (var i = 0, j = arguments.length; i < j; i++){
        paramName = arguments[i];
        paramValue = $('#id_'+arguments[i]).val();
        var pattern = new RegExp('('+paramName+'=).*?(&|$)'); 
        var newUrl = url.replace(pattern,'$1' + paramValue + '$2');
        var n=url.indexOf(paramName);
        if(n == -1){
            newUrl = newUrl + (newUrl.indexOf('?')>0 ? '&' : '?') + paramName + '=' + paramValue ;
        }
        url = newUrl
    }
    window.location.href = url;
}

$('#clickselect').click(function(){
    $('#collapseselect').toggle();
    $('#iconselect').toggleClass("fa-plus fa-minus")
})

$('input[type="file"]').on('change', function() {
    $(this).next('.custom-file-label').text($(this)[0].files[0].name);
});
