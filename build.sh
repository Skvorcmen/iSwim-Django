#!/bin/bash

# Установка зависимостей
pip install -r requirements.txt

# Сбор статики
python manage.py collectstatic --noinput --settings=swim_site.settings_production

# Миграции
python manage.py migrate --settings=swim_site.settings_production
