import datetime

import re
from random import random, uniform

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivy_garden.mapview import MapView, MapMarkerPopup
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivy.clock import Clock

from firebase import firebase


# class MarkerInfoPopup(Popup):
#     zone_number = StringProperty()
#     address = StringProperty()
#
#     def __init__(self, **kwargs):
#         super(MarkerInfoPopup, self).__init__(**kwargs)
#         self.title = 'Парковочная зона'
#
#     def dismiss(self):
#         super(MarkerInfoPopup, self).dismiss()

class MarkerInfoPopup(MDDialog):
    zone_number = StringProperty()
    address = StringProperty()

    def __init__(self, **kwargs):
        super(MarkerInfoPopup, self).__init__(
            title="Парковочная зона",
            type="custom",
            buttons=[
                MDFlatButton(
                    text="Close", md_bg_color=(0, 0, 1, 1), text_color=(1, 1, 1, 1), on_release=self.close_dialog
                ),
            ],
            **kwargs
        )

    def close_dialog(self, *args):
        self.dismiss()


class ParkingApp(MDApp):
    getting_markets_timer = None
    marker_info_popup = None

    def build(self):
        LabelBase.register(name="Montserrat",
                           fn_regular="data/fonts/Montserrat/Montserrat-Regular.ttf",
                           fn_bold="data/fonts/Montserrat/Montserrat-Bold.ttf",
                           fn_italic="data/fonts/Montserrat/Montserrat-Italic.ttf",
                           fn_bolditalic="data/fonts/Montserrat/Montserrat-BoldItalic.ttf")
        Builder.load_file("kv/markerinfo.kv")  # Загрузка разметки из файла markerinfo.kv

        screen_manager = ScreenManager()
        # screen_manager.add_widget(Builder.load_file("kv/welcome.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/login.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/signup.kv"))
        screen_manager.add_widget(Builder.load_file("kv/main.kv"))

        # screen_manager.add_widget(Builder.load_file("kv/booking.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/test.kv"))

        # mapview = MapView(zoom=11, lat=50.6394, lon=3.057)

        return screen_manager

    def on_start(self):
        # marker = MapMarkerPopup(lat=55.194698, lon=30.187438)

        marks = self.get_marks()
        # print(marks.keys())
        # if marks is not None:
        #     for i in marks.keys():
        #         self.mv().add_widget(MapMarkerPopup(lat=marks[i]["Lat"], lon=marks[i]["Lon"]))

        if marks is not None:
            for i in marks.keys():
                marker = MapMarkerPopup(lat=marks[i]["Lat"], lon=marks[i]["Lon"])

                button = Button(text="Получить информацию")
                button.bind(on_release=lambda btn, marker_info=marks[i]: self.show_marker_info(marker_info))

                marker.add_widget(button)
                self.mv().add_widget(marker)

        # for i in range(1, 3):
        #     lat = uniform(55.13, 55.23)
        #     lon = uniform(30.1, 30.3)
        #     mark = {
        #         "Lat": lat,
        #         "Lon": lon,
        #         "Number": self.distinct_zone_numbers(),
        #         "Address": "Vitebsk, etc.."
        #     }
        #     self.post_marks(mark)

        pass

    def distinct_zone_numbers(self):
        marks = self.get_marks()
        numbers = []
        return_num = 0
        if marks is not None:
            numbers = [mark["Number"] for mark in marks.values()]
            print(numbers)
            for i in range(1, len(marks) + 2):
                if i not in numbers:
                    return_num = i
        else:
            return_num = 1
        return return_num

    # def show_marker_info(self, marker):
    #     if self.marker_info_popup:  # Закрытие предыдущего экземпляра MarkerInfoPopup
    #         self.marker_info_popup.dismiss()
    #
    #     self.marker_info_popup = MarkerInfoPopup()
    #     self.marker_info_popup.zone_number = str(marker["Number"])
    #     self.marker_info_popup.address = marker["Address"]
    #     self.marker_info_popup.open()

    def show_marker_info(self, marker):
        if self.marker_info_popup:  # Закрытие предыдущего экземпляра MarkerInfoPopup
            self.marker_info_popup.dismiss()

        self.marker_info_popup = MarkerInfoPopup(
            zone_number=str(marker["Number"]),
            address=marker["Address"]
        )
        self.marker_info_popup.open()

    def start_getting_markets_in_fov(self):
        try:
            self.getting_markets_timer.cancel()
        except:
            pass

        self.getting_markets_timer = Clock.schedule_once(self.get_markets_in_fov, 1)

    def get_markets_in_fov(self, *args):
        print(self.mv().get_bbox())

    # MapView
    def mv(self):
        map_screen = self.root.get_screen("main")
        return map_screen.ids.map_view

    def on_login(self, email, password):

        # self.root.email_valid = self.validate_email(email)
        # self.root.password_valid = self.validate_password(email, password)

        # if not self.root.email_valid:
        #     print("WRONG EMAIL")
        #
        # if not self.root.password_valid:
        #     print("WRONG PASSWORD")

        if self.validate_email(email) and self.validate_password(email, password):
            print(email + " Вы вошли!")
            self.root.current = "main"
        else:
            print("Ошибка входа")
            self.root.email_valid = False
            self.root.password_valid = False

    def on_signup(self, email, password, rep_password):

        emails = self.get_emails()

        validRegistration = True

        # Проверка длины пароля
        if len(password) < 4 or len(password) > 20:
            validRegistration = False

        # Проверка наличия заглавной, строчной буквы и цифры
        if not re.search(r"[A-Z]", password):
            validRegistration = False
        if not re.search(r"[a-z]", password):
            validRegistration = False
        if not re.search(r"\d", password):
            validRegistration = False

        # Проверка на то, совпадают ли введённые пароли при регистрации
        if password != rep_password:
            validRegistration = False

        # Проверка на то, зарегистрирован ли уже пользователь с введённой почтой
        if email in emails:
            validRegistration = False

        if validRegistration:
            user_data = {
                "Email": email,
                "Password": password,
                "RegistrationDateTime": datetime.datetime.now()
            }

            self.post_users(user_data)
            self.root.current = "main"
        else:
            print("Ошибка регистрации!")

    def db(self):
        return firebase.FirebaseApplication(
            "https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/", None)

    def get_users(self):
        connection = self.db()
        users = connection.get("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Users",
                               "")
        return users

    def get_marks(self):
        connection = self.db()
        marks = connection.get("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Marks",
                               "")
        return marks

    def post_users(self, user_data):
        connection = self.db()
        connection.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Users",
                        user_data)

    def post_marks(self, marks_data):
        connection = self.db()
        connection.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Marks",
                        marks_data)

    def get_emails(self):
        users = self.get_users()
        emails = [user['Email'] for user in users.values()]
        return emails

    def validate_email(self, email):
        emails = self.get_emails()
        self.root.email_valid = email in emails or email == "admin"
        return self.root.email_valid

    def validate_password(self, email, password):
        users = self.get_users()
        for i in users.keys():
            if users[i] is not None and users[i]["Email"] == email:
                if users[i]["Password"] == password:
                    self.root.password_valid = True
                    return True
        self.root.password_valid = False
        return False


if __name__ == "__main__":
    Window.size = (360, 640)
    ParkingApp().run()
    # def show_parking_lots(self):
    #     parking_lots = ['Parking Lot A', 'Parking Lot B', 'Parking Lot C']
    #     self.root.ids.dropdown.set_item(parking_lots)
    #
    # def show_date_picker(self):
    #     from kivy.utils import platform
    #     if platform == 'android':
    #         import datetime
    #         today = datetime.date.today()
    #         max_date = today + datetime.timedelta(days=30)
    #         self.root.ids.date_picker.text = ''
    #         self.date_picker = MDDatePicker(callback=self.on_date_selected, max_date=max_date)
    #         self.date_picker.open()
    #
    # def on_date_selected(self, date):
    #     self.root.ids.date_picker.text = str(date)
    #
    # def on_time_selected(self):
    #     selected_time = self.root.ids.time_picker.time
    #     print(f"Selected time: {selected_time}")
    #
    # def book_parking_lot(self):
    #     selected_parking_lot = self.root.ids.dropdown.text
    #     selected_date = self.root.ids.date_picker.text
    #     selected_time = self.root.ids.time_picker.time
    #     print(f"Booking parking lot: {selected_parking_lot}")
    #     print(f"Date: {selected_date}")
    #     print(f"Time: {selected_time}")
