FROM python:3.6

WORKDIR /home

# Vademécum (INF-01): Ghostscript comprime las fichas PDF. Debian 11 (base de python:3.6)
# solo sigue disponible en archive.debian.org.
RUN printf "deb http://archive.debian.org/debian bullseye main\ndeb http://archive.debian.org/debian-security bullseye-security main\n" > /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends ghostscript \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install -r requirements.txt
RUN pip install requests

EXPOSE 5000

ENTRYPOINT ["python"]

CMD ["run.py"]