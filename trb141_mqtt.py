# This file handles the MQTT communication with the AWS broker

import json
import trb141_utility_functions
from datetime import datetime
import time
import subprocess

def mqtt_subscriber(info_logger, error_logger, ROOT_CA, PRIVATE_KEY, CERT_FILE, BROKER_ENDPOINT, BROKER_HOST, BROKER_QOS, sub_topic, BROKER_TLS_VERSION, BROKER_PROTOCOL_VERSION, thread_manager, stop_event):
    while not stop_event.is_set():
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_logger.info( f"[{current_time}] Subscribing to topic: {sub_topic}" )

            # Command to subscribe and listen for messages
            command = ['mosquitto_sub', '--cafile', ROOT_CA, '--cert', CERT_FILE,'--key', PRIVATE_KEY, '-h', BROKER_ENDPOINT, '-p', BROKER_HOST, '-q', BROKER_QOS, '-t', sub_topic, '--tls-version', BROKER_TLS_VERSION, '-V', BROKER_PROTOCOL_VERSION]
            # Start the subprocess
            with subprocess.Popen(command, stdout=subprocess.PIPE, text=True, bufsize=1) as proc:
                while not stop_event.is_set():
                    # Read a line of output from mosquitto_sub
                    output = proc.stdout.readline()
                    if output == '' and proc.poll() is not None:
                        break
                    if output:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        info_logger.info( f"[{current_time}] Received message: {output.strip()}" )
                        try:
                            payload = json.loads(output.strip())
                            trb141_utility_functions.command(info_logger, error_logger, payload, thread_manager)
                        except json.JSONDecodeError as e:
                            error_logger.error(f"[{current_time}] JSON parsing error: {e}", exc_info=True)
                    elif proc.poll() is not None:
                        break  # Process has terminated.
            if proc.poll() is None:  # Check if the subprocess is still running
                proc.terminate()  # Terminate the subprocess                
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_logger.error(f"[{current_time}] Failed to start MQTT subscriber process: {e}", exc_info=True)
            # Sleep for a while before attempting reconnection
            time.sleep(5)  # Adjust the sleep duration as needed
    
def mqtt_publisher(info_logger, error_logger, ROOT_CA, PRIVATE_KEY, CERT_FILE, BROKER_ENDPOINT, BROKER_HOST, BROKER_QOS, pub_topic, BROKER_TLS_VERSION, BROKER_PROTOCOL_VERSION, mqtt_queue, stop_event):

    def publish_message(message):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Convert the message to a JSON string if it's not already a string
        if not isinstance(message, str):
            message = json.dumps(message)
            
        # Prepare the command to publish the message
        command = ['mosquitto_pub', '--cafile', ROOT_CA, '--cert', CERT_FILE,'--key', PRIVATE_KEY,'-h', BROKER_ENDPOINT, '-p', BROKER_HOST, '-q', BROKER_QOS, '-t', pub_topic, '--tls-version', BROKER_TLS_VERSION, '-V', BROKER_PROTOCOL_VERSION, '-m', message]
        # Execute the command
        try:
            subprocess.run(command, check=True, capture_output=True)
            info_logger.info( f"[{current_time}] Message published to {pub_topic}" )
        except subprocess.CalledProcessError as e:
            error_logger.error( f"[{current_time}] Failed to publish message: {e}")
            # Add the message back to the queue for retry
            mqtt_queue.put(message)

    # Application loop.
    while not stop_event.is_set():
        # Check the message queue for messages to publish.
        while not mqtt_queue.empty():
            message = mqtt_queue.get()
            publish_message(message)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] MQTT thread stopping")
