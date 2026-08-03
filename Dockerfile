FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    unzip \
    python3 \
    python3-pip \
    curl \
    git \
    p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# apktool
RUN wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool && \
    wget https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && \
    chmod +x /usr/local/bin/apktool.jar

# zipalign from build-tools
RUN wget https://dl.google.com/android/repository/build-tools_r34-linux.zip && \
    unzip build-tools_r34-linux.zip -d /opt/android && \
    mv /opt/android/android-14 /opt/android/build-tools && \
    ln -s /opt/android/build-tools/zipalign /usr/local/bin/zipalign && \
    rm build-tools_r34-linux.zip

# AndResGuard (1.2.21 release asset is 404; use prebuilt JAR from upstream repo)
RUN git clone --depth 1 https://github.com/shwenzhang/AndResGuard.git /tmp/AndResGuard && \
    cp /tmp/AndResGuard/tool_output/AndResGuard-cli-1.2.15.jar /opt/AndResGuard.jar && \
    rm -rf /tmp/AndResGuard

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY bot.py env_loader.py .
COPY config/ config/

CMD ["python3", "bot.py"]
