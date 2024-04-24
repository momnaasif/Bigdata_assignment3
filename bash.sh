#!/bin/bash

# Start Zookeeper
echo "Starting Zookeeper..."
bin/zookeeper-server-start.sh config/zookeeper.properties &

sleep 5  # Wait for Zookeeper to start

# Start Kafka broker
echo "Starting Kafka broker..."
bin/kafka-server-start.sh config/server.properties &

sleep 10  # Wait for Kafka broker to start

# Start the producer
echo "Starting Kafka producer..."
python3 producer.py

# Start the three consumers
echo "Starting Kafka consumers..."
python3 consumer1.py &
python3 consumer2.py &
python3 consumer3.py &



# Optionally, you can add a message indicating the processes have started
echo "Kafka setup complete."

