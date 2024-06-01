import app
import time
from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES

class ClockJSON(app.App):
    def __init__(self):
        self.button_states = Buttons(self)
    
    def update(self, delta):
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()
    
    def draw(self, ctx):
        clear_background(ctx)
        ctx.save()
        
        ctx.font_size = 14
        
        # Drawing the backgrounds
        ctx.rgb(0.11, 0.11, 0.11)
        ctx.rectangle(-120, -120, 240, 240).fill()  # Adjusted width and height
        
        # Drawing the top bar
        ctx.rgb(0.15, 0.15, 0.15)
        ctx.rectangle(10, -120, 200, 25).fill()  # Adjusted width
        ctx.rgb(1, 1, 1)
        ctx.move_to(-90, -100)  # Moved closer to the center
        ctx.text("clockface.json  x")
    
        # Drawing line numbers
        ctx.rgb(0.5, 0.5, 0.5)
        ctx.font_size = 12
        for i in range(1, 14):
            ctx.move_to(-95, (i * 20) - 80)  # Moved closer to the center
            ctx.text(str(i+1))
        
        # Getting current date and time
        current_time = time.localtime()
        week_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        date_str = "{}, {} {}".format(week_days[current_time[6]], current_time[2], months[current_time[1] - 1])
        time_str = "{:02}:{:02}".format(current_time[3], current_time[4])

        json_data = '''
{{
  "date": "{}",
  "time": "{}",
  "bio": {{
    "coolness": "100%",
    "steps": "???"
  }},
  "battery": "100%"
}}
'''.format(date_str, time_str)

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

        y_position = -80
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
