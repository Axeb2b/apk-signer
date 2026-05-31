FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    unzip \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install apktool (for dummy asset addition later)
RUN wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool && \
    wget https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && \
    chmod +x /usr/local/bin/apktool.jar

# Install Android build-tools (zipalign)
RUN wget https://dl.google.com/android/repository/build-tools_r34-linux.zip && \
    unzip build-tools_r34-linux.zip -d /opt/android && \
    mv /opt/android/android-14 /opt/android/build-tools && \
    ln -s /opt/android/build-tools/zipalign /usr/local/bin/zipalign && \
    rm build-tools_r34-linux.zip

# Download AndResGuard jar (latest release)
RUN wget https://github.com/shwenzhang/AndResGuard/releases/download/1.2.21/AndResGuard-cli-1.2.21.jar -O /opt/AndResGuard.jar

# Copy bot files
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY bot.py .

# Create config directory for AndResGuard
RUN mkdir /app/andresguard-config

CMD ["python3", "bot.py"]
