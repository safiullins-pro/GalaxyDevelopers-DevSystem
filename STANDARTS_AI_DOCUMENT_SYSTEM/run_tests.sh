#!/bin/bash

# Добавляем текущую директорию в PYTHONPATH
export PYTHONPATH="$(pwd)"

# Запускаем pytest для всех тестов в директории 01_AGENTS
python3 -m pytest 01_AGENTS/
