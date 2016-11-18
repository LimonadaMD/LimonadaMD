from django.shortcuts import render

from lipids.models import membrane_example


# Create your views here.
def membrane_poc(request):
    context = {"membrane": membrane_example}
    return render(request, "membranes/poc.html", context=context)
