FROM python:3.8-slim
RUN mkdir -p /project
RUN mkdir -p /DATA
RUN apt-get update && apt-get install -y tesseract-ocr && apt-get install -y imagemagick && apt-get clean
COPY . /project
RUN pip install -r /project/requirements.txt
RUN pip install https://github.com/Rushyanth111/Semester-Stats-Report/tarball/master
CMD ["python", "/project/main.py"]