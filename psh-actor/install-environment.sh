
echo "Installing all required Python packages..."
pip3 install paho-mqtt --break-system-packages
pip3 install gpiozero --break-system-packages
echo "All packages installed"

echo "Create logs folder..."
mkdir logs

echo "Adjust access to gpio memory device..."
sudo chown root.gpio /dev/mem && sudo chmod g+rw /dev/mem

echo "All done for now. Please REBOOT!"
