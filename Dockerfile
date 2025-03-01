FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Install necessary packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY . /app

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Expose the application port
EXPOSE 5000

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
