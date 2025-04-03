import connexion
import json
from datetime import datetime, timezone
import yaml
import logging.config
import os
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
import os

CONFIG_DIR = os.getenv("CONFIG_DIR", "/app/config/dev")
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
CONFIG_FILE = os.path.join(CONFIG_DIR, "processing_conf.yml")
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

# with open("/app/config/prod/processing_conf.yml", "r") as f:
#     app_config = yaml.safe_load(f)

# with open("/app/config/prod/log_conf.yml", "r") as f:
#     LOG_CONFIG = yaml.safe_load(f.read())
#     service_name = os.getenv("SERVICE_NAME", "default_service")
# log_file_path = f"/app/logs/{service_name}.log"
# if "file" in LOG_CONFIG["handlers"]:
#     LOG_CONFIG["handlers"]["file"]["filename"] = log_file_path
#     logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")


def get_stats():
    logger.info("Request received for stats")

    try:
        with open(app_config["datastore"]["filename"], "r") as f:
            stats = json.load(f)
            logger.debug(f"Statistics loaded from file: {stats}")
            logger.info("Request completed")
            return stats, 200

    except FileNotFoundError:
        logger.error("Stats do not exist")
        return {"message": "Stats do not exist"}, 404


def calculate_stats(conditions_data, incidents_data):
    stats = {
        "num_condition_reports": len(conditions_data),
        "num_incident_reports": len(incidents_data),
        "max_vehicle_count": 0,
        "avg_vehicle_speed": 0,
    }

    if conditions_data:
        vehicle_counts = [report["vehicle_count"] for report in conditions_data]
        speeds = [report["average_speed"] for report in conditions_data]

        stats["max_vehicle_count"] = max(vehicle_counts)
        stats["avg_vehicle_speed"] = round(sum(speeds) / len(speeds))

    return stats


def populate_stats():
    logger.info("Starting period")

    current_time = (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )

    # set default values if file doesn't exist
    try:
        with open(app_config["datastore"]["filename"], "r") as f:
            stats = json.load(f)
            last_updated = stats.get("last_updated", "2000-01-01T00:00:00Z")
    except FileNotFoundError:
        last_updated = "2000-01-01T00:00:00Z"
        stats = {
            "num_condition_reports": 0,
            "num_incident_reports": 0,
            "max_vehicle_count": 0,
            "avg_vehicle_speed": 0,
            "last_updated": last_updated,
        }

    try:
        # get conditions data
        response = httpx.get(
            f"{app_config['eventstore']['conditions']['url']}",
            params={"start_timestamp": last_updated, "end_timestamp": current_time},
        )

        if response.status_code != 200:
            logger.error((f"Failed to get conditions data: {response.status_code}"))
            return

        conditions_data = response.json()

        # get incidents data
        response = httpx.get(
            f"{app_config['eventstore']['incidents']['url']}",
            params={"start_timestamp": last_updated, "end_timestamp": current_time},
        )

        if response.status_code != 200:
            logger.error((f"Failed to get incidents data: {response.status_code}"))
            return

        incidents_data = response.json()

        logger.info(
            f"Retrieved {len(conditions_data)} new conditions and "
            f"{len(incidents_data)} new incidents"
        )

        new_stats = calculate_stats(conditions_data, incidents_data)

        # Update existing stats with new data
        stats["num_condition_reports"] += new_stats["num_condition_reports"]
        stats["num_incident_reports"] += new_stats["num_incident_reports"]
        stats["max_vehicle_count"] = max(
            stats["max_vehicle_count"], new_stats["max_vehicle_count"]
        )

        # Update average speed (weighted average)
        if (
            stats["num_condition_reports"] > 0
            and new_stats["num_condition_reports"] > 0
        ):
            total_reports = (
                stats["num_condition_reports"] + new_stats["num_condition_reports"]
            )
            stats["avg_vehicle_speed"] = (
                (stats["avg_vehicle_speed"] * stats["num_condition_reports"])
                + (new_stats["avg_vehicle_speed"] * new_stats["num_condition_reports"])
            ) / total_reports
        elif new_stats["num_condition_reports"] > 0:
            stats["avg_vehicle_speed"] = new_stats["avg_vehicle_speed"]

        stats["last_updated"] = current_time

        # write updated stats to file
        with open(app_config["datastore"]["filename"], "w") as f:
            json.dump(stats, f)

        logger.debug(f"Updated stats: {stats}")
        logger.info("Period processing ended")

    except httpx.HTTPError as e:
        logger.error(f"Error during requests to eventstore: {e}")
        return


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(
        populate_stats, "interval", seconds=app_config["scheduler"]["interval"]
    )
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("traffic-api.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
