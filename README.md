# depviz — визуализатор графа зависимостей pip-пакетов

Практическая работа №2 по дисциплине «Конфигурационное управление»,
вариант 11.

## Общее описание

`depviz` — CLI-инструмент для построения и визуализации графа зависимостей
пакетов Python (pip). Готовые менеджеры пакетов и библиотеки для получения
зависимостей не используются.

Текущее состояние — **этап 1: минимальный прототип с конфигурацией**.
Приложение читает параметры из YAML-файла, проверяет их и выводит
в формате `ключ=значение`.

## Параметры конфигурации

Конфигурация задаётся в YAML-файле (по умолчанию `config.yaml`).

| Параметр           | Тип    | Обязательный | Описание |
|--------------------|--------|--------------|----------|
| `package_name`     | строка | да  | Имя анализируемого пакета (правила имён pip, PEP 508) |
| `repository`       | строка | да  | URL репозитория (`http(s)://...`) или путь к файлу тестового репозитория |
| `test_mode`        | bool   | да  | Режим работы с тестовым репозиторием: `true` — `repository` это путь к файлу, `false` — URL |
| `filter_substring` | строка | нет | Пакеты, имя которых содержит эту подстроку, исключаются из анализа (по умолчанию пустая строка) |

Пример (`config.yaml`):

```yaml
package_name: requests
repository: https://pypi.org/pypi
test_mode: false
filter_substring: ""
```

### Обработка ошибок

Все ошибки выводятся в stderr с префиксом `Ошибка конфигурации:`,
программа завершается с кодом 1. Проверяются:

- конфигурационный файл не найден или не читается;
- синтаксическая ошибка YAML, корень YAML — не словарь;
- не задан обязательный параметр или задан неизвестный;
- `package_name` пустой или не соответствует правилам имён pip;
- `repository` пустой; при `test_mode: false` — не URL `http(s)`;
  при `test_mode: true` — файл не существует;
- `test_mode` не логическое значение;
- `filter_substring` не строка.

Примеры некорректных конфигураций лежат в `examples/errors/`.

## Структура

```
src/depviz/config.py     загрузка и проверка конфигурации
src/depviz/__main__.py   точка входа CLI
tests/                   модульные тесты (unittest)
examples/                пример тестового репозитория и конфигурации
run.sh, run.bat          скрипты запуска и тестов
```

## Сборка и запуск

Требуется Python 3.10+.

```bash
python -m pip install -r requirements.txt
```

Запуск (Linux/macOS — `./run.sh`, Windows — `run.bat`):

```bash
./run.sh                                  # config.yaml
./run.sh --config examples/test_mode.yaml
```

Запуск тестов:

```bash
./run.sh test
```

## Примеры использования

```
$ ./run.sh
package_name=requests
repository=https://pypi.org/pypi
test_mode=false
filter_substring=

$ ./run.sh --config examples/test_mode.yaml
package_name=A
repository=examples/test_repo.txt
test_mode=true
filter_substring=E

$ ./run.sh --config examples/errors/bad_url.yaml
Ошибка конфигурации: repository: ожидается URL вида http(s)://..., получено 'ftp:/pypi'

$ ./run.sh --config examples/errors/missing_key.yaml
Ошибка конфигурации: не заданы параметры: repository
```
