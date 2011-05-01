#!/bin/sh
rm -r /var/log/manabi/profiles/
mkdir -p /var/log/manabi/profiles/
python manage.py runprofileserver --prof-path /var/log/manabi/profiles/ --nomedia --use-cprofile
