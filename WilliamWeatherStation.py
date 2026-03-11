import tkinter as tk
import pyttsx3
import threading
import time
import board
import busio
import glob
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_pms5003 import PMS5003


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WeatherMaster Pro - Universal Edition")
        self.root.geometry("550x850")

        # --- STATE & ACCESSIBILITY ---
        self.is_speaking = False
        self.speech_enabled = tk.BooleanVar(value=False)
        self.high_contrast = False
        self.large_font = False
        self.data = {"temp_bme": "0", "hum": "0", "pres": "0", "pm25": "0", "temp_ds": "0"}

        # --- THEMES ---
        self.themes = {
            "standard": {"bg": "#283592", "pill": "#fecd08", "text_main": "black", "text_label": "#546e7a",
                         "header": "white"},
            "contrast": {"bg": "black", "pill": "white", "text_main": "black", "text_label": "#333333",
                         "header": "yellow"}
        }
        self.current_theme = self.themes["standard"]

        # --- HARDWARE INIT ---
        self.init_hardware()

        # --- UI LAYOUT ---
        self.main_frame = tk.Frame(self.root, bg=self.current_theme["bg"])
        self.main_frame.pack(fill="both", expand=True)

        self.setup_header()

        # Container for pills to allow easy re-drawing for Zoom
        self.rows_container = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        self.rows_container.pack()

        self.canvas_items = {}
        self.build_data_rows()
        self.build_status_indicators()

        # Footer Button
        self.speak_btn = tk.Button(self.main_frame, text="🔊 READ ALOUD (SPACE)",
                                   command=self.read_aloud_threaded, bg="#0e8140", fg="white",
                                   font=("Arial", 12, "bold"), height=2)
        self.speak_btn.pack(pady=20, fill="x", padx=50)

        # Keyboard Bindings
        self.root.bind('<space>', lambda e: self.read_aloud_threaded())
        self.root.bind('v', lambda e: self.speech_enabled.set(not self.speech_enabled.get()))
        self.root.bind('c', lambda e: self.toggle_theme())
        self.root.bind('+', lambda e: self.toggle_font_size())

        self.update_loop()

    def init_hardware(self):
        # I2C Setup for BME280
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.bme = adafruit_bme280.Adafruit_BME280_I2C(self.i2c, address=0x76)
            self.bme_status = True
        except:
            self.bme_status = False

        # UART Setup for PMS5003
        try:
            uart = busio.UART(board.TX, board.RX, baudrate=9600)
            self.pms = PMS5003(uart)
            self.pms_status = True
        except:
            self.pms_status = False

        # DS18B20 Setup
        try:
            base_dir = '/sys/bus/w1/devices/'
            device_folder = glob.glob(base_dir + '28*')[0]
            self.ds_path = device_folder + '/w1_slave'
            self.ds_status = True
        except:
            self.ds_status = False

    def setup_header(self):
        self.header = tk.Label(self.main_frame, text="WEATHER STATION", font=("Arial", 22, "bold"),
                               fg=self.current_theme["header"], bg=self.current_theme["bg"])
        self.header.pack(pady=(20, 0))

        self.clock_label = tk.Label(self.main_frame, text="00:00:00", font=("Arial", 14),
                                    fg="#0e8140", bg=self.current_theme["bg"])
        self.clock_label.pack()

        # Controls
        ctrl_f = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        ctrl_f.pack(pady=5)
        tk.Checkbutton(ctrl_f, text="Voice (V)", variable=self.speech_enabled,
                       bg=self.current_theme["bg"], fg="white", selectcolor="#0e8140").pack(side="left", padx=10)
        tk.Button(ctrl_f, text="Contrast (C)", command=self.toggle_theme).pack(side="left", padx=5)
        tk.Button(ctrl_f, text="Zoom (+)", command=self.toggle_font_size).pack(side="left", padx=5)

    def read_ds18b20(self):
        if not self.ds_status: return 0.0
        try:
            with open(self.ds_path, 'r') as f:
                lines = f.readlines()
            if "YES" in lines[0]:
                temp_string = lines[1][lines[1].find('t=') + 2:]
                return round(float(temp_string) / 1000.0, 1)
        except:
            return 0.0

    def update_loop(self):
        self.clock_label.config(text=time.strftime("%H:%M:%S"))

        # 1. BME Reading
        try:
            t_bme = round(self.bme.temperature, 1) if self.bme_status else 0.0
            hum = round(self.bme.relative_humidity, 1) if self.bme_status else 0.0
            pres = int(self.bme.pressure) if self.bme_status else 0
            self.update_dot("BME", self.bme_status)
        except:
            self.update_dot("BME", False); t_bme, hum, pres = 0.0, 0.0, 0

        # 2. PMS Reading
        try:
            pm = self.pms.read().pm25_standard if self.pms_status else 0
            self.update_dot("PMS", self.pms_status)
        except:
            self.update_dot("PMS", False); pm = 0

        # 3. DS Reading
        t_ds = self.read_ds18b20()
        self.update_dot("DS", self.ds_status and t_ds != 0.0)

        # Store string versions for voice
        self.data = {
            "temp_bme": f"{t_bme} degrees", "hum": f"{hum} percent",
            "pres": f"{pres} hectopascals", "pm25": f"{pm} micrograms", "temp_ds": f"{t_ds} degrees"
        }

        # Update GUI Texts
        updates = [("temp_bme", f"🌡️ {t_bme} °C"), ("hum", f"💧 {hum} %"), ("pres", f"⏲️ {pres} hPa"),
                   ("pm25", f"💨 {pm} µg/m³"), ("temp_ds", f"🧪 {t_ds} °C")]

        for key, text in updates:
            canvas_obj, text_id = self.canvas_items[key]
            color = "red" if key == "pm25" and pm > 35 else self.current_theme["text_main"]
            canvas_obj.itemconfig(text_id, text=text, fill=color)

        self.root.after(2000, self.update_loop)

    def update_dot(self, sensor, active):
        color = "#0e8140" if active else "red"
        self.status_canvases[sensor].itemconfig(self.status_dots[sensor], fill=color)

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, color):
        points = [x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2,
                  y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2, x1 + radius,
                  y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1,
                  y1]
        return canvas.create_polygon(points, fill=color, smooth=True)

    def build_data_rows(self):
        for w in self.rows_container.winfo_children(): w.destroy()
        metrics = [("temp_bme", "BME280 Temp"), ("hum", "Humidity"), ("pres", "Pressure"), ("pm25", "Dust (PM2.5)"),
                   ("temp_ds", "Probe Temp")]
        f_size = 18 if self.large_font else 14
        h = 80 if self.large_font else 60
        for key, label in metrics:
            c = tk.Canvas(self.rows_container, width=450, height=h, bg=self.current_theme["bg"], highlightthickness=0)
            c.pack(pady=5)
            self.draw_rounded_rect(c, 5, 5, 445, h - 5, 25, self.current_theme["pill"])
            c.create_text(25, h / 2, text=label, anchor="w", fill=self.current_theme["text_label"],
                          font=("Arial", int(f_size * 0.8), "bold"))
            val_id = c.create_text(425, h / 2, text="--", anchor="e", fill=self.current_theme["text_main"],
                                   font=("Arial", f_size, "bold"))
            self.canvas_items[key] = (c, val_id)

    def build_status_indicators(self):
        f = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        f.pack(pady=10)
        self.status_canvases, self.status_dots = {}, {}
        for s in ["BME", "PMS", "DS"]:
            sub = tk.Frame(f, bg=self.current_theme["bg"])
            sub.pack(side="left", padx=20)
            c = tk.Canvas(sub, width=20, height=20, bg=self.current_theme["bg"], highlightthickness=0)
            c.pack()
            dot = c.create_oval(2, 2, 18, 18, fill="red")
            self.status_canvases[s], self.status_dots[s] = c, dot
            tk.Label(sub, text=s, font=("Arial", 8), fg="white", bg=self.current_theme["bg"]).pack()

    def toggle_theme(self):
        self.high_contrast = not self.high_contrast
        self.current_theme = self.themes["contrast"] if self.high_contrast else self.themes["standard"]
        self.main_frame.configure(bg=self.current_theme["bg"])
        self.rows_container.configure(bg=self.current_theme["bg"])
        self.header.configure(fg=self.current_theme["header"], bg=self.current_theme["bg"])
        self.build_data_rows()

    def toggle_font_size(self):
        self.large_font = not self.large_font
        self.build_data_rows()

    def read_aloud_threaded(self):
        if self.speech_enabled.get() and not self.is_speaking:
            threading.Thread(target=self.speak_logic, daemon=True).start()

    def speak_logic(self):
        self.is_speaking = True
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 155)
            rep = f"Weather Update. BME Temp {self.data['temp_bme']}. Humidity {self.data['hum']}. Pressure {self.data['pres']}. Dust level {self.data['pm25']}. Probe {self.data['temp_ds']}."
            engine.say(rep);
            engine.runAndWait();
            engine.stop()
        except:
            pass
        finally:
            self.is_speaking = False


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()