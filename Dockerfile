FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install boto3 requests flask flask-cors flask-socketio python-dotenv

# Copy the application
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000

# Run the socketio server
CMD ["python", "local_api.py"]
