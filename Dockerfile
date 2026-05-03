# Use the official lightweight Python image.
FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED=True

# Set working directory
WORKDIR /app

# Copy local code to the container image.
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080
EXPOSE 8080

# Run the web service on container startup.
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]
