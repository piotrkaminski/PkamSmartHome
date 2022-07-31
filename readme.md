# Installation

## Install openHabian with OpenHab

1. Install latest stable version of openHABian on SD card using instruction https://www.openhab.org/docs/installation/openhabian.html
    1. First boot requires to be connect to internet via cable (preferably) and can take a first long coffee break (~1 hour 15 minutes)
    1. If there will be keyboard and display attached, you will be asked for user name to create account - please use `pshactor` This account will be used for PkamSmartHome actor service. This user also is sudoer, used for operation system configuration.
    1. You can watch progress on http://your-ip/ page.
    1. Initial login and passwords to operating system are openhabian/openhabian
1. Login to operating system shell as `pshactor` created above, using `sudo openhabian-config` set following configuration
    1. Set you host name (menu 30 -> 31)
    1. Disable wifi (menu 30 -> 37)
    1. Install Mosquitto (menu 20 -> 23), use blank password for unencrypted communication
    1. Enable NTP time synchronisation (menu 30 -> Enable NTP)
1. Open openHAB console on page http://your-ip:8080
    1. create admin account
    1. point location or you home
    1. install following Add-ons:
       1. Astro Binding,
       1.  HomeKit Integration,
       1.  MQTT Binding,
       1.  NTP Binding,
       1. TP-Link Smart Home Binding
1. Reboot system `sudo reboot`

## Install required dependencies

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
1. Install service and set to be automatically started after machine boots
    ```
    cd ~/PkamSmartHome/linux-service
    sudo ./install-service.sh
    ```
1. Service psh-actor is already started. Status can be checked by
    ```
    sudo systemctl status psh-actor
    ```

## Add auto-discovered Things
1. Login into admin console http://your-ip:8080
1. Go to Settings -> Inbox
1. Each auto discovered Thing should be added by
    1. Click on Thing name
    2. Click 'Add as Thing'

# Executables Update

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
