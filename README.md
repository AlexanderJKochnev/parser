# README.md
# Reestr Parser

Парсер сайта reestrinform.ru для извлечения данных об алкогольной продукции.

## Запуск

1. Убедитесь, что у вас установлен Docker и docker-compose.
2. Скопируйте `config.yaml` и при необходимости отредактируйте.
3. Запустите:

```bash
docker-compose up --build -d


# 1. Создайте папку и скопируйте все файлы
mkdir reestr_parser && cd reestr_parser
# (скопируйте все файлы из выше)

# 2. Запустите
docker-compose up --build