# Installation

## Mosquito installation:

As root user execute following commands:

```
apt-get update
apt-get install mosquitto
apt-get install mosquitto-clients
```
Source: https://www.instructables.com/id/Installing-MQTT-BrokerMosquitto-on-Raspberry-Pi/

## OpenHab installation

As root user execute following commands:

```
wget -qO - 'https://bintray.com/user/downloadSubjectPublicKey?username=openhab' | sudo apt-key add -
sudo apt-get install apt-transport-https

echo 'deb https://dl.bintray.com/openhab/apt-repo2 stable main' | sudo tee /etc/apt/sources.list.d/openhab2.list
sudo apt-get update
sudo apt-get install openhab2
sudo apt-get install openhab2-addons

sudo systemctl start openhab2.service
sudo systemctl status openhab2.service

sudo systemctl daemon-reload
sudo systemctl enable openhab2.service

```
OpenHab is up and running on http://localhost:8080. Fist start takes few minutes (literally), take a break for coffee.

Source: https://www.openhab.org/docs/installation/linux.html

## OpenHab configuration

1. Open OpenHab web console and choose Standard COnfiguration.
2. Open OpenHan and click Paper UI console
3. For Add-ons -> Bindins install followin bindings:
    1. NTP Binding
    2. MQTT Binding

## Install required dependecies

1. Install Python Pyho 
    ```
    pip3 install paho-mqtt
    ```

## PkamSmartHome Actor installaction

1. Download project
    1. Add ssh key to GitHab
    1. Download project from git@github.com:piotrkaminski/PkamSmartHome.git
1. Update OpenHab configuration
    ```
    cd PROJECT_DIR/openhab
    sudo ./install-config.sh
    ```
1. Install service and set to be automaticaly started after machine boots
    ```
    cd PROJECT_DIR/linux-sertice
    sudo ./install-service.sh
    ```
1. Service psh-actor is allready started. Status can be checked by 
    ```
    sudo systemctl status psh-actor
    ```