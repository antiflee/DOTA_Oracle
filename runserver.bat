@echo off
SET CURRENTDIR="%cd%"
python %cd%\manage.py runserver
pause