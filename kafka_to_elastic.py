import json
from confluent_kafka import Consumer, KafkaException, KafkaError
from elasticsearch import Elasticsearch

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
                print(f"Parsed message: {parsed_message}")

                # Store the log in Elasticsearch
                response = es.index(index=index_name, document=parsed_message)
                print(f"Log stored in Elasticsearch with ID: {response['_id']}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}, message: {msg.value()}")
            except Exception as e:
                print(f"Error processing message: {e}")
except KeyboardInterrupt:
    print("Consumer interrupted")
finally:
    consumer.close()

