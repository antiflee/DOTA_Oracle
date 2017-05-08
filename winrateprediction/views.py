import os
from django.shortcuts import render,redirect
from .models import Hero
from .predict_ann import predictWinRate
from .forms import ImageUploadForm
from .imageProcess import image_process
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import json


# Create your views here.
def winrateHome(request):
    form = ImageUploadForm()
    radianceNames, direNames, radianceImgUrls, direImgUrls, radianceIds, direIds = [], [], [], [], [], []
    if request.method == 'POST':
        print('POST request')
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            raw_image = request.FILES['image']
            #raw_image = ContentFile(form.cleaned_data['image'].read())
            path = default_storage.save('tmp/img.png', raw_image)
            image = os.path.join(settings.MEDIA_ROOT, path)

            radianceNames, direNames = image_process(image)
            radianceIds,radianceImgUrls = getIds(radianceNames)
            direIds,direImgUrls = getIds(direNames)
            print(radianceNames, direNames, radianceIds,direIds)
            path = default_storage.delete(image)
    heroes = Hero.objects.all()
    return render(request, 'winrateprediction/winrateHome.html', {'heroes':heroes, \
    'form':form, 'radianceNames':json.dumps(radianceNames),'radianceIds':json.dumps(radianceIds),'radianceImgUrls':json.dumps(radianceImgUrls),\
    'direNames':json.dumps(direNames),'direIds':json.dumps(direIds),'direImgUrls':json.dumps(direImgUrls)})

def winrateResult(request):
    if request.method == 'POST':
        radianceNames = request.POST['radianceNames'].split(",")
        direNames = request.POST['direNames'].split(",")
        radianceImgs = request.POST['radianceImgs'].split(",")
        direImgs = request.POST['direImgs'].split(",")
        radianceIds = [int(i) for i in request.POST['radianceIds'].split(",")]
        print(request.POST['direIds'].split(","))
        direIds = [int(i) for i in request.POST['direIds'].split(",")]
        radianceInfo = zip(radianceNames, radianceImgs)
        direInfo = zip(direNames, direImgs)
        winRate = int(predictWinRate(radianceIds, direIds) * 100)
        return render(request, 'winrateprediction/winrateResult.html', {'radianceInfo': radianceInfo, 'direInfo':direInfo, 'winRate':winRate, 'direRate':100-winRate})
    return redirect('winrateprediction:winrateHome')

def getIds(names):
    heroes = Hero.objects.all()
    ids = []
    imgUrls = []
    for name in names:
        for hero in heroes:
            if name == hero.name:
                if name == 'Axe':
                    print(hero.hero_id)
                ids.append(str(hero.hero_id))
                imgUrls.append(hero.imageUrl)
    return ids, imgUrls
