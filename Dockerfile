# Use the official Python image as the base image
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    s3fs \
    awscli \
    libxcb-xinerama0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install the dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose port 5000
EXPOSE 5000

# Start the Flask application
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:5000"]
# CMD ["python", "main.py"]