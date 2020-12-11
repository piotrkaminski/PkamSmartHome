#!/bin/sh

echo "Getting Actor name from configuration to identify mqtt topic name..."

CLIENT_NAME=`/usr/bin/python3 ./configuration.py`

TOPIC="/$CLIENT_NAME/In/Admin"
COMMAND="NOTIFY_CURRENT_STATE"

echo "Sending $COMMAND command to mqtt topic $TOPIC..."

mosquitto_pub -h localhost -t $TOPIC -m $COMMAND

echo "Done."
