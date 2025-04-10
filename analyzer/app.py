import connexion
import json
import yaml
import logging.config
from pykafka import KafkaClient
import os
from flask_cors import CORS


CONFIG_DIR = os.getenv("CONFIG_DIR", "/app/config/dev")
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
CONFIG_FILE = os.path.join(CONFIG_DIR, "analyzer_conf.yml")
LOG_CONFIG_FILE = os.path.join(CONFIG_DIR, "log_conf.yml")

with open(CONFIG_FILE, "r") as f:
    app_config = yaml.safe_load(f.read())

with open(LOG_CONFIG_FILE, "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())


service_name = os.getenv("SERVICE_NAME", "default_service")
log_file_path = os.path.join(LOG_DIR, f"{service_name}.log")

if "file" in LOG_CONFIG["handlers"]:
    LOG_CONFIG["handlers"]["file"]["filename"] = log_file_path
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")

# with open("/app/config/prod/analyzer_conf.yml", "r") as f:
#     app_config = yaml.safe_load(f.read())


# with open("/app/config/prod/log_conf.yml", "r") as f:
#     LOG_CONFIG = yaml.safe_load(f.read())
#     service_name = os.getenv("SERVICE_NAME", "default_service")
# log_file_path = f"/app/logs/{service_name}.log"
# if "file" in LOG_CONFIG["handlers"]:
#     LOG_CONFIG["handlers"]["file"]["filename"] = log_file_path
#     logging.config.dictConfig(LOG_CONFIG)

# logger = logging.getLogger("basicLogger")


def get_traffic_conditions_by_index(index):
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000
    )

    logger.info(f"Searching for traffic conditions at index {index}")

    conditions_count = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data.get("type") == "conditions_report":
            if conditions_count == index:
                logger.debug(f"Found conditions report at index {index}")
                return data["payload"], 200
            conditions_count += 1

    logger.error(f"Could not find conditions report at index {index}")
    return {"message": f"No conditions report at index {index}"}, 404


def get_traffic_incidents_by_index(index):
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000
    )

    logger.info(f"Searching for traffic incident at index {index}")

    incidents_count = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data.get("type") == "incident_report":
            if incidents_count == index:
                logger.debug(f"Found incident report at index {index}")
                return data["payload"], 200
            incidents_count += 1

    logger.error(f"Could not find incident report at index {index}")
    return {"message": f"No incident report at index {index}"}, 404


def get_stats():
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000
    )

    stats = {"num_conditions": 0, "num_incidents": 0}

    logger.info("Calculating statistics")

    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data.get("type") == "conditions_report":
            stats["num_conditions"] += 1
        elif data.get("type") == "incident_report":
            stats["num_incidents"] += 1

    logger.debug(f"Statistics calculated: {stats}")
    return stats, 200


app = connexion.FlaskApp(__name__, specification_dir="")
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    CORS(app.app, resources={r"/*": {"origins": "*"}})
    app.add_api(
        "traffic-api.yaml",
        base_path="/analyzer",
        strict_validation=True,
        validate_responses=True,
    )


if __name__ == "__main__":

    app.run(port=8110, host="0.0.0.0")
