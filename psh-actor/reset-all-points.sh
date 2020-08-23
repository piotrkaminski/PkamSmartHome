#!/bin/sh

echo "Getting Actor name to create mqtt topic..."

CLIENT_NAME=`/usr/bin/python3 ./configuration.py`

TOPIC="/$CLIENT_NAME/In/Admin"
COMMAND="RESET"

echo "Sending $COMMAND command to mqtt topic $TOPIC..."

mosquitto_pub -h localhost -t $TOPIC -m $COMMAND

echo "Done."