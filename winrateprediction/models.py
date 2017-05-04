from django.db import models
from django.contrib.auth.models import User
import numpy as np
import requests
import os

class Hero(models.Model):
    name = models.CharField(max_length=30,unique=True)
    hero_id = models.CharField(max_length=10)
    imageUrl = models.URLField(max_length=200)

    def __str__(self):
        return self.name

import dota2api

api = dota2api.Initialise('A868F8A7BDA8E1E078F87E0C9166BDF2')
heroes = api.get_heroes()
# heroes = requests.get('https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v0001/?key='+API)
heroes = heroes['heroes']

for hero in heroes:
    newHero = Hero()
    newHero.name=hero['localized_name']
    newHero.hero_id=str(hero['id'])
    newHero.imageUrl=hero['url_small_portrait']
    newHero.save()
