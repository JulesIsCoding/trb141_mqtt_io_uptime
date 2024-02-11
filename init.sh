#!/bin/sh

# Update the list of available packages
echo "Updating package list..."
opkg update

# Install Python3
echo "Installing Python3..."
opkg install python3

# Install sqlite3
echo "Installing SQLite3..."
opkg install python3-sqlite3

# Install pip for Python3
echo "Installing pip for Python3..."
opkg install python3-pip

# Install the Eclipse Paho MQTT Python client library
echo "Installing Eclipse Paho MQTT Python client library..."
pip3 install paho-mqtt

# Install dotenv
echo "Installing dotenv..."
pip3 install python-dotenv

# Create folders
mkdir -p /trb141_mqtt_io_uptime
mkdir -p /etc/trb141_mqtt_io_uptime

cd /storage/trb141_mqtt_io_uptime/
# Move the package to the correct directory
echo "Moving package to the correct directory..."
mv trb141_api.py /trb141_mqtt_io_uptime/trb141_api.py
mv trb141_db.py /trb141_mqtt_io_uptime/trb141_db.py
mv mqtt.py /trb141_mqtt_io_uptime/mqtt.py
mv trb141_runtime_manager.py /trb141_mqtt_io_uptime/trb141_runtime_manager.py
mv trb141_runtime.py /trb141_mqtt_io_uptime/trb141_runtime.py
mv trb141_utility_functions.py /trb141_mqtt_io_uptime/trb141_utility_functions.py
mv main.py /trb141_mqtt_io_uptime/main.py

# Move the environment variable file and the credentials to the correct directory
echo "Moving credentials to the correct directory..."
mv aws.env /etc/trb141_mqtt_io_uptime/aws.env
mv AmazonRootCA1.pem /etc/trb141_mqtt_io_uptime/AmazonRootCA1.pem
mv certificate.pem.crt /etc/trb141_mqtt_io_uptime/certificate.pem.crt
mv private.pem.key /etc/trb141_mqtt_io_uptime/private.pem.key
cd ..

# Create system file
echo "Creating service file..."
mv /storage/trb141_mqtt_io_uptime/trb141_mqtt_io_uptime /etc/init.d/trb141_mqtt_io_uptime
chmod +x /etc/init.d/trb141_mqtt_io_uptime
/etc/init.d/trb141_mqtt_io_uptime enable
echo "Starting the service file..."
/etc/init.d/trb141_mqtt_io_uptime start

echo "Application started"