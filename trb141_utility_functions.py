import json
import trb141_db
from datetime import datetime


def command(info_logger, error_logger, payload, mqtt_queue, thread_manager):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(
        f"[{current_time}] Received message from subscribed topic: {str(payload)}"
    )

    if payload.get("command") == "set_configuration":
        configuration = payload["data"]
        try:
            trb141_db.insert_or_update_configuration(
                configuration, info_logger, error_logger
            )
            try:
                thread_manager.restart_gpio_thread(configuration)
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_logger.error(
                    f"[{current_time}] Error starting runtime thread: {e}"
                )
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_logger.error(
                f"[{current_time}] Error inserting or updating configuration: {e}"
            )

    # if payload.get('command') == "set_output":
    #     output = payload['data']['gpio']
    #     value = payload['data']['value']
    #     set_output(output, value)

    # elif payload.get('command') == "set_counter":
    #     gpio_counter = 'counter_' + payload['data']['gpio']
    #     value = payload['data']['value']
    #     # Increment the counter
    #     with open(counters_file, 'r+') as f:
    #         counters = json.load(f)
    #         counters[gpio_counter] = value
    #         f.seek(0)
    #         json.dump(counters, f)
    #         f.truncate()

    # elif payload.get('command') == "set_uptime":
    #     gpio_uptime = 'uptime_' + payload['data']['gpio']
    #     value = payload['data']['value']
    #     # Add the uptime
    #     with open(uptimes_file, 'r+') as f:
    #         uptimes = json.load(f)
    #         uptimes[gpio_uptime] = value
    #         f.seek(0)
    #         json.dump(uptimes, f)
    #         f.truncate()

    # elif payload.get('command') == "set_user_settings":
    #     publish_schedule = payload['data']['publish_schedule']
    #     input_high_timeout = payload['data']['input_high_timeout']
    #     adc_reading_threshold = payload['data']['adc_reading_threshold']
    #     # Add the uptime
    #     with open(user_settings_file, 'r+') as f:
    #         user_settings = json.load(f)
    #         user_settings['publish_schedule'] = publish_schedule
    #         user_settings['input_high_timeout'] = input_high_timeout
    #         user_settings['adc_reading_threshold'] = adc_reading_threshold
    #         f.seek(0)
    #         json.dump(user_settings, f)
    #         f.truncate()

    # elif payload.get('command') == "send_report":
    #     es_publish.publish_messages(user_settings_file, msg_file, counters_file, uptimes_file, adc_file, pub_topic, mqtt_queue)

    # else:
    #     info_logger.info("Unsupported method")


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
