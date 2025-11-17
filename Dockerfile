# Use a lightweight Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy everything into the image
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Streamlit and Firebase environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_ENABLEXSRSFPROTECTION=false
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Expose the Cloud Run port
EXPOSE 8080

# Launch Streamlit on the Cloud Run port (0.0.0.0 is required)
# Updated to point to the backend folder where the Streamlit app was moved
CMD ["streamlit", "run", "backend/home.py", "--server.port=8080", "--server.address=0.0.0.0"]
