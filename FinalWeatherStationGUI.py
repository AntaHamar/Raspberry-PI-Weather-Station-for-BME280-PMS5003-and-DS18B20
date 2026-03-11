import tkinter as tk
import pyttsx3
import threading
import random
import time


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("William's Weather Station Accessibility Project")
        self.root.geometry("550x850")

        # --- STATE VARIABLES ---
        self.is_speaking = False
        self.speech_enabled = tk.BooleanVar(value=False)
        self.high_contrast = False
        self.large_font = False
        self.data = {"temp_bme": "0", "hum": "0", "pres": "0", "pm25": "0", "temp_ds": "0"}
        self.canvas_items = {}
        self.status_dots = {}
        self.status_canvases = {}

        # --- THEMES ---
        self.themes = {
            "standard": {"bg": "#283592", "pill": "#fecd08", "text_main": "black", "text_label": "#546e7a",
                         "header": "white"},
            "contrast": {"bg": "black", "pill": "white", "text_main": "black", "text_label": "#333333",
                         "header": "yellow"}
        }
        self.current_theme = self.themes["standard"]

        # --- KEYBOARD BINDINGS ---
        self.root.bind('<space>', lambda e: self.read_aloud_threaded())
        self.root.bind('v', lambda e: self.speech_enabled.set(not self.speech_enabled.get()))
        self.root.bind('c', lambda e: self.toggle_theme())
        self.root.bind('+', lambda e: self.toggle_font_size())

        # --- UI SETUP ---
        self.main_frame = tk.Frame(self.root, bg=self.current_theme["bg"])
        self.main_frame.pack(fill="both", expand=True)

        self.header = tk.Label(self.main_frame, text="WEATHER STATION", font=("Arial", 22, "bold"),
                               fg=self.current_theme["header"], bg=self.current_theme["bg"])
        self.header.pack(pady=(20, 0))

        self.clock_label = tk.Label(self.main_frame, text="00:00:00", font=("Arial", 14),
                                    fg="#0e8140", bg=self.current_theme["bg"])
        self.clock_label.pack()

        # Accessibility Toolbar
        tool_frame = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        tool_frame.pack(pady=10)

        tk.Checkbutton(tool_frame, text="Voice (V)", variable=self.speech_enabled,
                       bg=self.current_theme["bg"], fg="white", selectcolor="#0e8140",
                       activebackground=self.current_theme["bg"]).pack(side="left", padx=5)

        tk.Button(tool_frame, text="Contrast (C)", command=self.toggle_theme, width=10).pack(side="left", padx=5)
        tk.Button(tool_frame, text="Zoom (+)", command=self.toggle_font_size, width=10).pack(side="left", padx=5)

        self.rows_container = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        self.rows_container.pack()

        self.build_data_rows()
        self.build_status_lights()

        self.speak_btn = tk.Button(self.main_frame, text="🔊 READ ALOUD (SPACE)",
                                   command=self.read_aloud_threaded, font=("Arial", 12, "bold"),
                                   bg="#0e8140", fg="white", height=2)
        self.speak_btn.pack(pady=20, fill="x", padx=50)

        self.update_loop()

    def build_data_rows(self):
        for widget in self.rows_container.winfo_children():
            widget.destroy()

        metrics = [("temp_bme", "BME280 Temp"), ("hum", "Humidity"), ("pres", "Pressure"),
                   ("pm25", "Dust (PM2.5)"), ("temp_ds", "Probe Temp")]

        f_size = 18 if self.large_font else 14
        h = 80 if self.large_font else 60

        for key, label_text in metrics:
            c = tk.Canvas(self.rows_container, width=450, height=h, bg=self.current_theme["bg"],
                          highlightthickness=0)
            c.pack(pady=5)
            self.draw_rounded_rect(c, 5, 5, 445, h - 5, 25, self.current_theme["pill"])

            c.create_text(25, h / 2, text=label_text, anchor="w",
                          fill=self.current_theme["text_label"], font=("Arial", int(f_size * 0.8), "bold"))

            val_id = c.create_text(425, h / 2, text="--", anchor="e",
                                   fill=self.current_theme["text_main"], font=("Arial", f_size, "bold"))
            self.canvas_items[key] = (c, val_id)

    def build_status_lights(self):
        status_frame = tk.Frame(self.main_frame, bg=self.current_theme["bg"])
        status_frame.pack(pady=10)
        for sensor in ["BME", "PMS", "DS"]:
            f = tk.Frame(status_frame, bg=self.current_theme["bg"])
            f.pack(side="left", padx=20)
            dot_canvas = tk.Canvas(f, width=20, height=20, bg=self.current_theme["bg"], highlightthickness=0)
            dot_canvas.pack()
            dot_id = dot_canvas.create_oval(2, 2, 18, 18, fill="red")
            self.status_canvases[sensor] = dot_canvas
            self.status_dots[sensor] = dot_id
            tk.Label(f, text=sensor, font=("Arial", 8), fg="white", bg=self.current_theme["bg"]).pack()

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, color):
        points = [x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2,
                  y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2, x1 + radius,
                  y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1,
                  y1]
        return canvas.create_polygon(points, fill=color, smooth=True)

    def toggle_theme(self):
        self.high_contrast = not self.high_contrast
        self.current_theme = self.themes["contrast"] if self.high_contrast else self.themes["standard"]
        self.refresh_ui()

    def toggle_font_size(self):
        self.large_font = not self.large_font
        self.refresh_ui()

    def refresh_ui(self):
        self.main_frame.configure(bg=self.current_theme["bg"])
        self.rows_container.configure(bg=self.current_theme["bg"])
        self.header.configure(fg=self.current_theme["header"], bg=self.current_theme["bg"])
        self.clock_label.configure(bg=self.current_theme["bg"])
        self.build_data_rows()

    def update_loop(self):
        self.clock_label.config(text=time.strftime("%H:%M:%S"))

        # Simulating data - ensure they are formatted as clean strings for the voice engine
        t_bme = round(random.uniform(15, 30), 1)
        hum = round(random.uniform(30, 80), 1)
        pres = random.randint(980, 1030)
        pm = random.randint(2, 60)
        t_ds = round(random.uniform(15, 28), 1)

        self.data = {
            "temp_bme": f"{t_bme} degrees Celsius",
            "hum": f"{hum} percent",
            "pres": f"{pres} hectopascals",
            "pm25": f"{pm} micrograms",
            "temp_ds": f"{t_ds} degrees Celsius"
        }

        # Update visual dots
        for s in self.status_dots:
            self.status_canvases[s].itemconfig(self.status_dots[s], fill="#0e8140")

        # Update UI text
        updates = [
            ("temp_bme", f"🌡️ {t_bme} °C", self.current_theme["text_main"]),
            ("hum", f"💧 {hum} %", self.current_theme["text_main"]),
            ("pres", f"⏲️ {pres} hPa", self.current_theme["text_main"]),
            ("pm25", f"💨 {pm} µg/m³", "red" if pm > 35 else self.current_theme["text_main"]),
            ("temp_ds", f"🧪 {t_ds} °C", self.current_theme["text_main"])
        ]

        for key, text, color in updates:
            if key in self.canvas_items:
                canvas_obj, text_id = self.canvas_items[key]
                canvas_obj.itemconfig(text_id, text=text, fill=color)

        self.root.after(1000, self.update_loop)

    def read_aloud_threaded(self):
        if self.speech_enabled.get() and not self.is_speaking:
            threading.Thread(target=self.speak_logic, daemon=True).start()

    def speak_logic(self):
        self.is_speaking = True
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 155)

            # Explicitly building the report string to ensure Pressure and Probe are included
            report = (
                f"Weather station update for {time.strftime('%H:%M')}. "
                f"B M E temperature is {self.data['temp_bme']}. "
                f"Humidity is {self.data['hum']}. "
                f"Atmospheric pressure is {self.data['pres']}. "
                f"Dust levels are {self.data['pm25']}. "
                f"And the probe temperature is {self.data['temp_ds']}."
            )

            engine.say(report)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"Speech error: {e}")
        finally:
            self.is_speaking = False


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()