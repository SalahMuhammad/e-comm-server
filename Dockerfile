FROM python:3.13.3-slim-bookworm

# RUN apt-get update && apt-get install -y curl
# RUN apt-get install -y postgresql-client

# 1. Update package list and install necessary tools for adding repositories
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    # Clean up apt lists to reduce image size
    && rm -rf /var/lib/apt/lists/*

# 2. Add the PostgreSQL PGDG repository
# The LSB release command (lsb_release -cs) will dynamically get the current Debian codename (bookworm)
# and use it to configure the correct repository source.
RUN curl -o /etc/apt/keyrings/postgresql.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/postgresql.asc] https://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update

# 3. Install the specific version 17 client utilities
# This will install the package `postgresql-client-17` and set the v17 client as the default link.
RUN apt-get install -y postgresql-client-17 \
    # Clean up again
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


# Install the timezone data package
# RUN apt-get install -y tzdata && \
#     rm -rf /var/lib/apt/lists/*

# Set the timezone environment variable to Cairo, Egypt
# The 'TZ' variable is used by many programs and libraries to determine the local time.
# ENV TZ="Africa/Cairo"

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]
