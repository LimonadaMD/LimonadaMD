from django.shortcuts import render

def builder(request):
    return render(request, 'builder/builder.html')

