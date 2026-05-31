FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y openjdk-17-jdk wget unzip python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool && chmod +x /usr/local/bin/apktool
RUN wget https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && chmod +x /usr/local/bin/apktool.jar
RUN wget https://dl.google.com/android/repository/build-tools_r34-linux.zip && unzip build-tools_r34-linux.zip -d /opt/android && mv /opt/android/android-14 /opt/android/build-tools && ln -s /opt/android/build-tools/zipalign /usr/local/bin/zipalign && rm build-tools_r34-linux.zip
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY bot.py .
CMD ["python3", "bot.py"]
