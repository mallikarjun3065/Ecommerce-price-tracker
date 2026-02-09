# Docker Setup for Smart Price Tracker

This guide explains how to run SmartPriceTracker using Docker.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the application:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - Open your browser and navigate to `http://localhost:8000`

3. **View logs:**
   ```bash
   docker-compose logs -f smart-price-tracker
   ```

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the Docker image:**
   ```bash
   docker build -t smart-price-tracker:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name smart-price-tracker \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/price_tracker.db:/app/price_tracker.db \
     smart-price-tracker:latest
   ```

3. **Access the application:**
   - Open your browser and navigate to `http://localhost:8000`

4. **View logs:**
   ```bash
   docker logs -f smart-price-tracker
   ```

5. **Stop the container:**
   ```bash
   docker stop smart-price-tracker
   docker rm smart-price-tracker
   ```

## Docker Compose Services

### smart-price-tracker
- **Image:** Built from Dockerfile
- **Port:** 8000
- **Volumes:**
  - `./data:/app/data` - Data persistence
  - `./price_tracker.db:/app/price_tracker.db` - Database persistence
- **Health Check:** Enabled
- **Restart Policy:** Unless stopped

## Environment Variables

The following environment variables are set in docker-compose.yml:
- `FLASK_APP=app.py`
- `FLASK_ENV=production`
- `PYTHONUNBUFFERED=1`

You can override these by creating a `.env` file or modifying docker-compose.yml.

## Troubleshooting

### Container exits immediately
Check logs: `docker-compose logs smart-price-tracker`

### Port already in use
Change the port mapping in docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Database not persisting
Ensure the volume mounts are correct in docker-compose.yml and the host directory has proper permissions.

### Application not responding
Check health status: `docker ps` and look at the STATUS column. If unhealthy, check logs for errors.

## Building for Production

For production deployment:

1. Use a production WSGI server (e.g., Gunicorn):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. Consider using environment-specific configurations

3. Set up proper logging and monitoring

4. Use a reverse proxy (e.g., Nginx) in front of the application
