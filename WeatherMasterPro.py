import tkinter as tk
from tkinter import ttk
import smbus2
import bme280
from pms5003 import PMS5003
from w1thermsensor import W1ThermSensor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WeatherMaster Pro - BME280 Module Edition")
        self.root.geometry("600x850")
        
        # --- Accessibility & Data States ---
        self.high_contrast = False
        self.font_size_large = False
        self.history = {"temp": [], "dust": [], "probe": []}
        self.display_labels = {}

        self.init_hardware()
        self.setup_gui()
        self.update_loop()

    def init_hardware(self):
        """Initialize sensors using smbus2 and bme280 module"""
        # 1. BME280 (Standard Module)
        try:
            self.port = 1
            self.address = 0x77  # Your specific sensor address
            self.bus = smbus2.SMBus(self.port)
            self.calibration_params = bme280.load_calibration_params(self.bus, self.address)
            print("BME280: Connected via smbus2 (0x77)")
            self.bme_enabled = True
        except Exception as e:
            self.bme_enabled = False
            print(f"BME280: Not Found ({e})")

        # 2. PMS5003 (Dust Sensor)
        try:
            self.pms = PMS5003(device='/dev/serial0', baudrate=9600)
            print("PMS5003: Connected")
        except Exception as e:
            self.pms = None
            print(f"PMS5003: Not Found")

        # 3. DS18B20 (Probe)
        try:
            self.probe = W1ThermSensor()
            print("DS18B20: Connected")
        except Exception as e:
            self.probe = None
            print(f"DS18B20: Not Found")

    def setup_gui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill="both")
        self.apply_theme()

    def apply_theme(self):
        bg_col = "#000000" if self.high_contrast else "#1a1a2e"
        box_default = "#ffffff" if self.high_contrast else "#f1c40f"
        txt_col = "#000000" if self.high_contrast else "#1a1a2e"
        
        self.main_frame.configure(bg=bg_col)
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        tk.Label(self.main_frame, text="WEATHER STATION", font=("Arial", 28, "bold"), 
                 bg=bg_col, fg="white").pack(pady=20)

        ctrl_frame = tk.Frame(self.main_frame, bg=bg_col)
        ctrl_frame.pack(pady=10)
        tk.Button(ctrl_frame, text="CONTRAST (C)", command=self.toggle_contrast).grid(row=0, column=0, padx=10)
        tk.Button(ctrl_frame, text="ZOOM (+/-)", command=self.toggle_zoom).grid(row=0, column=1, padx=10)

        font_size = 26 if self.font_size_large else 18
        items = [("BME Temp", "°C"), ("Humidity", "%"), ("Pressure", "hPa"), 
                 ("Dust (PM2.5)", "µg/m³"), ("Probe Temp", "°C")]

        for name, unit in items:
            row_frame = tk.Frame(self.main_frame, bg=box_default)
            row_frame.pack(pady=8, fill="x", padx=40)
            lbl = tk.Label(row_frame, text=f"{name}: -- {unit}", font=("Arial", font_size, "bold"), 
                           bg=box_default, fg=txt_col)
            lbl.pack(pady=15)
            self.display_labels[name] = lbl

        tk.Button(self.main_frame, text="📊 VIEW LIVE GRAPHS", font=("Arial", 16, "bold"),
                  bg="#27ae60", fg="white", command=self.show_graphs).pack(pady=30, fill="x", padx=60)

    def toggle_contrast(self):
        self.high_contrast = not self.high_contrast
        self.apply_theme()

    def toggle_zoom(self):
        self.font_size_large = not self.font_size_large
        self.apply_theme()

 def show_graphs(self):
        """Pop-up window for data visualization with explicit drawing"""
        try:
            if not self.history["temp"]:
                print("No data collected yet to graph!")
                return

            graph_win = tk.Toplevel(self.root)
            graph_win.title("Live Sensor Trends")
            graph_win.geometry("600x600")
            graph_win.configure(bg="white")
            
            # Use a clean figure
            fig = plt.figure(figsize=(5, 6), dpi=100)
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            
            fig.tight_layout(pad=5.0)
            
            # Plot Temperature
            ax1.plot(self.history["temp"], color='red', marker='o', label='BME')
            ax1.plot(self.history["probe"], color='blue', marker='x', label='Probe')
            ax1.set_title("Temperature History (°C)")
            ax1.set_ylabel("Celsius")
            ax1.legend()
            ax1.grid(True)

            # Plot Dust
            ax2.plot(self.history["dust"], color='green', label='PM2.5')
            ax2.set_title("Dust Levels (µg/m³)")
            ax2.set_ylabel("micrograms")
            ax2.legend()
            ax2.grid(True)

            # Link the plot to the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=graph_win)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            
        except Exception as e:
            print(f"Graphing Error: {e}")
    def update_loop(self):
        # 1. BME280 Update (Non-Adafruit logic)
        if self.bme_enabled:
            try:
                data = bme280.sample(self.bus, self.address, self.calibration_params)
                t, h, p = round(data.temperature, 1), round(data.humidity, 1), int(data.pressure)
                
                t_color = "#2ecc71" if 18 <= t <= 25 else "#e74c3c"
                self.display_labels["BME Temp"].config(text=f"BME Temp: {t}°C")
                self.display_labels["BME Temp"].master.config(bg=t_color)
                self.display_labels["Humidity"].config(text=f"Humidity: {h}%")
                self.display_labels["Pressure"].config(text=f"Pressure: {p} hPa")
                self.history["temp"].append(t)
            except: pass

        # 2. PMS5003 Update
        if self.pms:
            try:
                d = self.pms.read().pm25_standard
                d_color = "#2ecc71" if d <= 12 else "#f1c40f" if d <= 35 else "#e74c3c"
                self.display_labels["Dust (PM2.5)"].config(text=f"Dust: {d} µg/m³")
                self.display_labels["Dust (PM2.5)"].master.config(bg=d_color)
                self.history["dust"].append(d)
            except: pass

        # 3. DS18B20 Update
        if self.probe:
            try:
                pt = round(self.probe.get_temperature(), 1)
                self.display_labels["Probe Temp"].config(text=f"Probe: {pt}°C")
                self.history["probe"].append(pt)
            except: pass

        for k in self.history:
            if len(self.history[k]) > 30: self.history[k].pop(0)

        self.root.after(3000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
