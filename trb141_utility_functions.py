import time
import trb141_db
import trb141_api
from datetime import datetime


def command(info_logger, error_logger, payload, thread_manager):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(
        f"[{current_time}] Received message from subscribed topic: {str(payload)}"
    )

    # Extract the 'message' dictionary from the payload
    message = payload.get('message')

    if message:  # Ensure 'message' dictionary exists
        cmd = message.get('command')

        if cmd == "set_output":
            output = message['data']['gpio']
            value = message['data']['value']
            set_output(output, value)

        elif cmd == "set_uptime":
            name = message['data']['name']
            value = message['data']['value']
            try:
                thread_manager.stop_gpio_thread()
                reading = {
                    "name": name,
                    "numericValue": value,
                    "timestamp": time.time()
                }
                try:
                    trb141_db.insert_or_update_persistent_data(
                        reading, error_logger
                    )
                    try:
                        # Device authentication details.
                        SERIAL_NUMBER = trb141_api.get_serial_number()
                        thread_manager.start_gpio_thread(SERIAL_NUMBER)
                    except Exception as e:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        error_logger.error(
                            f"[{current_time}] Error starting runtime: {e}", exc_info=True
                        )
                except Exception as e:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    error_logger.error(
                        f"[{current_time}] Error inserting or updating persistent data: {e}"
                    )
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_logger.error(
                    f"[{current_time}] Error stopping runtime: {e}", exc_info=True
                )

        elif cmd == "send_report":
            try:
                # Device authentication details.
                SERIAL_NUMBER = trb141_api.get_serial_number()
                thread_manager.restart_gpio_thread(SERIAL_NUMBER)
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_logger.error(
                    f"[{current_time}] Error restarting runtime: {e}", exc_info=True
                )

        else:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_logger.info(f"[{current_time}] Unsupported method")


def set_output(output, value):
    # When one Relay output is open, the other one is closed; so to turn an output on or off, we have to change the value on both pins:
    # echo 1 > /sys/class/gpio/gpio20/value & echo 0 > /sys/class/gpio/gpio22/value
    # echo 1 > /sys/class/gpio/gpio23/value & echo 0 > /sys/class/gpio/gpio21/value

    if output == "relay_1":
        if value == 1:
            with open("/sys/class/gpio/gpio20/value", "w") as f:
                f.write("1")
            with open("/sys/class/gpio/gpio22/value", "w") as f:
                f.write("0")
        else:
            with open("/sys/class/gpio/gpio20/value", "w") as f:
                f.write("0")
            with open("/sys/class/gpio/gpio22/value", "w") as f:
                f.write("1")
    elif output == "relay_2":
        if value == 1:
            with open("/sys/class/gpio/gpio23/value", "w") as f:
                f.write("1")
            with open("/sys/class/gpio/gpio21/value", "w") as f:
                f.write("0")
        else:
            with open("/sys/class/gpio/gpio23/value", "w") as f:
                f.write("0")
            with open("/sys/class/gpio/gpio21/value", "w") as f:
                f.write("1")
