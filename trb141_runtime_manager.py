import threading
import trb141_runtime
from datetime import datetime


# Initialize the I/O thread manager
class runtimeThreadManager:
    def __init__(self, info_logger, error_logger, io_thread, mqtt_queue):
        self.info_logger = info_logger
        self.error_logger = error_logger
        self.io_thread = io_thread
        self.mqtt_queue = mqtt_queue

    def start_gpio_thread(self, SERIAL_NUMBER):
        try:
            stop_event = threading.Event()
            t = threading.Thread(
                target=trb141_runtime.es_runtime,
                args=(
                    self.info_logger,
                    self.error_logger,
                    SERIAL_NUMBER,
                    self.mqtt_queue,
                    stop_event,
                ),
            )
            t.start()
            self.io_thread = {"thread": t, "stop_flag": stop_event}
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.error_logger.error(f"[{current_time}] Error starting IO thread: {e}")

    def restart_gpio_thread(self, configuration):
        if self.io_thread:
            self.stop_gpio_thread()
        # Start a new thread
        self.start_gpio_thread(configuration)

    def stop_gpio_thread(self):
        self.io_thread["stop_flag"].set()
        # Remove the thread_data from the original list
        self.io_thread = {}

    def get_io_thread(self):
        return self.io_thread
