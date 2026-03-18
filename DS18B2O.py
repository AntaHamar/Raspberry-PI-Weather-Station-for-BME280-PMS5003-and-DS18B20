import time
from w1thermsensor import W1ThermSensor, SensorNotReadyError

try:
	sensor = W1ThermSensor()
	print(f"Found DS18B20 Sensor ID: {sensor.id}")
except Exception as e:
	print("Could not find DS18B20. Please check your wiring and resistor.")
	sensor = None
	
try:
	while sensor:
		try:
			temperature_in_c = sensor.get_temperature()
			print(f"Water/Probe Temp: {temperature_in_c:.2f} Degrees Celcuis")
			print("-" *25)
		except SensorNotReadyError:
			print("Sensor Busy...")
			
		time.sleep(2)
		
except KeyboardInterrupt:
	print("\nStopping DSB1820 monitor...")
