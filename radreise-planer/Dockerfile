ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11
FROM ${BUILD_FROM}

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
COPY server.py          ./
COPY radreise_planer.html ./

# Startskript
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

EXPOSE 3000

CMD ["/bin/sh", "/app/run.sh"]
