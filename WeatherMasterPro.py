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
        self.root.geometry("700x980")
        
        # --- Custom Color Palette ---
        self.color_bg = "#2c3592"
        self.color_text = "#a3a3a3"
        self.color_box = "#108340"
        self.color_pulse = "#1db954" # A lighter green for the flash
        self.color_line1 = "#ffcf11"
        self.color_line2 = "#108340"
        
        self.high_contrast = False
        self.font_size_large = False
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
        except: self.bme_enabled = False
        try: self.pms = PMS5003(device='/dev/serial0', baudrate=9600)
        except: self.pms = None
        try: self.probe = W1ThermSensor()
        except: self.probe = None

    def setup_gui(self):
        self.main_frame = tk.Frame(self.root, bg=self.color_bg)
        self.main_frame.pack(expand=True, fill="both")
        self.draw_interface()

    def draw_interface(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        current_bg = "#000000" if self.high_contrast else self.color_bg
        current_txt = "#ffffff" if self.high_contrast else self.color_text
        current_box = "#ffffff" if self.high_contrast else self.color_box
        box_txt_color = "#000000" if self.high_contrast else self.color_text
        font_size = 26 if self.font_size_large else 16

        tk.Label(self.main_frame, text="WEATHER STATION", font=("Arial", 22, "bold"), 
                 bg=current_bg, fg=current_txt).pack(pady=5)

        btn_frame = tk.Frame(self.main_frame, bg=current_bg)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="CONTRAST", font=("Arial", 10, "bold"), 
                  command=self.toggle_contrast, width=10).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="ZOOM +/-", font=("Arial", 10, "bold"), 
                  command=self.toggle_zoom, width=10).grid(row=0, column=1, padx=5)

        self.data_container = tk.Frame(self.main_frame, bg=current_bg)
        self.data_container.pack(fill="x", padx=20)

        items = [("BME Temp", "°C"), ("Humidity", "%"), ("Pressure", "hPa"),
                 ("Dust (PM2.5)", "µg/m³"), ("Probe Temp", "°C")]

        for name, unit in items:
            f = tk.Frame(self.data_container, bg=current_box, padx=5, pady=5)
            f.pack(pady=3, fill="x")
            lbl = tk.Label(f, text=f"{name}: -- {unit}", font=("Arial", font_size, "bold"), 
                           bg=current_box, fg=box_txt_color)
            lbl.pack()
            self.display_labels[name] = {"label": lbl, "frame": f}

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5, 3.5), facecolor=current_bg)
        self.fig.tight_layout(pad=2.5)
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor(current_bg)
            ax.tick_params(colors=current_txt, labelsize=7)
            for spine in ax.spines.values():
                spine.set_color(current_txt)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(pady=5, fill="both", expand=True)

    def pulse_effect(self, name):
        """Flashes the box color to show a data update"""
        if self.high_contrast: return # Skip pulse in high contrast for accessibility
        
        target_frame = self.display_labels[name]["frame"]
        target_label = self.display_labels[name]["label"]
        
        # Flash to lighter green
        target_frame.config(bg=self.color_pulse)
        target_label.config(bg=self.color_pulse)
        
        # Revert back after 100ms
        self.root.after(100, lambda: target_frame.config(bg=self.color_box))
        self.root.after(100, lambda: target_label.config(bg=self.color_box))

    def toggle_contrast(self):
        self.high_contrast = not self.high_contrast
        self.draw_interface()

    def toggle_zoom(self):
        self.font_size_large = not self.font_size_large
        self.draw_interface()

    def update_loop(self):
        if self.bme_enabled:
            try:
                data = bme280.sample(self.bus, self.address, self.calib)
                t, h, p = round(data.temperature, 1), round(data.humidity, 1), int(data.pressure)
                self.history["temp"].append(t)
                self.display_labels["BME Temp"]["label"].config(text=f"BME Temp: {t}°C")
                self.display_labels["Humidity"]["label"].config(text=f"Humidity: {h}%")
                self.display_labels["Pressure"]["label"].config(text=f"Pressure: {p} hPa")
                self.pulse_effect("BME Temp")
            except: pass

        if self.pms:
            try:
                d = self.pms.read().pm25_standard
                self.history["dust"].append(d)
                self.display_labels["Dust (PM2.5)"]["label"].config(text=f"Dust: {d} µg/m³")
                self.pulse_effect("Dust (PM2.5)")
            except: pass

        if self.probe:
            try:
                pt = round(self.probe.get_temperature(), 1)
                self.history["probe"].append(pt)
                self.display_labels["Probe Temp"]["label"].config(text=f"Probe: {pt}°C")
                self.pulse_effect("Probe Temp")
            except: pass

        for k in self.history:
            if len(self.history[k]) > 20: self.history[k].pop(0)

        self.ax1.clear()
        self.ax1.set_title("Temperature History", color=self.color_text if not self.high_contrast else "white", fontsize=9)
        self.ax1.plot(self.history["temp"], color=self.color_line1, linewidth=2, label="BME")
        self.ax1.plot(self.history["probe"], color=self.color_line2, linewidth=2, label="Probe")
        self.ax2.clear()
        self.ax2.set_title("Dust History", color=self.color_text if not self.high_contrast else "white", fontsize=9)
        self.ax2.plot(self.history["dust"], color=self.color_line1, linewidth=2)
        self.canvas.draw()
        
        self.root.after(1000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
