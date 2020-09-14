#!/usr/bin/env bash
  
set -e

export FLASK_APP=app.py
export FLASK_RUN_PORT=3000

flask run
