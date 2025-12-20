FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=main.py
CMD ["gunicorn", "main:app", "-w", "4", "-b", "0.0.0.0:5000"]
