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
    icon = $(this).find("i");
    icon.toggleClass("fa-plus fa-minus")
})


