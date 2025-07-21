#!/bin/bash
set -e

echo "[INFO] Corrigindo repositórios do Debian antigo (Buster)..."
sudo sed -i 's|deb http://deb.debian.org/debian|deb http://archive.debian.org/debian|g' /etc/apt/sources.list
sudo sed -i 's|deb http://security.debian.org/debian-security|deb http://archive.debian.org/debian-security|g' /etc/apt/sources.list

echo "[INFO] Atualizando pacotes..."
sudo apt -o Acquire::Check-Valid-Until=false update

echo "[INFO] Instalando dependências SDL e libs necessárias..."
sudo apt install -y python3-dev python3-pip python3-setuptools \
libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
libportmidi-dev libfreetype6-dev libswscale-dev libavformat-dev \
libavcodec-dev libjpeg-dev libpng-dev libtiff-dev libx11-dev pkg-config

echo "[INFO] Instalando pygame via pip..."
pip3 install --upgrade --force-reinstall pygame

echo "[INFO] Instalação concluída com sucesso!"
