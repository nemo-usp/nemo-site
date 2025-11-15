# Deploying the Application with Docker

This document provides instructions on how to deploy the application using Docker.

## Prerequisites

- Docker installed on your machine.

## Building the Docker Image

1.  Navigate to the root directory of the project.
2.  Build the Docker image by running the following command:

    ```bash
    docker build -t nemo-app .
    ```

## Running the Docker Container

1.  Run the Docker container using the following command. The `-v` flags mount the local `posts`, `instance`, and `static/uploads` directories into the container, ensuring that your data is persisted even after the container is stopped.

    ```bash
    docker run -p 8000:8000 \
      -v $(pwd)/posts:/app/posts \
      -v $(pwd)/instance:/app/instance \
      -v $(pwd)/static/uploads:/app/static/uploads \
      --env-file .env \
      nemo-app
    ```

2.  The application will be accessible at `http://localhost:8000`.

## Security Considerations

### Use HTTPS in Production

For a production environment, it is strongly recommended to serve the application over HTTPS to ensure that all traffic is encrypted. You can achieve this by using a reverse proxy like Nginx or Apache in front of the Gunicorn server. The reverse proxy would handle the SSL/TLS termination and forward requests to the application.

## Environment Variables

The application requires the following environment variables to be set:

-   `SECRET_KEY`: A secret key for the application.
-   `DATABASE_URL`: The URL for the database.

These variables can be set in a `.env` file in the root directory of the project.
