#!/usr/bin/env bash
export FLASK_APP=opendemic
export FLASK_ENV=production
python application.py
#gunicorn -w 4 -b 127.0.0.1:8080 "auggi:create_app()" # --keyfile config/privkey.pem --certfile config/cert.pem