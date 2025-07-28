import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import detrend
import threading
import json
from queue import Queue
import paho.mqtt.client as mqtt
import time

broker = "localhost"
topic_prefix = "sensor/raw/"
data_queues = {"A": Queue(), "B": Queue()}
amplitudes = {"A": [], "B": []}
timestamps = {"A": [], "B": []}
start_time = time.time()

def process_mqtt_payload(chunk_list, source):
    x_vals, y_vals, z_vals = [], [], []
    for chunk in chunk_list:
        if chunk.startswith("GG"):
            chunk = chunk[2:]
        if len(chunk) < 12:
            continue
        try:
            x = int(chunk[0:4], 16)
            y = int(chunk[4:8], 16)
            z = int(chunk[8:12], 16)
            if x >= 0x8000: x -= 0x10000
            if y >= 0x8000: y -= 0x10000
            if z >= 0x8000: z -= 0x10000
            x_vals.append(x)
            y_vals.append(y)
            z_vals.append(z)
        except:
            continue

    if x_vals and y_vals and z_vals:
        magnitude = np.sqrt(np.array(x_vals)**2 + np.array(y_vals)**2 + np.array(z_vals)**2)
        data_queues[source].put(magnitude)

def on_connect(client, userdata, flags, rc):
    client.subscribe(topic_prefix + "#")

def on_message(client, userdata, msg):
    try:
        chunk_list = json.loads(msg.payload.decode())
        topic_parts = msg.topic.split("/")
        source = topic_parts[-1]  # 'A' 또는 'B'
        if source in data_queues:
            process_mqtt_payload(chunk_list, source)
    except Exception as e:
        print("❌ 오류:", e)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, 1883, 60)
    client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

fig, ax = plt.subplots(figsize=(12, 6))
line_A, = ax.plot([], [], label="Publisher A", color='blue')
line_B, = ax.plot([], [], label="Publisher B", color='red')
ax.set_xlabel("Time (s)")
ax.set_ylabel("Amplitude")
ax.set_title("Real-Time Mean FFT Amplitude (10s)")
ax.legend()
ax.grid(True)

def update(frame):
    now = time.time() - start_time

    for source, queue in data_queues.items():
        if not queue.empty():
            data = detrend(queue.get())
            fft_result = np.fft.rfft(data) / len(data)
            amps = np.abs(fft_result)
            mean_amp = np.mean(amps)
            timestamps[source].append(now)
            amplitudes[source].append(mean_amp)

            # 최근 10초 이내로 자르기
            while timestamps[source] and timestamps[source][0] < now - 10:
                timestamps[source].pop(0)
                amplitudes[source].pop(0)

    # 선 업데이트
    line_A.set_data(timestamps["A"], amplitudes["A"])
    line_B.set_data(timestamps["B"], amplitudes["B"])

    # x축, y축 범위 설정
    ax.set_xlim(now - 10, now)
    all_amplitudes = amplitudes["A"] + amplitudes["B"]
    ax.set_ylim(0, max(all_amplitudes) * 1.2 if all_amplitudes else 1)

    return line_A, line_B

ani = animation.FuncAnimation(fig, update, interval=500, blit=False)
plt.tight_layout()
plt.show()
