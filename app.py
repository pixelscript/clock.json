import app
import wifi
import json
import os
from requests import get
from system.eventbus import eventbus
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES

IPIFY_URL = "https://api.ipify.org"
TIME_API_URL = "https://timeapi.io/api/Time/current/ip?ipAddress="

class ClockJSON(app.App):
    def __init__(self):
        self.button_states = Buttons(self)
        self.state = "init"
        self.ip = ""
        self.ip_displayed = False
        self.local_time = ""
        self.time_fetched = False
        self.hours = 0
        self.minutes = 0
        self.day = 0
        self.month = 0
        self.year = 0
        self.weekday = ""
        self.last_update_minutes = 0
        
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
                self.last_update_minutes = self.get_current_minutes()
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
        if self.state == "init":
            print("calling get_ip")
            try:
                self.get_ip()
            except Exception as e:
                print(e)
                self.update_state("no_ip")
        elif self.state == "ip_received":
            self.handle_ip()
        elif self.state == "ip_ready" and not self.ip_displayed:
            self.ip_displayed = True
            self.update_state("fetching_time")
        elif self.state == "no_ip":
            self.ip = "No ip API"
        elif self.state == "time_fetched" and not self.time_fetched:
            self.time_fetched = True
        elif self.state == "time_fetch_error":
            self.local_time = "No time API"
            
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()

        # Update time every minute if time_fetched
        if self.state == "time_fetched":
            current_minutes = self.get_current_minutes()
            if current_minutes != self.last_update_minutes:
                self.increment_time()
                self.last_update_minutes = current_minutes

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
            ctx.rgb(0, 1, 0).move_to(0, 0).text(self.format_time())
        elif self.state == 'time_fetch_error':
            ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(1, 0, 0).move_to(0, 0).text(self.local_time)
        
        ctx.restore()
    
    def format_time(self):
        if self.local_time:
            # Custom formatting of time
            day_suffix = lambda d: 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            formatted_date = f'{weekdays[self.get_weekday_index()]}, {self.day}{day_suffix(self.day)} {months[self.month - 1]}'
            formatted_time = f'{self.hours:02d}:{self.minutes:02d}'
            return f"{formatted_date}\n{formatted_time}"
        return "No time API"

    def increment_time(self):
        self.minutes += 1
        if self.minutes >= 60:
            self.minutes = 0
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

__app_export__ = ClockJSON
