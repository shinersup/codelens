FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first
# if code changes but requirements don't, it skips pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the FastAPI app with uvicorn
# --host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
