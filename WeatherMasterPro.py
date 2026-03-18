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
        self.root.title("WeatherMaster Custom Pro")
        self.root.geometry("700x900")
        
        # Colors from your request
        self.color_bg = "#2c3592"
        self.color_text = "#a3a3a3"
        self.color_box = "#108340"
        self.color_line1 = "#ffcf11" # Yellow
        self.color_line2 = "#108340" # Green

        # Data State - 20 points for faster-looking movement
        self.history = {"temp": [0]*20, "dust": [0]*20, "probe": [0]*20}
        self.display_labels = {}

        self.init_hardware()
        self.setup_gui()
        self.update_loop()

    def init_hardware(self):
        try:
            self.bus = smbus2.SMBus(1)
            self.address = 0x77
            self.calib = bme280.load_calibration_params(self.bus, self.address)
            self.bme_enabled = True
        except:
            self.bme_enabled = False
        
        try: self.pms = PMS5003(device='/dev/serial0', baudrate=9600)
        except: self.pms = None
            
        try: self.probe = W1ThermSensor()
        except: self.probe = None

    def setup_gui(self):
        self.main_frame = tk.Frame(self.root, bg=self.color_bg)
        self.main_frame.pack(expand=True, fill="both")

        # Title
        tk.Label(self.main_frame, text="WEATHER STATION", font=("Arial", 24, "bold"), 
                 bg=self.color_bg, fg=self.color_text).pack(pady=10)

        # Data Boxes (Rectangles)
        self.data_container = tk.Frame(self.main_frame, bg=self.color_bg)
        self.data_container.pack(fill="x", padx=20)

        items = [("BME Temp", "°C"), ("Dust (PM2.5)", "µg/m³"), ("Probe Temp", "°C")]
        for name, unit in items:
            # We use highlightthickness to simulate a border/rounded look in standard Tkinter
            f = tk.Frame(self.data_container, bg=self.color_box, bd=0, padx=10, pady=10)
            f.pack(pady=8, fill="x")
            lbl = tk.Label(f, text=f"{name}: -- {unit}", font=("Arial", 18, "bold"), 
                           bg=self.color_box, fg=self.color_text)
            lbl.pack()
            self.display_labels[name] = lbl

        # --- THE LIVE GRAPH ---
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5, 4), facecolor=self.color_bg)
        self.fig.tight_layout(pad=3.0)
        
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor(self.color_bg)
            ax.tick_params(colors=self.color_text, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(self.color_text)

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
            except: pass

        # 2. Read Dust
        if self.pms:
            try:
                d = self.pms.read().pm25_standard
                self.history["dust"].append(d)
                self.display_labels["Dust (PM2.5)"].config(text=f"Dust: {d} µg/m³")
            except: pass

        # 3. Read Probe
        if self.probe:
            try:
                pt = round(self.probe.get_temperature(), 1)
                self.history["probe"].append(pt)
                self.display_labels["Probe Temp"].config(text=f"Probe: {pt}°C")
            except: pass

        # Maintain 20 points for faster visual flow
        for k in self.history:
            if len(self.history[k]) > 20: self.history[k].pop(0)

        # --- REFRESH GRAPH WITH CUSTOM LINE COLORS ---
        self.ax1.clear()
        self.ax1.set_title("Temperature History", color=self.color_text)
        self.ax1.plot(self.history["temp"], color=self.color_line1, label="BME", linewidth=2)
        self.ax1.plot(self.history["probe"], color=self.color_line2, label="Probe", linewidth=2)
        self.ax1.legend(facecolor=self.color_bg, labelcolor=self.color_text, fontsize='x-small')
        
        self.ax2.clear()
        self.ax2.set_title("Dust Levels", color=self.color_text)
        self.ax2.plot(self.history["dust"], color=self.color_line1, linewidth=2)
        
        self.canvas.draw()

        # SPEED: Updated to 1000ms (1 second)
        self.root.after(1000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
