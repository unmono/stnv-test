# Use the official Python 3.11 image as the base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /src

# Copy requirements.txt to the container's working directory
COPY requirements.txt ./requirements.txt

# Install any dependencies listed in requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code to the working directory
COPY . .

ENV SECRET_KEY=SOME_SECRET_KEY
ENV DB_PATH=db.sqlite

# Set the command to run the main file on container startup
CMD ["fastapi", "run", "src/main.py"]

EXPOSE 8000