# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python
FROM python:3.12.6

# Встановимо змінну середовища
ENV APP_HOME=/app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Копіюємо всі файли проєкту до робочої директорії контейнера
COPY . .

# Встановлюємо залежності
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --only main

# Запустимо наш застосунок всередині контейнера
CMD ["python", "hw_m2_se.py"]
