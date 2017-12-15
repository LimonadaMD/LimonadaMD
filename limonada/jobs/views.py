from django.shortcuts import render

def jobs(request):

    data = { 'jobs' : True }
    return render(request, 'jobs/jobs.html', data)

