from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivy_garden.mapview import MapView, MapMarkerPopup

from firebase import firebase



class ParkingApp(MDApp):
    def build(self):
        screen_manager = ScreenManager()
        # screen_manager.add_widget(Builder.load_file("kv/welcome.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/login.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/signup.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/booking.kv"))
        screen_manager.add_widget(Builder.load_file("kv/main.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/test.kv"))

        # mapview = MapView(zoom=11, lat=50.6394, lon=3.057)


        return screen_manager

    def on_start(self):
        marker = MapMarkerPopup(lat=55.194698,lon=30.187438)
        map_screen = self.root.get_screen("main")
        map_screen.ids.map_view.add_widget(marker)

    pass

    def on_signup(self, username, email, password):
        connection = firebase.FirebaseApplication(
            "https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/", None)

        data = {
            "Username": username,
            "Email": email,
            "Password": password
        }

        connection.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Users", data)

    def show_parking_lots(self):
        parking_lots = ['Parking Lot A', 'Parking Lot B', 'Parking Lot C']
        self.root.ids.dropdown.set_item(parking_lots)

    def show_date_picker(self):
        from kivy.utils import platform
        if platform == 'android':
            import datetime
            today = datetime.date.today()
            max_date = today + datetime.timedelta(days=30)
            self.root.ids.date_picker.text = ''
            self.date_picker = MDDatePicker(callback=self.on_date_selected, max_date=max_date)
            self.date_picker.open()

    def on_date_selected(self, date):
        self.root.ids.date_picker.text = str(date)

    def on_time_selected(self):
        selected_time = self.root.ids.time_picker.time
        print(f"Selected time: {selected_time}")

    def book_parking_lot(self):
        selected_parking_lot = self.root.ids.dropdown.text
        selected_date = self.root.ids.date_picker.text
        selected_time = self.root.ids.time_picker.time
        print(f"Booking parking lot: {selected_parking_lot}")
        print(f"Date: {selected_date}")
        print(f"Time: {selected_time}")


LabelBase.register(name="Montserrat",
                   fn_regular="data/fonts/Montserrat/Montserrat-Regular.ttf",
                   fn_bold="data/fonts/Montserrat/Montserrat-Bold.ttf",
                   fn_italic="data/fonts/Montserrat/Montserrat-Italic.ttf",
                   fn_bolditalic="data/fonts/Montserrat/Montserrat-BoldItalic.ttf")

if __name__ == "__main__":
    Window.size = (360, 640)
    ParkingApp().run()
