# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Specify the command to run the app
CMD ["python", "ttsapp.py"]

# Expose the port for the Flask app
EXPOSE 8080
