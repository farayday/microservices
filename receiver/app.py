import logging.config
import connexion
from connexion import NoContent
import json
import uuid
import yaml
from pykafka import KafkaClient
import datetime
import os
from flask_cors import CORS


CONFIG_DIR = os.getenv("CONFIG_DIR", "/app/config/dev")
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
CONFIG_FILE = os.path.join(CONFIG_DIR, "receiver_conf.yml")
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

# with open("/app/config/prod/receiver_conf.yml", "r") as f:
#     app_config = yaml.safe_load(f.read())

# with open("/app/config/prod/log_conf.yml", "r") as f:
#     LOG_CONFIG = yaml.safe_load(f.read())
#     service_name = os.getenv("SERVICE_NAME", "default_service")
# log_file_path = f"/app/logs/{service_name}.log"
# if "file" in LOG_CONFIG["handlers"]:
#     LOG_CONFIG["handlers"]["file"]["filename"] = log_file_path
#     logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")


kafka_client = KafkaClient(
    hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}"
)
topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]


def generate_trace_id():
    return str(uuid.uuid4())


def report_traffic_conditions(body):

    trace_id = generate_trace_id()
    body["trace_id"] = trace_id
    logger.info(
        f"Received event conditions_report with a trace_id of {body['trace_id']}"
    )

    producer = topic.get_sync_producer()

    msg = {
        "type": "conditions_report",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body,
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode("utf-8"))

    logger.info(f"Sent conditions_report to Kafka with trace_id {trace_id}")

    return NoContent, 201


def report_traffic_incidents(body):

    trace_id = generate_trace_id()
    body["trace_id"] = trace_id
    logger.info(f"Received event incident_report with a trace_id of {body['trace_id']}")

    producer = topic.get_sync_producer()

    msg = {
        "type": "incident_report",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body,
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode("utf-8"))

    logger.info(f"Sent incident_report to Kafka with trace_id {trace_id}")

    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api(
    "traffic-api.yml",
    base_path="/receiver",
    strict_validation=True,
    validate_responses=True,
)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    CORS(app.app, resources={r"/*": {"origins": "*"}})


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
