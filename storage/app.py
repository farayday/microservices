import connexion
import json
import functools
from models import IncidentReport, ConditionsReport
from database import make_session
import yaml
import logging.config
from datetime import datetime, timezone
from sqlalchemy import select
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import os


with open("/app/config/storage/storage_conf.yml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("/config/log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    service_name = os.getenv("SERVICE_NAME", "default_service")
log_file_path = f"/logs/{service_name}.log"
if "file" in LOG_CONFIG["handlers"]:
    LOG_CONFIG["handlers"]["file"]["filename"] = log_file_path
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")


def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()

    return wrapper


# @use_db_session
# def get_traffic_conditions(session, start_timestamp, end_timestamp):

#     start_datetime = datetime.fromisoformat(start_timestamp).replace(
#         tzinfo=timezone.utc
#     )
#     end_datetime = datetime.fromisoformat(end_timestamp).replace(tzinfo=timezone.utc)

#     statement = select(ConditionsReport).where(
#         ConditionsReport.date_created >= start_datetime,
#         ConditionsReport.date_created < end_datetime,
#     )

#     event_list = [
#         result.to_dict() for result in session.execute(statement).scalars().all()
#     ]

#     logger.info(
#         f"Retrieved {len(event_list)} traffic conditions reports between {start_timestamp} and {end_timestamp}"
#     )

#     return event_list, 200


# @use_db_session
# def get_traffic_incidents(session, start_timestamp, end_timestamp):

#     start_datetime = datetime.fromisoformat(start_timestamp).replace(
#         tzinfo=timezone.utc
#     )
#     end_datetime = datetime.fromisoformat(end_timestamp).replace(tzinfo=timezone.utc)

#     statement = select(IncidentReport).where(
#         IncidentReport.date_created >= start_datetime,
#         IncidentReport.date_created < end_datetime,
#     )

#     event_list = [
#         result.to_dict() for result in session.execute(statement).scalars().all()
#     ]

#     logger.info(
#         f"Retrieved {len(event_list)} traffic incident reports between {start_timestamp} and {end_timestamp}"
#     )

#     return event_list, 200


@use_db_session
def process_traffic_conditions(session, body):

    # commit condition report event to the database
    condition_report = ConditionsReport(
        device_id=body.get("device_id"),
        location=body.get("location"),
        vehicle_count=body.get("vehicle_count"),
        average_speed=body.get("average_speed"),
        timestamp=body.get("timestamp"),
        trace_id=body.get("trace_id"),
    )
    session.add(condition_report)
    session.commit()

    trace_id = body.get("trace_id")
    logger.debug(f"Stored event conditions_report with a trace_id of {trace_id}")
    return


@use_db_session
def process_traffic_incidents(session, body):
    # commit traffic incident to database
    incident_report = IncidentReport(
        reporter_id=body.get("reporter_id"),
        location=body.get("location"),
        incident_type=body.get("incident_type"),
        description=body.get("description"),
        timestamp=body.get("timestamp"),
        trace_id=body.get("trace_id"),
    )
    session.add(incident_report)
    session.commit()

    trace_id = body.get("trace_id")
    logger.debug(f"Stored event incident_report with a trace_id of {trace_id}")
    return


@use_db_session
def process_messages(session):
    """Process event messages"""
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"  # localhost:9092
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(
        consumer_group=b"event_group",
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST,
    )
    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode("utf-8")
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]

        if msg["type"] == "conditions_report":
            # Store the event1 (i.e., the payload) to the DB
            process_traffic_conditions(payload)
            logger.info(
                f"Processed conditions_report with trace_id: {payload.get('trace_id')}"
            )

        elif msg["type"] == "incident_report":
            # Store the event2 (i.e., the payload) to the DB
            process_traffic_incidents(payload)
            logger.info(
                f"Processed incident_report with trace_id: {payload.get('trace_id')}"
            )
        # Commit the new message as being read
        consumer.commit_offsets()


def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("traffic-api.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    from database import create_tables, drop_tables

    drop_tables()
    create_tables()
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")
