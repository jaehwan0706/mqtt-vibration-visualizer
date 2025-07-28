# publisher2.py
import paho.mqtt.client as mqtt
import time
import json
import os

broker_address = "localhost"
topic = "sensor/raw/B"
file_path = "C:/Users/jaehw/OneDrive/바탕 화면/백석대학교 산업협력단(인포비)/Python/fft_data.txt"

batch_size = 800
sleep_sec = 1

client = mqtt.Client()
client.connect(broker_address, 1883, 60)

try:
    while True:
        if not os.path.exists(file_path):
            print(f"❌ 파일 없음: {file_path}")
            continue

        print(f"📤 Publisher B 전송 시작")

        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = f.read()

        chunks = raw_data.split("GG")
        gg_chunks = ["GG" + chunk for chunk in chunks if chunk.strip() != ""]

        for i in range(0, len(gg_chunks), batch_size):
            batch = gg_chunks[i:i + batch_size]
            message = json.dumps(batch)
            client.publish(topic, message)
            print(f"Published {len(batch)} chunks to B")
            time.sleep(sleep_sec)

except KeyboardInterrupt:
    print("🛑 Publisher B 중단됨")
finally:
    client.disconnect()
