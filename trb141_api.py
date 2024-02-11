import subprocess
import json


def read_gpio_status(info_logger, error_logger, source_address):
    if not all(char.isalnum() or char == "." for char in source_address):
        info_logger.info("Invalid source address.")
        return None

    ubus_command = ["ubus", "call", source_address, "status"]

    try:
        result = subprocess.check_output(ubus_command, text=True)
        status_data = json.loads(result)

        if not isinstance(status_data, dict):
            info_logger.info("Unexpected data format.")
            return None

        # Adapt the return based on the presence of either 'value' or 'state'
        value = status_data.get("value")
        state = status_data.get("state")

        # Decide what to return based on the available keys
        if value is not None:
            return {"value": value}
        elif state is not None:
            return {"state": state}
        else:
            info_logger.info("Neither 'value' nor 'state' found in response.")
            return None

    except subprocess.CalledProcessError as e:
        error_logger.error("Error executing ubus command:", e)
        return None
    except json.JSONDecodeError:
        error_logger.error("Failed to decode JSON response.")
        return None


def get_serial_number():
    # Execute the shell command and get the output
    result = (
        subprocess.check_output("mnf_info -sn | sed -n '2p'", shell=True)
        .decode("utf-8")
        .strip()
    )
    return result
