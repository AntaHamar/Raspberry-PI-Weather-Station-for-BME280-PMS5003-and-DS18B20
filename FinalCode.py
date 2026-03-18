import tkinter as tk
from tkinter import ttk
import board
import busio
import adafruit_bme280
from pms5003 import PMS5003, ReadTimeoutError
import glob
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class WeatherStation:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi Weather Master")
        self.root.geometry("600x600")
        
        # Data History for Plotting
        self.temp_history = []
        
        self.setup_hardware()
        self.setup_gui()
        self.update_loop()

    def setup_hardware(self):
        # 1. BME280 Setup (I2C)
        try:
            i2c = board.I2C()
            self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
        except Exception as e:
            print(f"BME280 Not Found: {e}")
            self.bme280 = None

        # 2. PMS5003 Setup (Serial)
        try:
            self.pms = PMS5003(device='/dev/serial0', baudrate=9600)
            self.pms_active = True
        except Exception as e:
            print(f"PMS5003 Not Found: {e}")
            self.pms_active = False

    def get_probe_temp(self):
        # 3. DS18B20 Setup (1-Wire)
        try:
            base_dir = '/sys/bus/w1/devices/'
            device_folder = glob.glob(base_dir + '28*')[0]
            device_file = device_folder + '/w1_slave'
            with open(device_file, 'r') as f:
                lines = f.readlines()
            if 'YES' in lines[0]:
                output = lines[1].find('t=')
                return float(lines[1][output+2:]) / 1000.0
        except:
            return None

    def setup_gui(self):
        # Text Displays
        self.title_label = tk.Label(self.root, text="LIVE SENSOR DATA", font=("Arial", 18, "bold"))
        self.title_label.pack(pady=10)

        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(pady=10)

        self.bme_label = tk.Label(self.info_frame, text="BME Temp: --", font=("Arial", 14))
        self.bme_label.grid(row=0, column=0, padx=20)

        self.dust_label = tk.Label(self.info_frame, text="PM2.5: --", font=("Arial", 14))
        self.dust_label.grid(row=0, column=1, padx=20)

        self.probe_label = tk.Label(self.info_frame, text="Probe: --", font=("Arial", 14))
        self.probe_label.grid(row=1, column=0, columnspan=2, pady=10)

        # Matplotlib Graph Setup
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.line, = self.ax.plot([], [], color='red', marker='o')
        self.ax.set_title("Temperature History (Last 20 readings)")
        self.ax.set_ylabel("Celsius")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_loop(self):
        current_temp = 0
        
        # Read BME280
        if self.bme280:
            current_temp = self.bme280.temperature
            self.bme_label.config(text=f"BME Temp: {current_temp:.1f}°C")
            
            # Update Graph Data
            self.temp_history.append(current_temp)
            if len(self.temp_history) > 20: self.temp_history.pop(0)
            
            self.line.set_data(range(len(self.temp_history)), self.temp_history)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

        # Read PMS5003
        if self.pms_active:
            try:
                data = self.pms.read()
                self.dust_label.config(text=f"PM2.5: {data.pm_ug_per_m3(2.5)} µg/m³")
            except ReadTimeoutError:
                self.dust_label.config(text="PM2.5: Waiting...")

        # Read Probe
        p_temp = self.get_probe_temp()
        if p_temp:
            self.probe_label.config(text=f"Probe Temp: {p_temp:.1f}°C")

        # Refresh every 3 seconds
        self.root.after(3000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherStation(root)
    root.mainloop()
