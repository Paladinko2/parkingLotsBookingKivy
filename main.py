from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase
from kivy.lang import Builder

from firebase import firebase


# firebase = firebase.FirebaseApplication("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/", None)
#
# data = {
#     "Login": "Admin",
#     "Password": "Admin"
# }
#
# firebase.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Users", data)

class ParkingApp(MDApp):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(Builder.load_file("kv/welcome.kv"))
        screen_manager.add_widget(Builder.load_file("kv/login.kv"))
        screen_manager.add_widget(Builder.load_file("kv/signup.kv"))
        return screen_manager


LabelBase.register(name="Montserrat",
                   fn_regular="data/fonts/Montserrat/Montserrat-Regular.ttf",
                   fn_bold="data/fonts/Montserrat/Montserrat-Bold.ttf",
                   fn_italic="data/fonts/Montserrat/Montserrat-Italic.ttf",
                   fn_bolditalic="data/fonts/Montserrat/Montserrat-BoldItalic.ttf")

if __name__ == "__main__":
    Window.size = (360, 640)
    ParkingApp().run()
