FROM python:3.12-alpine

# Java (für BRouter) + Download-Tools
RUN apk add --no-cache \
    openjdk21-jre-headless \
    wget \
    unzip

# BRouter herunterladen und installieren
RUN mkdir -p /opt/brouter/profiles2 /opt/brouter/customprofiles && \
    wget -q -O /tmp/brouter.zip \
        "https://github.com/abrensch/brouter/releases/download/1.7.0/brouter_1.7.0.zip" && \
    unzip -q /tmp/brouter.zip -d /tmp/brtemp && \
    find /tmp/brtemp -name "brouter.jar"  | head -1 | xargs -I{} cp {} /opt/brouter/ && \
    find /tmp/brtemp -type d -name "profiles2" | head -1 | \
        xargs -I{} sh -c 'cp -r {}/* /opt/brouter/profiles2/' && \
    rm -rf /tmp/brtemp /tmp/brouter.zip

# App-Dateien kopieren
WORKDIR /app
COPY server.py            ./
COPY radreise_planer.html ./
COPY run.sh               ./
RUN chmod +x /app/run.sh

EXPOSE 3000

CMD ["/bin/sh", "/app/run.sh"]
