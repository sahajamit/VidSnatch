# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Install ffmpeg for pytubefix
RUN apt-get update && apt-get install -y ffmpeg

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY web_app.py .
COPY youtube_downloader/ ./youtube_downloader/
COPY static/ ./static/

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the command to start the server
CMD ["python", "web_app.py"]
