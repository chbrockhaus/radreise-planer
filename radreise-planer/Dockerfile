FROM python:3.12-alpine

# Build-Argumente (von HA Supervisor übergeben, werden ignoriert wenn nicht gesetzt)
ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64

# Java 21 + Tools
# openjdk21-jre-headless ist in Alpine edge verfügbar
RUN apk add --no-cache \
    openjdk21-jre-headless \
    wget \
    unzip \
    ca-certificates \
 || apk add --no-cache \
    openjdk17-jre-headless \
    wget \
    unzip \
    ca-certificates

# BRouter herunterladen
# Fallback auf brouter.jar direkt falls Zip-Struktur abweicht
RUN mkdir -p /opt/brouter/profiles2 /opt/brouter/customprofiles && \
    wget -q --tries=3 -O /tmp/brouter.zip \
        "https://github.com/abrensch/brouter/releases/download/1.7.0/brouter_1.7.0.zip" && \
    unzip -q /tmp/brouter.zip -d /tmp/brtemp && \
    find /tmp/brtemp -name "brouter.jar" | head -1 | xargs -I{} cp {} /opt/brouter/ && \
    find /tmp/brtemp -type d -name "profiles2" | head -1 | \
        xargs -I{} sh -c 'cp -r {}/* /opt/brouter/profiles2/ 2>/dev/null || true' && \
    rm -rf /tmp/brtemp /tmp/brouter.zip && \
    test -f /opt/brouter/brouter.jar || (echo "ERROR: brouter.jar not found after extraction" && exit 1)

# App-Dateien
WORKDIR /app
COPY server.py            ./
COPY radreise_planer.html ./
COPY run.sh               ./
RUN chmod +x /app/run.sh

EXPOSE 3000

CMD ["/bin/sh", "/app/run.sh"]
