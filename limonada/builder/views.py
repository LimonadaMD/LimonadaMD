from django.shortcuts import render

def builder(request):

    data = { 'builder' : True }
    return render(request, 'builder/builder.html', data)


