from django.views.generic.base import TemplateView


class page_not_found_view(TemplateView):
    template_name = "404.html"
    status_code = 404


class error_view(TemplateView):  
    template_name = "504.html"
    status_code = 500


class permission_denied_view(TemplateView):  
    template_name = "403.html"
    status_code = 403


class bad_request_view(TemplateView):  
    template_name = "400.html"
    status_code = 400


