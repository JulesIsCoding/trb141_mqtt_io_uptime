import sys
import os
import queue
import threading
import signal
import time
from datetime import datetime
import trb141_mqtt
import trb141_db
import trb141_api
import trb141_runtime_manager
import logging
import logging.handlers


def setup_logger(name, log_file, level):
    """Function to set up a logger with rotating file handler."""
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=1
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# Device authentication details.
SERIAL_NUMBER = trb141_api.get_serial_number()
ROOT_CA = os.environ.get("ROOT_CA")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
CERT_FILE = os.environ.get("CERT_FILE")
BROKER_ENDPOINT = os.environ.get("BROKER_ENDPOINT")

# Thread for IO
io_thread = {}

# Global flag to indicate if the application should keep running
keep_running = True

# MQTT topic details
sub_topic = "trb141/" + str(SERIAL_NUMBER) + "/command"
pub_topic = "trb141/" + str(SERIAL_NUMBER) + "/state"


# Signal handler function
def signal_handler(signum, frame):
    try:
        global keep_running
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_logger.info(f"[{current_time}] Received signal {signum}. Shutting down...")
        keep_running = False
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_logger.error(f"[{current_time}] Error handling signal {signum}: {e}")


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    error_logger = setup_logger(
        "error_logger", "/var/log/trb141_mqtt_io_uptime_error.log", logging.ERROR
    )
    info_logger = setup_logger("info_logger", "/var/log/trb141_mqtt_io_uptime_info.log", logging.INFO)

    trb141_db.init_database(info_logger, error_logger)

    # If the device is not connected and the workflows are sending messages, this queue can grow indefinitely. Probably a good idea add a max size in the future
    mqtt_queue = queue.Queue()
    thread_manager = trb141_runtime_manager.runtimeThreadManager(
        info_logger, error_logger, io_thread, mqtt_queue
    )

    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Initialize the runtime thread
        thread_manager.start_gpio_thread(SERIAL_NUMBER)
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_logger.error(f"[{current_time}] Error retrieving persistent data: {e}")

    # Initialize the MQTT client
    stop_event = threading.Event()
    mqtt_publish_thread = threading.Thread(
        target=trb141_mqtt.mqtt_publisher,
        args=(info_logger, error_logger, ROOT_CA, PRIVATE_KEY, CERT_FILE, BROKER_ENDPOINT, pub_topic, sub_topic, mqtt_queue, thread_manager, stop_event, ),
    )
    mqtt_publish_thread.start()
    mqtt_subscribe_thread = threading.Thread(
        target=trb141_mqtt.mqtt_subscriber,
        args=(info_logger, error_logger, ROOT_CA, PRIVATE_KEY, CERT_FILE, BROKER_ENDPOINT, pub_topic, sub_topic, mqtt_queue, thread_manager, stop_event, ),
    )
    mqtt_subscribe_thread.start()

    # Main loop - check the keep_running flag periodically
    try:
        while keep_running:
            try:
                io_thread = thread_manager.get_io_thread()
                if io_thread:
                    t = io_thread["thread"]
                    stop_flag = io_thread["stop_flag"]
                    if not t.is_alive() and not stop_flag.is_set():
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        info_logger.info(
                            f"[{current_time}] Runtime thread has stopped. Restarting..."
                        )
                        thread_manager.restart_gpio_thread()
                time.sleep(10)
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_logger.error(
                    f"[{current_time}] Error in the main loop: {e}", exc_info=True
                )
                sys.exit(1)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_logger.info(f"[{current_time}] Main loop exited")
    finally:
        stop_event.set()
        io_thread = thread_manager.get_io_thread()
        if io_thread:
            t = io_thread["thread"]
            stop_flag = io_thread["stop_flag"]
            stop_flag.set()
            t.join()
        mqtt_publish_thread.join()
        mqtt_subscribe_thread.join()
