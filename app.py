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
                self.update_state("time_fetched")
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
            ctx.rgb(0, 1, 0).move_to(0, 0).text(self.local_time)
        elif self.state == 'time_fetch_error':
            ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(1, 0, 0).move_to(0, 0).text(self.local_time)
        
        ctx.restore()

__app_export__ = ClockJSON
