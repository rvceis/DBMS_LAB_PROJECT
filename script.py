import csv
import random
from datetime import datetime, timedelta

# Config
num_devices = 50          # number of sensors
rows_per_phase = 100      # rows per phase (scale up as needed)
start_time = datetime(2025, 12, 31, 9, 0, 0)

# Helper: generate timestamp
def ts(i):
    return (start_time + timedelta(seconds=i*5)).isoformat() + "Z"

# Phase 1: Flat schema
def generate_phase1(filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id","timestamp","temperature","humidity"])
        for i in range(rows_per_phase):
            device = f"sensor_{(i % num_devices)+1:03d}"
            writer.writerow([device, ts(i),
                             round(random.uniform(27.5,29.5),1),
                             random.randint(60,70)])

# Phase 2: Expanded schema
def generate_phase2(filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id","timestamp","temperature","humidity","air_quality_index","battery_level"])
        for i in range(rows_per_phase):
            device = f"sensor_{(i % num_devices)+1:03d}"
            writer.writerow([device, ts(i),
                             round(random.uniform(27.5,29.5),1),
                             random.randint(60,70),
                             random.randint(30,50),
                             random.randint(80,100)])

# Phase 3: Type mutation
def generate_phase3(filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id","timestamp","temperature_mode","humidity"])
        units = ["C","F","K"]
        for i in range(rows_per_phase):
            device = f"sensor_{(i % num_devices)+1:03d}"
            val = round(random.uniform(27.5,29.5),1)
            unit = random.choice(units)
            if unit=="C": temp = f"{val}_{unit}"
            elif unit=="F": temp = f"{round(val*9/5+32,1)}_{unit}"
            else: temp = f"{round(val+273.15,1)}_{unit}"
            writer.writerow([device, ts(i), temp, random.randint(60,70)])

# Phase 4: Batch mode
def generate_phase4(filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id","timestamp","temperature_readings","humidity_readings"])
        for i in range(rows_per_phase):
            device = f"sensor_{(i % num_devices)+1:03d}"
            temps = [round(random.uniform(27.5,29.5),1) for _ in range(3)]
            hums = [random.randint(60,70) for _ in range(3)]
            writer.writerow([device, ts(i),
                             "|".join(map(str,temps)),
                             "|".join(map(str,hums))])

# Phase 5: IoT + ML fusion
def generate_phase5(filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id","timestamp","temperature","humidity","prediction","confidence"])
        preds = ["normal","anomaly"]
        for i in range(rows_per_phase):
            device = f"sensor_{(i % num_devices)+1:03d}"
            pred = random.choice(preds)
            conf = round(random.uniform(0.1,0.99),2)
            writer.writerow([device, ts(i),
                             round(random.uniform(27.5,29.5),1),
                             random.randint(60,70),
                             pred, conf])

# Generate all phases
generate_phase1("phase1.csv")
generate_phase2("phase2.csv")
generate_phase3("phase3.csv")
generate_phase4("phase4.csv")
generate_phase5("phase5.csv")

print("Files generated: phase1.csv ... phase5.csv")
