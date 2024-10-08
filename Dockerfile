# Use the official Python image from the Docker Hub
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Set environment variables for Django
ENV PYTHONUNBUFFERED=1

# Run the Django development server when the container launches
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

RUN ls -al /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
