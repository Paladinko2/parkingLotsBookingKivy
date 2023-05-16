from kivymd.app import MDApp
from kivymd.uix.label import MDLabel


class ParkingApp(MDApp):
    def build(self):
        return MDLabel(text="Hello, Dimasik", halign="center")


ParkingApp().run()
