import time
import trb141_db
import trb141_api
from datetime import datetime
import subprocess

def command(info_logger, error_logger, payload, thread_manager):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(
        f"[{current_time}] Received message from subscribed topic: {str(payload)}"
    )

    cmd = payload.get('command')

    if cmd == "set_output":
        output = payload['data']['gpio']
        value = payload['data']['value']
        set_output(output, value)

    elif cmd == "set_uptime":
        name = payload['data']['name']
        value = payload['data']['value']
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

    elif cmd == "update_runtime":
        update_runtime(info_logger, error_logger)

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

def run_command(info_logger, error_logger, command):
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_logger.info(f"[{current_time}] Command executed successfully: {command}")
    except subprocess.CalledProcessError as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_logger.error(f"[{current_time}] Error executing command {command}: {e.output.decode()}")

def update_runtime(info_logger, error_logger):
    
    # Change directory to /storage and download the latest version of the repo
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] Downloading latest version of the repository...")
    run_command(info_logger, error_logger, "cd /storage && wget https://api.github.com/repos/JulesIsCoding/trb141_mqtt_io_uptime/tarball -O repo.tgz && tar -xzvf repo.tgz")

    # Remove the archive
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] Removing archive...")
    run_command(info_logger, error_logger, "rm -rf /storage/repo.tgz")

    # Since the exact directory name is not known, find directories matching the pattern and move into the first one found
    directories = subprocess.check_output("ls /storage | grep JulesIsCoding", shell=True).decode().strip().split("\n")
    if directories:
        directory = directories[0]  # Assume the first directory is the correct one
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_logger.info(
            f"[{current_time}] Moving to directory: {directory}"
        )
        # Move the necessary files to the correct directory
        commands_to_run = [
            f"mv /storage/{directory}/trb141_api.py /trb141_mqtt_io_uptime/trb141_api.py",
            f"mv /storage/{directory}/trb141_db.py /trb141_mqtt_io_uptime/trb141_db.py",
            f"mv /storage/{directory}/trb141_mqtt.py /trb141_mqtt_io_uptime/trb141_mqtt.py",
            f"mv /storage/{directory}/trb141_runtime_manager.py /trb141_mqtt_io_uptime/trb141_runtime_manager.py",
            f"mv /storage/{directory}/trb141_runtime.py /trb141_mqtt_io_uptime/trb141_runtime.py",
            f"mv /storage/{directory}/trb141_utility_functions.py /trb141_mqtt_io_uptime/trb141_utility_functions.py",
            f"mv /storage/{directory}/main.py /trb141_mqtt_io_uptime/main.py",
        ]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_logger.info(f"[{current_time}] Moving new files...")
        for cmd in commands_to_run:
            run_command(info_logger, error_logger, cmd)
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_logger.error(
            f"[{current_time}] Error: Could not find the downloaded repository directory.", exc_info=True
        )

    # Remove the directory
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] Removing directory...")
    cmd = f"rm -rf /storage/{directory}"
    run_command(info_logger, error_logger, cmd)

    # Restart the trb141_mqtt_io_uptime service
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] Restarting runtime service...")
    run_command(info_logger, error_logger, "/etc/init.d/trb141_mqtt_io_uptime restart")
