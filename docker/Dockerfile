FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Default entrypoint
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
