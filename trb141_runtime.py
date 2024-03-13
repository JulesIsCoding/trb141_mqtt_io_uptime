import uuid
import time
import json
from datetime import datetime
import trb141_db
import trb141_api

def es_runtime(info_logger, error_logger, SERIAL_NUMBER, mqtt_queue, stop_event):

    configuration = {
        "polling_interval": 3600,
        "nodes": [
            {
                "address": "ioman.dwi.dwi0",
                "attributes": [
                    {"name": "pin_1_status", "type": "boolean", "invert_input": True},
                    {"name": "pin_1_uptime", "type": "time", "invert_input": True}
                ]
            },
            {
                "address": "ioman.dwi.dwi1",
                "attributes": [
                    {"name": "pin_2_status", "type": "boolean", "invert_input": True},
                    {"name": "pin_2_uptime", "type": "time", "invert_input": True}
                ]
            },
            {
                "address": "ioman.gpio.dio0",
                "attributes": [
                    {"name": "pin_3_status", "type": "boolean", "invert_input": False},
                    {"name": "pin_3_uptime", "type": "time", "invert_input": False}
                ]
            },
            {
                "address": "ioman.gpio.dio1",
                "attributes": [
                    {"name": "pin_4_status", "type": "boolean", "invert_input": False},
                    {"name": "pin_4_uptime", "type": "time", "invert_input": False}
                ]
            },
            {
                "address": "ioman.gpio.iio",
                "attributes": [
                    {"name": "isolated_input_status", "type": "boolean", "invert_input": False},
                    {"name": "isolated_input_uptime", "type": "time", "invert_input": False}
                    
                ]
            }
        ]
    }
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] GPIO runtime started")

    try:
        persistent_data = trb141_db.get_persistent_data(error_logger)
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_logger.error(f"[{current_time}] Error retrieving persistent data: {e}")

    message = {
        "serial_number": SERIAL_NUMBER,
        "message_id": uuid.uuid4().hex,
        "timestamp": time.time(),
        "readings": [],
    }

    gpios = []
    timestamp = time.time()
    readings = []

    for node in configuration["nodes"]:
        try:
            current_gpio_status = trb141_api.read_gpio_status(
                info_logger, error_logger, node["address"]
            )
            if current_gpio_status is None:
                raise ValueError(
                    f"[{current_time}] No data returned for address {node['address']}"
                )
            
            # Determine if we should use 'value' or 'state'
            value_or_state = ( current_gpio_status.get("value") if "value" in current_gpio_status else current_gpio_status.get("state") )

            if value_or_state is None:
                raise ValueError(f"'value' or 'state' not found in response for address {node['address']}")

            gpio = {
                "address": node["address"],
                "previous_value": value_or_state,
                "attributes": [],
            }
            for attribute in node["attributes"]:
                attribute["timestamp"] = timestamp
                name = attribute["name"]
                reading = {
                    "name": name,
                }
                if attribute["type"] == "time":
                    if name in persistent_data:
                        persistent_item = persistent_data[name]
                        attribute["value"] = persistent_item["numericValue"]
                        reading.update(
                            {"numericValue": persistent_item["numericValue"]}
                        )
                    else:
                        attribute["value"] = 0
                        reading.update({"numericValue": 0})

                else:
                    if value_or_state == "1":
                        reading.update({"booleanValue": True})
                        attribute["value"] = True
                    else:
                        reading.update({"booleanValue": False})
                        attribute["value"] = False

                readings.append(reading)

                gpio["attributes"].append(attribute)
            gpios.append(gpio)

        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_logger.error(
                f"[{current_time}] Error reading device input at address '{node['address']}': {e}"
            )

    if readings:
        message["readings"] = readings
        mqtt_queue.put(json.dumps(message))

    # Continuously monitor the GPIO pins
    while not stop_event.is_set():
        timestamp = time.time()
        readings = []
        message["message_id"] = uuid.uuid4().hex
        message["timestamp"] = timestamp

        for gpio in gpios:
            try:
                current_gpio_status = trb141_api.read_gpio_status(
                    info_logger, error_logger, gpio["address"]
                )
                if current_gpio_status is None:
                    raise ValueError(f"No data returned for address {node['address']}")
                
                # Determine if we should use 'value' or 'state'
                value_or_state = ( current_gpio_status.get("value") if "value" in current_gpio_status else current_gpio_status.get("state") )

                if value_or_state is None:
                    raise ValueError(
                        f"'value' or 'state' not found in response for address {node['address']}"
                    )

                for attribute in gpio["attributes"]:
                    reading = {}

                    name = attribute["name"]
                    time_elapsed = timestamp - attribute["timestamp"]

                    if value_or_state != gpio["previous_value"]:  # input value change
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        if attribute["type"] == "time":
                            # Transition from high to low
                            if value_or_state == "0":
                                attribute["value"] += time_elapsed
                                attribute["timestamp"] = timestamp
                                reading = {
                                    "name": name,
                                    "numericValue": attribute["value"],
                                    "timestamp": timestamp,
                                }
                                readings.append(reading)

                            # Transition from low to high
                            if value_or_state == "1":
                                attribute["timestamp"] = timestamp
                                reading = {
                                    "name": name,
                                    "numericValue": attribute["value"],
                                    "timestamp": timestamp,
                                }
                                readings.append(reading)
                        
                        else:
                            attribute["value"] = value_or_state
                            attribute["timestamp"] = timestamp
                            reading = {
                                "name": name,
                                "timestamp": timestamp,
                            }
                            if value_or_state == "1":
                                reading.update({"booleanValue": True})
                            else:
                                reading.update({"booleanValue": False})
                            readings.append(reading)

                    else:  # no input value change
                        if configuration["polling_interval"] <= time_elapsed:
                            if attribute["type"] == "time":
                                if value_or_state == "1":
                                    attribute["value"] += time_elapsed
                                reading = {
                                    "name": name,
                                    "numericValue": attribute["value"],
                                    "timestamp": timestamp,
                                }
                                readings.append(reading)
                                attribute["timestamp"] = timestamp
                            else:
                                reading = {
                                    "name": name,
                                    "timestamp": timestamp,
                                }
                                if value_or_state == "1":
                                    reading.update({"booleanValue": True})
                                else:
                                    reading.update({"booleanValue": False})
                                readings.append(reading)
                                attribute["timestamp"] = timestamp

                    if reading:
                        try:
                            trb141_db.insert_or_update_persistent_data(
                                reading, error_logger
                            )
                        except Exception as e:
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            error_logger.error(
                                f"[{current_time}] Error inserting or updating persistent data: {e}"
                            )

                gpio["previous_value"] = value_or_state

            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_logger.error(
                    f"[{current_time}] Error reading device input at address '{gpio['address']}': {e}"
                )
        if readings:
            message["readings"] = readings
            mqtt_queue.put(json.dumps(message))

        time.sleep(0.1)

    timestamp = time.time()
    readings = []
    message["message_id"] = uuid.uuid4().hex
    message["timestamp"] = timestamp

    for gpio in gpios:
        try:
            current_gpio_status = trb141_api.read_gpio_status(
                info_logger, error_logger, gpio["address"]
            )
            if current_gpio_status is None:
                raise ValueError(f"No data returned for address {node['address']}")
            
            # Determine if we should use 'value' or 'state'
            value_or_state = ( current_gpio_status.get("value") if "value" in current_gpio_status else current_gpio_status.get("state") )

            if value_or_state is None:
                raise ValueError(
                    f"'value' or 'state' not found in response for address {node['address']}"
                )

            for attribute in gpio["attributes"]:
                reading = {}
                name = attribute["name"]
                time_elapsed = timestamp - attribute["timestamp"]
                if attribute["type"] == "time":
                    if value_or_state == "1":
                        attribute["value"] += time_elapsed
                    reading = {
                        "name": name,
                        "numericValue": attribute["value"],
                    }
                    readings.append(reading)
                    attribute["timestamp"] = timestamp
                else:
                    reading = {
                        "name": name,
                    }
                    if value_or_state == "1":
                        reading.update({"booleanValue": True})
                    else:
                        reading.update({"booleanValue": False})
                    readings.append(reading)
                    attribute["timestamp"] = timestamp
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_logger.error(
                f"[{current_time}] Error reading device input at address '{gpio['address']}': {e}"
            )
    if readings:
        message["readings"] = readings
        mqtt_queue.put(json.dumps(message))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_logger.info(f"[{current_time}] IO thread stopping")
