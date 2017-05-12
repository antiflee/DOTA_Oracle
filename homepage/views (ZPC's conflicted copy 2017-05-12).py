from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'homepage/home.html')

def letsencrypt(request):
    return HttpResponse('nZcaKFYf44ATKVkr9n6-97a7hZO6Pq2QdJReCE_HZfo.ci-AlUepbk4jWBShijsxfvqkRbOAk8WJM0zSR6EZ1MY')
