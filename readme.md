# Installation

## Mosquito installation:

As root user execute following commands:

```
sudo apt-get update
sudo apt-get install mosquitto
sudo apt-get install mosquitto-clients
```
Source: https://www.instructables.com/id/Installing-MQTT-BrokerMosquitto-on-Raspberry-Pi/

## OpenHab installation

As root user execute following commands:

```
sudo apt update
sudo apt install openjdk-8-jdk

sudo apt-get install screen mc vim git htop

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

1. Open OpenHab web console and choose Standard Configuration.
1. Open OpenHab and click Paper UI console
1. For Add-ons -> Bindins install following bindings:
    1. Astro Binding
    1. MQTT Binding
    1. NTP Binding
    1. TP-Link Smart Home Binding
1. For Add-ons -> Misc install for following
    1. HomeKit Integration
1. For Configuration -> Services -> IO -> HomeKit Integration apply configuration
    1. Network Interface -> WiFi Ip address

## Install required dependecies

1. Install Python Pyho 
    ```
    pip3 install paho-mqtt
    ```

## PkamSmartHome Actor installation

1. Download project
    1. Add ssh key to GitHab
    1. Download project from git
   ```
   git clone git@github.com:piotrkaminski/PkamSmartHome.git
   ```
1. Update OpenHab configuration
    ```
    cd ~/PkamSmartHome/openhab
    sudo ./install-config.sh
    ```
1. Create log directory
   ```
   cd ~/PkamSmartHome/psh-actor 
   mkdir logs
   ```
1. Install service and set to be automaticaly started after machine boots
    ```
    cd ~/PkamSmartHome/linux-service
    sudo ./install-service.sh
    ```
1. Service psh-actor is allready started. Status can be checked by 
    ```
    sudo systemctl status psh-actor
    ```

## Additional installation component

1. It is usefull to enable SSL interface on Raspberry
    1. Raspberry Start -> Preferences -> Raspberry Pi Configuration -> Interfaces -> SSH enabled


# Executabes Update

## PkamSmartHome Actor update

1. Update code
   ```
   cd ~/PkamSmartHome 
   git pull
   sudo systemctl restart psh-actor
   ```

# Reset installation (put all points into standard mode)

## Reset all points in PkamSmartHome Actor
   ```
   cd ~/PkamSmartHome/psh-actor 
   ./reset-all-points.sh
   ```