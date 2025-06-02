import json
import time
import uuid
from datetime import datetime
import threading
import random
import os

class Microservice:
    def __init__(self, service_name):
        self.service_name = service_name
        self.node_id = 2  # Generate unique node ID
        self.log_file = os.path.join(os.path.dirname(__file__), "microservice2.log")  # Local log file path

    def write_log(self, log_message):
        """
        Write log messages to a file.
        """
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_message) + "\n")

    def register_node(self):
        """
        Register the microservice node with the system.twtw
        """
        registration_message = {
            "node_id": self.node_id,
            "message_type": "REGISTRATION",
            "service_name": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "UP"
        }
        self.write_log(registration_message)
        print(f"Node Registration Message Sent: {registration_message}")

    def send_heartbeat(self, interval=5):
        """
        Sends heartbeat messages at fixed intervals.
        """
        while True:
            heartbeat_message = {
                "node_id": self.node_id,
                "message_type": "HEARTBEAT",
                "status": "UP",
                "timestamp": datetime.utcnow().isoformat()
            }
            self.write_log(heartbeat_message)
            print(f"Heartbeat Message Sent: {heartbeat_message}")
            time.sleep(interval)

    def log_info(self, message):
        """
        Send an INFO level log.
        """
        log_message = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "INFO",
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.write_log(log_message)
        print(f"INFO Log Sent: {log_message}")

    def log_warn(self, message, response_time_ms, threshold_limit_ms):
        """
        Send a WARN level log.
        """
        log_message = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "WARN",
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "response_time_ms": response_time_ms,
            "threshold_limit_ms": threshold_limit_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.write_log(log_message)
        print(f"WARN Log Sent: {log_message}")

    def log_error(self, message, error_code, error_message):
        """
        Send an ERROR level log.
        """
        log_message = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": "ERROR",
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "error_details": {
                "error_code": error_code,
                "error_message": error_message
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        self.write_log(log_message)
        print(f"ERROR Log Sent: {log_message}")

    def generate_logs(self, interval=10):
        """
        Periodically generate INFO, WARN, and ERROR logs.
        """
        while True:
            # Randomly choose a log type to generate
            log_type = random.choice(["INFO", "WARN", "ERROR"])

            if log_type == "INFO":
                self.log_info("Periodic INFO log generated.")
            elif log_type == "WARN":
                self.log_warn(
                    "Response time nearing threshold.",
                    response_time_ms=random.randint(1500, 2500),
                    threshold_limit_ms=2000
                )
            elif log_type == "ERROR":
                self.log_error(
                    "Simulated error occurred.",
                    error_code="500",
                    error_message="Internal Server Error"
                )

            time.sleep(interval)

    def start(self):
        """
        Starts the microservice by registering and sending heartbeats.
        """
        self.register_node()
        threading.Thread(target=self.send_heartbeat, daemon=True).start()
        threading.Thread(target=self.generate_logs, daemon=True).start()


if __name__ == "__main__":
    service = Microservice(service_name="Orders")
    service.start()

    # Keep the main thread alive to let other threads run indefinitely
    while True:
        time.sleep(1)
