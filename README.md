# trb141_mqtt_io_uptime
The [Teltonika TRB141](https://teltonika-networks.com/products/gateways/trb141/) is a LTE industrial gateway with I/Os.

This runtime allows the device to monitor up to 5 digital outputs, and transform digital signals into attributes such as uptime or status (boolean). More information on the device capabilities is available from the [Teltonika Wiki page](https://wiki.teltonika-networks.com/view/TRB141_Input/Output#Power_Socket_Pinout).

## Device commissioning

### Transfer the entire directory from your computer to the device
```
scp -r trb141_mqtt_io_uptime root@192.168.2.1:/storage
```

### Create the following files and insert AWS credentials:
```
nano /storage/trb141_mqtt_io_uptime/AmazonRootCA1.pem
nano /storage/trb141_mqtt_io_uptime/certificate.pem.crt
nano /storage/trb141_mqtt_io_uptime/private.pem.key
```

### Install packages
```
chmod +x /storage/trb141_mqtt_io_uptime/init.sh
/storage/trb141_mqtt_io_uptime/init.sh
```

### Test the MQTT messaging
Subscribe to the topic `trb141/{device_serial_number}/state` in AWS IoT Core to monitor the incoming messages
