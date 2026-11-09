#!/bin/sh
# Запуск: ./run.sh [--config файл]   Тесты: ./run.sh test
cd "$(dirname "$0")"
export PYTHONPATH=src
if [ "$1" = "test" ]; then
    exec python -m unittest discover -s tests -v
fi
exec python -m depviz "$@"
