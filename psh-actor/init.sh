#!/bin/sh

ENV_NAME=env

echo "Making Python virtual environment"
python -m venv $ENV_NAME

echo "Installing all required dependencies"
pip3 install paho-mqtt