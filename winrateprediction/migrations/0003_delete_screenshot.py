# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-27 06:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('winrateprediction', '0002_screenshot'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Screenshot',
        ),
    ]
