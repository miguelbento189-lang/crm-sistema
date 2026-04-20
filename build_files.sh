#!/bin/sh
set -e

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput

rm -rf staticfiles_build
mkdir -p staticfiles_build
cp -r staticfiles staticfiles_build/static