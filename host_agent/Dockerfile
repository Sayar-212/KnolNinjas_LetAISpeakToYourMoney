FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/



# Set working directory
WORKDIR /app

# Copy rest of the code
COPY . ./

# Sync dependencies
RUN uv sync


# Expose the port (adjust as needed)
EXPOSE 8080


# Run your service
CMD ["uv", "run", ".", "--host", "0.0.0.0", "--port", "8080"]

