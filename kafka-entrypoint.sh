#!/bin/bash
if [ -f "/data/kafka/meta.properties" ]; then
    rm -f /data/kafka/meta.properties
fi

echo "Starting Kafka..."
exec "$@"
