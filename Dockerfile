FROM python:3.13.3-slim-bookworm

RUN apt-get update && apt-get install -y curl

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


# Install the timezone data package
# RUN apt-get install -y tzdata && \
#     rm -rf /var/lib/apt/lists/*

# Set the timezone environment variable to Cairo, Egypt
# The 'TZ' variable is used by many programs and libraries to determine the local time.
# ENV TZ="Africa/Cairo"

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]
