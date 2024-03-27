FROM python:3.11.5-slim
LABEL maintainer="Abhishek Singh Chauhan"
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]