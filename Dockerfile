FROM python:3.10-slim

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Set environment variables
# PATH is used to set the path to the virtual environment
# PYTHONUNBUFFERED is used to prevent buffering of output
# PYTHONDONTWRITEBYTECODE is used to prevent writing bytecode to the disk
# UV_COMPILE_BYTECODE is used to compile bytecode to the disk
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1

# Create /app folder if it doesn't exist, the /app folder is the current working directory 
WORKDIR /app

# Copy dependency files first for layer caching
COPY uv.lock pyproject.toml /app/

# Install uv and sync env 
RUN pip install --no-cache-dir uv
RUN uv sync --locked 

# Check if uvicorn is installed
RUN uvicorn --version

# Copy necessary files to app
COPY ./app /app

# Port will be exposed, for documentation only
EXPOSE 30000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "30000"]