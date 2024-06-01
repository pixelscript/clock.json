import app
import wifi
from requests import get
from system.eventbus import eventbus
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES
import time

IPIFY_URL = "https://api.ipify.org"
TIME_API_URL = "https://timeapi.io/api/Time/current/ip?ipAddress="

class ClockJSON(app.App):
    def __init__(self):
        self.button_states = Buttons(self)
        self.state = "init"
        self.ip = ""
        self.local_time = ""
        self.time_fetched = False
        self.hours = 0
        self.minutes = 0
        self.day = 0
        self.month = 0
        self.year = 0
        self.weekday = ""
        self.last_update_time = 0
        
    def check_wifi(self):
        self.update_state("checking_wifi")
        ssid = wifi.get_ssid()
        if not ssid:
            print("No WIFI config!")
            return False

        if not wifi.status():
            wifi.connect()
            while not wifi.status():
                print(f"Connecting to {ssid}...")

        if self.state != "checking_wifi":
            self.update_state("checking_wifi")
        connected = wifi.status()
        if not connected:
            self.update_state("no_wifi")
        return connected
    
    def get_ip(self):
        if not self.check_wifi():
            self.update_state("no_wifi")
        self.update_state("getting_ip")

    def background_update(self, delta):
        if self.state == "getting_ip":
            try:
                self.response = get(IPIFY_URL)
            except Exception:
                try:
                    self.response = get(IPIFY_URL)
                except Exception:
                    self.update_state("no_ip")
                    return
            self.update_state("ip_received")
        elif self.state == "fetching_time":
            try:
                time_response = get(TIME_API_URL + self.ip)
                time_data = time_response.json()
                self.local_time = time_data.get("time")
                self.hours, self.minutes = map(int, self.local_time.split(":"))
                self.day = time_data.get("day")
                self.month = time_data.get("month")
                self.year = time_data.get("year")
                self.weekday = time_data.get("dayOfWeek")
                self.update_state("time_fetched")
                self.last_update_time = time.time()
            except Exception:
                self.update_state("time_fetch_error")
    
    def update_state(self, state):
        print(f"State Transition: '{self.state}' -> '{state}'")
        self.state = state
        
    def handle_ip(self):
        if not self.response:
            return
        self.ip = self.response.text
        self.update_state("ip_ready")

    def update(self, delta):
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()
        if self.button_states.get(BUTTON_TYPES["CONFIRM"]):
            self.button_states.clear()
            print("Retrying!")
            self.update_state("init")

        if self.state == "init":
            print("calling get_ip")
            try:
                self.get_ip()
            except Exception as e:
                print(e)
                self.update_state("no_ip")
        elif self.state == "ip_received":
            self.handle_ip()
        elif self.state == "ip_ready":
            self.update_state("fetching_time")
        elif self.state == "no_ip":
            self.ip = "Can't access API\nC button to retry"
        elif self.state == "time_fetched" and not self.time_fetched:
            self.time_fetched = True
        elif self.state == "time_fetch_error":
            self.local_time = "Can't access API\nC button to retry"
            
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()

        # Update time based on the elapsed time since the last update
        if self.state == "time_fetched":
            current_time = time.time()
            elapsed_seconds = int(current_time - self.last_update_time)
            if elapsed_seconds >= 60:
                self.increment_time(elapsed_seconds // 60)
                self.last_update_time = current_time - (elapsed_seconds % 60)

    def draw(self, ctx):
        ctx.save()
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        clear_background(ctx)
        if self.state == 'init':
            ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(1, 0, 0).move_to(0, 0).text("Calling get_ip")
        elif self.state == 'ip_received':
            ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(1, 0, 0).move_to(0, 0).text("IP Received")
        elif self.state == 'ip_ready':
            ctx.rgb(0, 0.2, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(0, 1, 0).move_to(0, 0).text(self.ip)
        elif self.state == 'no_ip':
            ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(1, 0, 0).move_to(0, 0).text(self.ip)
        elif self.state == 'time_fetched':
            ctx.rgb(0, 0.2, 0).rectangle(-120, -120, 240, 240).fill()
            formatted_date, formatted_time = self.format_time()
            self.draw_clock(ctx, formatted_date, formatted_time, self.ip)
        elif self.state == 'time_fetch_error':
            ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(1, 0, 0).move_to(0, 0).text(self.local_time)
        
        ctx.restore()
    
    def format_time(self):
        if self.local_time:
            # Custom formatting of time
            day_suffix = lambda d: 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')
            weekdays = ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat", "Sun"]
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            formatted_date = f'{weekdays[self.get_weekday_index()]}, {self.day}{day_suffix(self.day)} {months[self.month - 1]}'
            formatted_time = f'{self.hours:02d}:{self.minutes:02d}'
            return formatted_date, formatted_time
        return "No time API"

    def increment_time(self, minutes_to_increment=1):
        self.minutes += minutes_to_increment
        while self.minutes >= 60:
            self.minutes -= 60
            self.hours += 1
            if self.hours >= 24:
                self.hours = 0
                self.increment_day()

    def increment_day(self):
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0):
            days_in_month[1] = 29
        self.day += 1
        if self.day > days_in_month[self.month - 1]:
            self.day = 1
            self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1

    def get_current_minutes(self):
        # Returns the current time in minutes since midnight
        return self.hours * 60 + self.minutes

    def get_weekday_index(self):
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return weekdays.index(self.weekday)
    
    def draw_clock(self, ctx, date_str, time_str, ip):
        clear_background(ctx)
        ctx.save()
        
        # Drawing the backgrounds
        ctx.rgb(0.11, 0.11, 0.11)
        ctx.rectangle(-120, -120, 240, 240).fill()
        
        # Drawing the top bar
        ctx.font_size = 16
        ctx.rgb(0.15, 0.15, 0.15)
        ctx.rectangle(30, -120, 200, 50).fill()
        ctx.rgb(0, 0, 0)
        ctx.rectangle(-120, -120, 240, 20).fill()
        ctx.rgb(1, 1, 1)
        ctx.move_to(-30, -85)
        ctx.text("clockface.json  x")
    
        # Drawing line numbers
        ctx.rgb(0.5, 0.5, 0.5)
        ctx.font_size = 12
        for i in range(0, 14):
            ctx.move_to(-95, (i * 20) - 60)
            ctx.text(str(i+1))

        json_data = '''
{{
  "date": "{}",
  "time": "{}",
  "ip": "{}"
}}
'''.format(date_str, time_str, ip)

        # Drawing the JSON data with syntax highlighting

        lines = json_data.strip().split('\n')
        colors = {
            'key': (0.61, 0.86, 0.99),
            'string': (0.80, 0.56, 0.47),
            'number': (0.5, 0.5, 0.8),
            'bracket': (0.8, 0.8, 0.8),
            'colon': (0.8, 0.8, 0.8),
            'comma': (0.8, 0.8, 0.8)
        }

        y_position = -60
        in_string = False  # Initialize in_string
        for line in lines:
            x_position = -80  # Moved closer to the center
            char_count = 0
            for char in line:
                if char in '{}[]':
                    ctx.rgb(*colors['bracket'])
                elif char in ':':
                    ctx.rgb(*colors['colon'])
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
