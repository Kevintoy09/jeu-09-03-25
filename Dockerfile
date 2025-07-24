# 🐳 Dockerfile pour compilation APK Android
# Environnement testé et stable pour éviter 15h de debug

FROM cimg/android:2023.12

# Versions fixes testées (anti-debug)
ENV PYTHON_VERSION=3.9.16
ENV KIVY_VERSION=2.1.0
ENV BUILDOZER_VERSION=1.5.0
ENV NDK_VERSION=25b
ENV GRADLE_VERSION=7.6

# Installation des dépendances système
USER root
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    zip \
    unzip \
    openjdk-11-jdk \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev

# Configuration Android SDK
ENV ANDROID_HOME=/opt/android/sdk
ENV ANDROID_SDK_ROOT=$ANDROID_HOME
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Installation des packages Python avec versions fixes
RUN pip3 install --upgrade pip
RUN pip3 install \
    buildozer==$BUILDOZER_VERSION \
    kivy==$KIVY_VERSION \
    kivymd==1.1.1 \
    cython==0.29.36 \
    requests==2.25.1 \
    flask==2.0.1

# Configuration Buildozer
RUN buildozer init

# Point d'entrée
WORKDIR /src
COPY . /src/

# Script de compilation
CMD ["bash", "-c", "buildozer android debug"]
