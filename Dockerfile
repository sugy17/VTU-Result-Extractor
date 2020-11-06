FROM python:3.8-slim
RUN mkdir -p /project
RUN apt-get update && apt-get install -y tesseract-ocr && apt-get install -y imagemagick && apt-get clean
COPY . /project
RUN pip install -r /project/requirements.txt
CMD ["python", "-m","/project/scrapper"]