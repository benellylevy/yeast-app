import os
import sys
import time
from datetime import datetime
import random
import ast
import json
import ujson
import paho.mqtt.client as mqtt_client


BROKER = 'localhost'
PORT = 1883
TOPIC = "status/T_controller"
CLIENT_ID = f'python-mqtt-{random.randint(0, 100)}'
USERNAME = ''
PASSWORD = ''
NAME_FOLDER = None 


def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")
    client = mqtt_client.Client(CLIENT_ID)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client

def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            normalized = payload.replace('true', '1').replace('false', '0')
            data = ast.literal_eval(normalized)
            now = datetime.now()
            timestr = now.strftime("%Y%m%d-%H%M%S")
            data['Date'] = timestr
            json_data = ujson.dumps(data)
            output_path = os.path.join(NAME_FOLDER, f"{timestr}.json")
            with open(output_path, "w") as f:
                f.write(json_data)
        except Exception as e:
            print("Error processing message:", e)
    
    client.subscribe(TOPIC)
    client.on_message = on_message

def run():
    client = connect_mqtt()
    subscribe(client)
    
    start_time = time.time()
    duration = 7200  # 2 שעות = 7200 שניות
    while time.time() - start_time < duration:
        client.loop(timeout=1.0)
    print("2 hours passed. Restarting the script.")

def main():
    global NAME_FOLDER
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            if "name_folder" not in config:
                print("Error: The JSON config does not contain the key 'name_folder'.")
                sys.exit(1)
            NAME_FOLDER = config["name_folder"]
            print(f"Name Folder: {NAME_FOLDER}")
        except Exception as e:
            print("Error reading JSON config:", e)
            sys.exit(1)
    else:
        print("No JSON config path provided. Exiting.")
        sys.exit(1)

    print(f"MQTT script started for experiment folder: {NAME_FOLDER}")
    while True:
        run()
        time.sleep(5)

if __name__ == '__main__':
    main()