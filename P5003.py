import time
from pms5003 import PMS5003, ReadTimeoutError

# Configure the sensor
# Using /dev/serial0 which is the default for Raspberry Pi TX/RX pins
pms5003 = PMS5003(
    device='/dev/serial0',
    baudrate=9600,
    pin_enable=22,
    pin_reset=27
)

print("--- PMS5003 Diagnostic Test ---")
print("Waiting for stable data flow... (Press Ctrl+C to stop)")
time.sleep(2) # Give the fan a second to reach full speed

try:
    while True:
        try:
            readings = pms5003.read()
            print("\n" + "="*30)
            print(f"PM 1.0 (ug/m3): {readings.pm_ug_per_m3(1.0)}")
            print(f"PM 2.5 (ug/m3): {readings.pm_ug_per_m3(2.5)}  <-- Main Sensor")
            print(f"PM 10  (ug/m3): {readings.pm_ug_per_m3(10)}")
            print("-" * 30)
            print(f"Raw 0.3um particles: {readings.pm_per_1l_air(0.3)}")
            print(f"Raw 0.5um particles: {readings.pm_per_1l_air(0.5)}")
            
            # This is how you check if it's REALLY working:
            if readings.pm_ug_per_m3(2.5) > 50:
                print("!!! SPIKE DETECTED !!!")
                
            time.sleep(1)

        except ReadTimeoutError:
            print("Search timed out. Check if wires are loose!")
            time.sleep(1)

except KeyboardInterrupt:
    print("\nTest stopped by user.")
