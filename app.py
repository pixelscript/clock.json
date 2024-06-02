import app
from requests import get
from system.eventbus import eventbus
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES
import utime
import ntptime
from system.patterndisplay.events import *
from tildagonos import tildagonos
from power import BatteryLevel
import imu
IPIFY_URL = "https://api.ipify.org"

class ClockJSON(app.App):
    def __init__(self):
        self.button_states = Buttons(self)
        eventbus.emit(PatternDisable())
        self.set_leds_black()
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.day = 0
        self.month = 0
        self.year = 0
        self.weekday = ""
        self.ip = False
        self.acc = None
        
    def set_leds_black(self):
        for i in range(1, 13):
            tildagonos.leds[i] = (0, 0, 0)
        tildagonos.leds.write()
    
    def get_ip(self):
        try:
            self.response = get(IPIFY_URL)
            self.ip = self.response.text
        except:
            return
        
    def set_time(self):
        try:
            ntptime.settime()
        except Exception as e:
            pass
        current_time_utc = utime.time()
        current_time = utime.localtime( current_time_utc + 3600)
        self.year = current_time[0]
        self.month = current_time[1]
        self.day = current_time[2]
        self.hours = current_time[3]
        self.minutes = current_time[4]
        self.seconds = current_time[5]
        self.weekday = current_time[6]
        self.last_update_time = utime.time()
        
    def time_is_set(self):
        return self.year > 2000

    def update(self, dt):
        self.set_leds_black()
        self.set_time()
        self.acc = imu.acc_read()
        if not self.ip:
            self.get_ip()
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()

    def draw(self, ctx):
        ctx.save()
        clear_background(ctx)
        formatted_date, formatted_time = self.format_time()
        self.draw_clock(ctx, formatted_date, formatted_time, self.ip, self.acc[0], self.acc[1], self.acc[2])
        ctx.restore()
    
    def format_time(self):
        if self.time_is_set():
            # Custom formatting of time
            day_suffix = lambda d: 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')
            weekdays = ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat", "Sun"]
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
            formatted_date = f'{weekdays[self.weekday]}, {self.day}{day_suffix(self.day)} {months[self.month - 1]}'
            formatted_time = f'{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}'
            return formatted_date, formatted_time
        return ["fetching...", "fetching..."]

    
    def draw_clock(self, ctx, date_str, time_str, ip, x, y, z):
        power = f"{(BatteryLevel() / 106.25) * 100:.0f} %"
        clear_background(ctx)
        ctx.save()
        
        # Drawing the backgrounds
        ctx.rgb(0.11, 0.11, 0.11)
        ctx.rectangle(-120, -120, 240, 240).fill()
        
        # Drawing the top bar
        ctx.font_size = 16
        ctx.rgb(0.15, 0.15, 0.15)
        ctx.rectangle(35, -120, 200, 50).fill()
        ctx.rgb(0, 0, 0)
        ctx.rectangle(-120, -120, 240, 20).fill()
        ctx.rgb(1, 1, 1)
        ctx.move_to(-80, -80)
        ctx.text("clockface.json  x")
    
        # Drawing line numbers
        ctx.rgb(0.5, 0.5, 0.5)
        ctx.font_size = 14
        for i in range(0, 14):
            ctx.move_to(-95, (i * 20) - 60)
            ctx.text(str(i+1))

        json_data = '''
{{
  "date": "{}",
  "time": "{}",
  "battery": "{}",
  "ip": "{}",
  "acc": {{
    "x": "{}",
    "y": "{}",
    "z": "{}"
  }}
}}
'''.format(date_str, time_str, power, ip, x, y, z)

        # Drawing the JSON data with syntax highlighting

        lines = json_data.strip().split('\n')
        colors = {
            'key': (0.61, 0.86, 0.99),
            'string': (0.80, 0.56, 0.47),
            'bracket': (0.8, 0.8, 0.8),
        }

        y_position = -60
        for line in lines:
            x_position = -80
            char_count = 0
            for char in line:
                if char in '{}[]:':
                    ctx.rgb(*colors['bracket'])
                elif char == '"':
                    char_count += 1
                    if char_count <= 2:
                        ctx.rgb(*colors['key'])
                    else:
                        ctx.rgb(*colors['string'])
                else:
                    if char_count <= 2:
                        ctx.rgb(*colors['key'])
                    else:
                        ctx.rgb(*colors['string'])
                ctx.move_to(x_position, y_position)
                ctx.text(char)
                x_position += 7
            y_position += 20
        
        ctx.restore()

__app_export__ = ClockJSON
