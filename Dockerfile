# Use an official Python runtime as a parent image
FROM python:3.10.11-alpine3.18

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY ./app .

# Run the command to start the application
# CMD ["python3", "-u", "server.py"]
CMD [ "/bin/sh" ]