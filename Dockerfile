FROM python:3.8-alpine
RUN mkdir -p /project
RUN apk update && apk add tesseract-ocr && apk add imagemagick && apk cache clean
COPY . /project
RUN pip install -r /project/requirements.txt
CMD ["python", "/project/main.py"]