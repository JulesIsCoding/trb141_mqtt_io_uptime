#
# This file handles the MQTT communication with the AWS broker
#

import time
import json
import paho.mqtt.client as mqtt
import trb141_utility_functions
from datetime import datetime


def es_mqtt(
    info_logger,
    error_logger,
    ROOT_CA,
    PRIVATE_KEY,
    CERT_FILE,
    BROKER_ENDPOINT,
    pub_topic,
    sub_topic,
    mqtt_queue,
    thread_manager,
    stop_event,
):
    connected = False

    # On successfull connections, subscribe to required topic.
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_logger.info(
                f"[{current_time}] Connected to {BROKER_ENDPOINT} successfully!"
            )
            client.subscribe(sub_topic)
            nonlocal connected
            connected = True
        else:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_logger.info(f"[{current_time}] Connection failed with error code {rc}")

    # Disconnection
    def on_disconnect(client, userdata, rc):
        nonlocal connected
        connected = False
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_logger.info(
            f"[{current_time}] Disconnected from {BROKER_ENDPOINT} with return code {rc}"
        )

    # Invoked by the mqtt client whenever a message is received.
    def on_message(client, userdata, msg):
        if msg.topic == sub_topic:
            payload = json.loads(msg.payload)  # Parse the JSON string into a dictionary
            trb141_utility_functions.command(
                info_logger, error_logger, payload, mqtt_queue, thread_manager
            )  # Call the command function with the payload as a dictionary

    def on_log(client, userdata, level, buf):
        info_logger.info(str(buf))

    # Create an MQTT client and attach our routines to it.
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_log = on_log

    # Connect to the AWS IoT broker using TLS
    client.tls_set(ROOT_CA, certfile=CERT_FILE, keyfile=PRIVATE_KEY)

    # Attempt to connect to MQTT broker.
    while not stop_event.is_set():
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_logger.info(
                f"[{current_time}] Attempting to connect to MQTT broker at {BROKER_ENDPOINT}..."
            )
            client.connect(BROKER_ENDPOINT, 8883, keepalive=60)
            break
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_logger.error(
                f"[{current_time}] Failed to connect to {BROKER_ENDPOINT}. Error: {str(e)}"
            )

        time.sleep(5)

    # Network loop.
    while not stop_event.is_set():
        # If connection was lost, attempt to reconnect.
        if not connected:
            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                info_logger.info(
                    f"[{current_time}] Attempting to connect to MQTT broker at {BROKER_ENDPOINT}..."
                )
                client.reconnect()
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_logger.error(
                    f"[{current_time}] Failed to connect to {BROKER_ENDPOINT}. Error: {str(e)}"
                )

            time.sleep(5)

        # Check the message queue for messages to publish.
        while connected and not mqtt_queue.empty():
            message = mqtt_queue.get()
            client.publish(pub_topic, message)

        client.loop(timeout=1.0)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] MQTT thread stopping")
