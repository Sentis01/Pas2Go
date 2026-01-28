#!/bin/bash

# Скрипт для запуска веб-приложения транслятора

cd "$(dirname "$0")/code/webapp"
python3 app.py
