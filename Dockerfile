FROM python:3
# This prevents Python from writing .pyc files (bytecode compiled files)
# ENV PYTHONDONTWRITEBYTECODE 1
# output server responses to the terminal
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . .
RUN pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

