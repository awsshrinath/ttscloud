# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies required for FFmpeg and GCS
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY . .

# Install required Python packages
RUN pip install -r requirements.txt

# Expose the port for the Flask app
EXPOSE 8080

# Run the application
CMD ["python", "vdocomp.py"]
