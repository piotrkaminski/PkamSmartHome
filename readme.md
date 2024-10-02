# Installation

## Install openHabian with OpenHab

1. Install latest stable version of openHABian on SD card using instruction https://www.openhab.org/docs/installation/openhabian.html
    1. First boot requires to be connect to internet via cable (preferably) and can take a first long coffee break (~1 hour 15 minutes)
    1. You can watch progress on http://your-ip:81/ page.
    1. Initial login and passwords to operating system are `openhabian/openhabian`
1. Login to operating system shell as `openhabian`. Execute `sudo openhabian-config` to set following configuration:
    1. Set you host name (menu 30 -> 31)
    1. Install Mosquitto (menu 20 -> 23), use blank password for unencrypted communication despite of insisting for prividing password.
1. Change password for `openhubian` 
    1. Type in terminal `passwd`. provide current password `openhabian` and change to different one.
1. Open openHAB console on page http://your-ip:8080
    1. Create admin account
    1. Begin setup
    1. Point location or you home
    1. Skip proposed storage Add-ons
    1. Skip install discovered Add-ons, it is safer to install them manually in later phase, one by one.
    1. Install following Add-ons
        1. Astro Binding
        1. MQTT Binding
        1. NTP Binding
        1. HomeKit Integration
        1. TP-Link Smart Home Binding
1. Back to terminal and create `pshactor` user. This account will be used for PkamSmartHome actor service.
    1. Execute `sudo adduser pshactor`
    1. Provide additional details if would like to.
    1. Execute `sudo usermod -aG sudo pshactor`
    1. Exectue `sudo usermod -a -G gpio pshactor`
    1. Exectue `sudo chown root.gpio /dev/mem && sudo chmod g+rw /dev/mem`
1. Reboot system `sudo reboot`

## PkamSmartHome Actor installation

1. Login to terminal as `pshactor`
1. Download project
    1. Add ssh key to GitHab
    1. Download project from git
   ```
   git clone git@github.com:piotrkaminski/PkamSmartHome.git
   ```
1. Initialize PSH Actor environment
   ```
   cd ~/PkamSmartHome/psh-actor
   ./install-environment.sh
   ```
1. Update OpenHab configuration
    ```
    cd ~/PkamSmartHome/openhab
    sudo ./install-config.sh
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
1. Go to Settings -> Things -> Inbox
1. Each auto discovered Thing should be added by
    1. Click on Thing name
    2. Click 'Add as Thing'

# Executables Update

## PkamSmartHome Actor update

This step is needed when configuration of system is updated via GitHub. Initial installation does not require this step.

1. Update code
   ```
   cd ~/PkamSmartHome
   git pull
   sudo systemctl restart psh-actor
   ```

# Reset installation 

This step puts all points into standard (initial) mode. Initial installation does not require this step.

## Reset all points in PkamSmartHome Actor
   ```
   cd ~/PkamSmartHome/psh-actor
   ./reset-all-points.sh
   ```
