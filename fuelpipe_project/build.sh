#!/usr/bin/env bash
pip install -r requirements.txt

mkdir -p media/products

cp -r media/products/* media/products/ || true

python manage.py collectstatic --noinput
python manage.py migrate