FROM python:3.11-slim

WORKDIR /app

# Install headless JRE for Apache Spark and essential utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME="/usr/lib/jvm/default-java"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and data
COPY . .

# Expose standard Streamlit port
EXPOSE 8501

# Run Streamlit on container startup
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
