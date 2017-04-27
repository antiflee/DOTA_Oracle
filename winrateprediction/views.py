from django.shortcuts import render,redirect
from .models import Hero
from .predict_ann import predictWinRate
from .forms import ImageUpload

# Create your views here.
def winrateHome(request):
    heroes = Hero.objects.all()
    return render(request, 'winrateprediction/winrateHome.html', {'heroes':heroes})

def winrateResult(request):
    if request.method == 'POST':
        radianceNames = request.POST['radianceNames'].split(",")
        direNames = request.POST['direNames'].split(",")
        radianceImgs = request.POST['radianceImgs'].split(",")
        direImgs = request.POST['direImgs'].split(",")
        radianceIds = [int(i) for i in request.POST['radianceIds'].split(",")]
        direIds = [int(i) for i in request.POST['direIds'].split(",")]
        radianceInfo = zip(radianceNames, radianceImgs)
        direInfo = zip(direNames, direImgs)
        winRate = int(predictWinRate(radianceIds, direIds) * 100)
        return render(request, 'winrateprediction/winrateResult.html', {'radianceInfo': radianceInfo, 'direInfo':direInfo, 'winRate':winRate, 'direRate':100-winRate})
    return redirect('winrateprediction:winrateHome')
