import json
from confluent_kafka import Consumer, KafkaException, KafkaError
from elasticsearch import Elasticsearch
import time

# Kafka Consumer Configuration
kafka_conf = {
    'bootstrap.servers': '192.168.0.113:9092',  # Kafka broker address
    'group.id': 'fluentd-consumer-group',         # Consumer group id
    'auto.offset.reset': 'earliest'              # Start from the earliest message
}

consumer = Consumer(kafka_conf)

# Subscribe to the topic
consumer.subscribe(['fluentd_logs'])

# Elasticsearch Configuration
es = Elasticsearch(
    hosts=["http://localhost:9200"],  # Replace with your Elasticsearch host
)

# Elasticsearch Index
index_name = 'fluentd_logs_index'

# Check if index exists, and create it if it doesn't
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)

# Dictionary to track the last heartbeat time for each node
last_heartbeat = {}

# Dictionary for mapping node_id to service names
node_service_mapping = {
    1: "PaymentService",
    2: "Orders",
    3: "Returns"
}

# Function to register or update the node status
def register_node(node_id, status):
    # Get the service name from the mapping dictionary
    service_name = node_service_mapping.get(node_id, "UnknownService")
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
    document = {
        "message_type": "REGISTRATION",
        "node_id": node_id,
        "service_name": service_name,
        "status": status,
        "timestamp": timestamp
    }

    # Update or create the document in Elasticsearch
    response = es.index(index=index_name, document=document)
    print(f"Node {node_id} registered/updated with status {status} at {timestamp}")

# Check the status of the node and update to DOWN if no heartbeat
def check_heartbeat(node_id, current_time):
    if node_id in last_heartbeat:
        last_time = last_heartbeat[node_id]
        # If the heartbeat is older than 10 seconds, update the status to DOWN
        if current_time - last_time > 10:
            print(f"No heartbeat from node {node_id} for more than 10 seconds. Updating status to DOWN.")
            register_node(node_id, "DOWN")
    else:
        # If no heartbeat is found for the node, register it as UP
        print(f"Node {node_id} registered with status UP.")
        register_node(node_id, "UP")

# Main loop to consume Kafka messages
try:
    print("Consuming Kafka logs and sending to Elasticsearch...")
    while True:
        msg = consumer.poll(timeout=20.0)
        if msg is None:
            print("No message received")  # Debug print
            continue
        if msg.error():
            print(f"Kafka error: {msg.error()}")
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f"End of partition {msg.partition}")
        else:
            try:
                # Decode the message
                decoded_message = msg.value().decode('utf-8')

                # Parse JSON if the message is in JSON format
                parsed_message = json.loads(decoded_message)

                # Process logs based on message type
                if parsed_message.get('message_type') == 'LOG':
                    # Process logs based on log_level
                    log_level = parsed_message.get('log_level', 'INFO')
                    if log_level in ('WARN', 'ERROR'):
                        print(f"ALERT {log_level}: {parsed_message}")
                    else:
                        continue
                elif parsed_message.get('message_type') == 'HEARTBEAT':
                    # If it's a heartbeat message, register or update the node
                    node_id = parsed_message.get('node_id')

                    # Register the node if it's the first heartbeat or update last heartbeat time
                    current_time = time.time()
                    last_heartbeat[node_id] = current_time

                    # Register the node as UP
                    register_node(node_id, "UP")

                else:
                    # Process other message types (e.g., registration)
                    print(f"{parsed_message['message_type']}: {parsed_message}")
                    continue

                # Store the log in Elasticsearch
                response = es.index(index=index_name, document=parsed_message)
                #print(f"Log stored in Elasticsearch with ID: {response['_id']}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}, message: {msg.value()}")
            except Exception as e:
                print(f"Error processing message: {e}")

        # Check for heartbeat timeout and update node status accordingly
        current_time = time.time()
        for node_id in last_heartbeat.keys():
            check_heartbeat(node_id, current_time)

except KeyboardInterrupt:
    print("Consumer interrupted")
finally:
    consumer.close()

