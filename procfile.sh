#!/bin/sh

if [ "$DEBUG" = "True" ]; then
        FLASK_ENV="development"
        python run.py
else
        python run.py#gunicorn app:app
fi
