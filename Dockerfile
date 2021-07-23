FROM python:3.6

WORKDIR /home

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python"]

CMD ["run.py"]