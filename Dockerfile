# Use official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . .

# Expose port (optional, for web apps)
EXPOSE 8080

# Command to run your bot (replace if different)
CMD ["python", "run.py"]
