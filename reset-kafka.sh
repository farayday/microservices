#!/bin/bash
# Stop the services
docker-compose stop kafka zookeeper

# Remove the meta.properties file
rm -f ./data/kafka/meta.properties

# Start the services again
docker-compose start zookeeper
sleep 5
docker compose start kafka
