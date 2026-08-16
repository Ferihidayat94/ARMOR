FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install nginx, supervisor, dan dependencies
RUN apt-get update && apt-get install -y     gcc     libpq-dev     nginx     supervisor     curl     && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements_docker.txt .
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copy project
COPY . .

# Embed nginx config
COPY nginx-embed.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Embed supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/armor.conf

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 80 443

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/armor.conf"]
