import tkinter as tk
from tkinter import ttk
import smbus2
import bme280
from pms5003 import PMS5003
from w1thermsensor import W1ThermSensor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WeatherMaster Pro - Live Graph Edition")
        self.root.geometry("700x900")
        
        # --- Settings & Data ---
        self.high_contrast = False
        self.font_size_large = False
        # Fill with 30 zeros so the graph starts immediately
        self.history = {"temp": [0]*30, "dust": [0]*30, "probe": [0]*30}
        self.display_labels = {}

        self.init_hardware()
        self.setup_gui()
        self.update_loop()

    def init_hardware(self):
        # BME280 (Standard Module - Address 0x77)
        try:
            self.bus = smbus2.SMBus(1)
            self.address = 0x77
            self.calib = bme280.load_calibration_params(self.bus, self.address)
            self.bme_enabled = True
        except:
            self.bme_enabled = False
            print("BME280: Not Found")

        # PMS5003
        try:
            self.pms = PMS5003(device='/dev/serial0', baudrate=9600)
        except:
            self.pms = None

        # DS18B20
        try:
            self.probe = W1ThermSensor()
        except:
            self.probe = None

    def setup_gui(self):
        self.main_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.main_frame.pack(expand=True, fill="both")

        # Title
        tk.Label(self.main_frame, text="LIVE WEATHER STATION", font=("Arial", 24, "bold"), 
                 bg="#1a1a2e", fg="white").pack(pady=10)

        # Data Boxes
        self.data_container = tk.Frame(self.main_frame, bg="#1a1a2e")
        self.data_container.pack(fill="x", padx=20)

        items = [("BME Temp", "°C"), ("Dust (PM2.5)", "µg/m³"), ("Probe Temp", "°C")]
        for name, unit in items:
            f = tk.Frame(self.data_container, bg="#f1c40f", bd=2)
            f.pack(pady=5, fill="x")
            lbl = tk.Label(f, text=f"{name}: -- {unit}", font=("Arial", 16, "bold"), bg="#f1c40f")
            lbl.pack(pady=10)
            self.display_labels[name] = lbl

        # --- THE LIVE GRAPH ---
        # Creating the figure and the axes (subplots)
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5, 4), facecolor='#1a1a2e')
        self.fig.tight_layout(pad=3.0)
        
        # Style the graphs
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor('#1a1a2e')
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('white')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

    def update_loop(self):
        # 1. Read BME
        if self.bme_enabled:
            try:
                data = bme280.sample(self.bus, self.address, self.calib)
                t = round(data.temperature, 1)
                self.history["temp"].append(t)
                self.display_labels["BME Temp"].config(text=f"BME Temp: {t}°C")
                # Health Alert Color
                bg = "#2ecc71" if 18 <= t <= 26 else "#e74c3c"
                self.display_labels["BME Temp"].master.config(bg=bg)
                self.display_labels["BME Temp"].config(bg=bg)
            except: pass

        # 2. Read Dust
        if self.pms:
            try:
                d = self.pms.read().pm25_standard
                self.history["dust"].append(d)
                self.display_labels["Dust (PM2.5)"].config(text=f"Dust: {d} µg/m³")
                bg = "#2ecc71" if d <= 12 else "#f1c40f" if d <= 35 else "#e74c3c"
                self.display_labels["Dust (PM2.5)"].master.config(bg=bg)
                self.display_labels["Dust (PM2.5)"].config(bg=bg)
            except: pass

        # 3. Read Probe
        if self.probe:
            try:
                pt = round(self.probe.get_temperature(), 1)
                self.history["probe"].append(pt)
                self.display_labels["Probe Temp"].config(text=f"Probe: {pt}°C")
            except: pass

        # Maintain list length
        for k in self.history:
            if len(self.history[k]) > 30: self.history[k].pop(0)

        # --- REFRESH THE GRAPH ---
        self.ax1.clear()
        self.ax1.set_title("Temperature (°C)", color="white", fontsize=10)
        self.ax1.plot(self.history["temp"], color="#e74c3c", label="BME")
        self.ax1.plot(self.history["probe"], color="#3498db", label="Probe")
        
        self.ax2.clear()
        self.ax2.set_title("Dust (µg/m³)", color="white", fontsize=10)
        self.ax2.plot(self.history["dust"], color="#2ecc71")
        
        self.canvas.draw()

        self.root.after(3000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
