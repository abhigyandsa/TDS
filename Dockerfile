FROM python:3.11-slim-buster  # Use a slim Python 3.11 base image

WORKDIR /app  # Set the working directory inside the container

COPY requirements.txt requirements.txt # Copy requirements file
RUN pip install -r requirements.txt   # Install Python dependencies

COPY . .  # Copy the rest of the application code

EXPOSE 8000  # Expose port 8000

CMD ["python", "app.py"] # Command to run the Flask application