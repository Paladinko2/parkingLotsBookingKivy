import datetime

import re
from random import random, uniform, choice

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatButton, MDFloatingActionButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivymd.uix.list import OneLineListItem
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivy_garden.mapview import MapView, MapMarkerPopup
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivy.clock import Clock
from kivymd.font_definitions import theme_font_styles

from firebase import firebase

from geopy.geocoders import Nominatim

from kivy.uix.screenmanager import Screen


class MarkerInfoPopup(MDDialog):
    zone_number = StringProperty()
    address = StringProperty()
    lots = StringProperty()
    av_lots = StringProperty()
    app = None

    def __init__(self, parking_app, **kwargs):
        super(MarkerInfoPopup, self).__init__(
            title="Парковочная зона",
            type="custom",
            **kwargs
        )
        self.size_hint = (0.8, 0.8)
        self.app = parking_app

    def close_dialog(self, *args):
        self.dismiss()

    def book(self, zone_number):
        self.app.book(zone_number)


class BookingInfoPopup(MDDialog):
    zone = StringProperty()
    lot = StringProperty()
    date = StringProperty()
    app = None

    def __init__(self, parking_app, **kwargs):
        super(BookingInfoPopup, self).__init__(**kwargs)
        self.size_hint = (0.8, 0.8)
        self.app = parking_app

    def show_booking_info(self, zone, lot, date):
        self.zone = zone
        self.lot = lot
        self.date = date
        self.open()

    def cancel_booking(self):
        self.app.cancel_booking(self.zone, self.lot)


class ParkingApp(MDApp):
    getting_markets_timer = None
    marker_info_popup = None
    user = {
        "Email": "admin",
        "Password": "admin"
    }

    def build(self):
        LabelBase.register(name="Montserrat",
                           fn_regular="data/fonts/Montserrat/Montserrat-Regular.ttf",
                           fn_bold="data/fonts/Montserrat/Montserrat-Bold.ttf",
                           fn_italic="data/fonts/Montserrat/Montserrat-Italic.ttf",
                           fn_bolditalic="data/fonts/Montserrat/Montserrat-BoldItalic.ttf")
        Builder.load_file("kv/markerinfo.kv")
        Builder.load_file("kv/bookinginfo.kv")

        screen_manager = ScreenManager()
        # screen_manager.add_widget(Builder.load_file("kv/welcome.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/login.kv"))
        # screen_manager.add_widget(Builder.load_file("kv/signup.kv"))
        screen_manager.add_widget(Builder.load_file("kv/bookings.kv"))
        screen_manager.add_widget(Builder.load_file("kv/main.kv"))

        # screen_manager.add_widget(Builder.load_file("kv/test.kv"))

        # mapview = MapView(zoom=11, lat=50.6394, lon=3.057)

        return screen_manager

    def on_start(self):
        marks = self.get_marks()
        print(marks.keys())
        if marks is not None:
            for i in marks.keys():
                self.mv().add_widget(MapMarkerPopup(lat=marks[i]["Lat"], lon=marks[i]["Lon"]))

        if marks is not None:
            for i in marks.keys():
                marker = MapMarkerPopup(lat=marks[i]["Lat"], lon=marks[i]["Lon"])

                button = MDFloatingActionButton(
                    icon='',
                    text=str(marks[i]["Available"]),
                    font_style='H6',
                    text_color=(1, 1, 1, 1),
                    size_hint=(None, None),
                    size=('56dp', '56dp'),
                )

                label = Label(
                    text=button.text,
                    font_size=button.font_size,
                    halign='center',
                    valign='middle',
                    size_hint=(None, None),
                    size=button.size,
                    pos=button.pos,
                    color=button.text_color,
                )

                button.add_widget(label)

                button.bind(on_release=lambda btn, marker_info=marks[i]: self.show_marker_info(marker_info))

                marker.add_widget(button)
                self.mv().add_widget(marker)

        # for i in range(1, 10):
        #     lat = uniform(55.13, 55.23)
        #     lon = uniform(30.1, 30.3)
        #     lots = int(uniform(10, 30))
        #     av_lots = int(uniform(0, lots))
        #
        #     mark = {
        #         "Lat": lat,
        #         "Lon": lon,
        #         "Number": self.distinct_zone_numbers(),
        #         "Address": self.get_address(lat, lon),
        #         "LotsNumber": lots,
        #         "Available": av_lots,
        #         "Lots": self.make_lots(av_lots, lots)
        #     }
        #     self.post_marks(mark)

        pass

    def book(self, zone_number):
        mark = self.get_mark_by_num(zone_number)
        if mark is not None and mark[1]["Available"] > 0:
            key, val = mark

            lot_key = 0

            for i in range(len(val["Lots"])):
                if val["Lots"][i]["Status"] == "Available":
                    val["Lots"][i]["Status"] = "Not available"
                    lot_key = i
                    mark[1]["Available"] = mark[1]["Available"] - 1
                    mark[1]["Lots"][i] = val["Lots"][i]
                    break

            booking = self.get_booking_by_email(self.user["Email"])

            lot_data = {
                "Lot": lot_key,
                "Zone": zone_number
            }

            if booking is not None:
                k, v = booking
                v["List"].append(lot_data)
                booking_data = {
                    "Email": self.user["Email"],
                    "List": v["List"]
                }
                self.update_booking(k, booking_data)
            else:
                booking_data = {
                    "Email": self.user["Email"],
                    "List": [lot_data]
                }
                self.post_booking(booking_data)

            # self.update_mark(key, val)

        else:
            print("Empty parking zone!")

    def update_mark(self, key, mark_data):
        connection = self.db()
        connection.put("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Marks",
                       key, mark_data)

    def get_bookings(self):
        connection = self.db()
        bookings = connection.get("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app"
                                  "/Bookings", "")
        return bookings

    def get_booking_by_email(self, email):
        bookings = self.get_bookings()
        if bookings is not None:
            for key, booking in bookings.items():
                if booking["Email"] == email:
                    return key, booking

    def post_booking(self, booking_data):
        connection = self.db()
        connection.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Bookings",
                        booking_data)

    def update_booking(self, key, booking_data):
        connection = self.db()
        connection.put("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Bookings", key,
                       booking_data)

    def distinct_zone_numbers(self):
        marks = self.get_marks()
        numbers = []
        return_num = 0
        if marks is not None:
            numbers = [mark["Number"] for mark in marks.values()]
            # print(numbers)
            for i in range(1, len(marks) + 2):
                if i not in numbers:
                    return_num = i
        else:
            return_num = 1
        return return_num

    def show_marker_info(self, marker):
        if self.marker_info_popup:  # Закрытие предыдущего экземпляра MarkerInfoPopup
            self.marker_info_popup.dismiss()

        self.marker_info_popup = MarkerInfoPopup(
            parking_app=self,
            zone_number=str(marker["Number"]),
            address=marker["Address"],
            av_lots=str(marker["Available"]),
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

    def bkgs(self):
        bookings_screen = self.root.get_screen("bookings")
        return bookings_screen.ids.bookings_list

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
            self.user = {
                "Email": email,
                "Password": password
            }
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

            self.post_user(user_data)
            self.user = {
                "Email": email,
                "Password": password
            }
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

    def get_mark_by_num(self, num):
        marks = self.get_marks()
        for key, mark in marks.items():
            if mark["Number"] == int(num):
                return key, mark

    def post_user(self, user_data):
        connection = self.db()
        connection.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Users",
                        user_data)

    def post_mark(self, mark_data):
        connection = self.db()
        connection.post("https://parkinglotsbookingkivy-default-rtdb.europe-west1.firebasedatabase.app/Marks",
                        mark_data)

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

    def get_address(self, latitude, longitude):
        geolocator = Nominatim(user_agent="my_app")  # Создаем экземпляр геокодера
        location = geolocator.reverse(f"{latitude}, {longitude}")  # Получаем обратную геокодировку
        address = location.address  # Извлекаем адрес из результата
        return address

    def make_lots(self, av_lots, lots):
        types = ["Motorcycle", "Car", "Truck"]
        status = "Not available"
        lots_array = []
        for i in range(lots):
            if i >= lots - av_lots and status != "Available":
                status = "Available"
            lots_array.append({
                "Status": status,
                "Type": choice(types)
            })
        return lots_array

    def go_to_main_screen(self):
        self.root.transition.direction = "right"
        self.root.current = "main"

    def open_bookings(self):
        booking_list = self.get_booking_by_email(self.user["Email"])
        key, val = booking_list
        self.bkgs().clear_widgets()

        for item in val["List"]:
            lot = str(item["Lot"])
            zone = item["Zone"]
            # date = item["Date"]
            date = "04.06.23"

            booking_text = f'Зона: {zone}, Место №: {lot}, Дата: {date}'
            booking_item = OneLineListItem(text=booking_text)
            booking_item.bind(on_release=lambda instance: self.show_booking_info(zone, lot, date))

            self.bkgs().add_widget(booking_item)

        self.root.transition.direction = "left"
        self.root.current = "bookings"

    def show_booking_info(self, zone, lot, date):
        popup = BookingInfoPopup(self, zone=zone, lot=lot, date=date)
        popup.open()

    def update_bookings_list(self):
        self.bkgs().clear_widgets()
        self.open_bookings()

    def cancel_booking(self, bookings):
        print("CANCELLING")
        pass


if __name__ == "__main__":
    Window.size = (360, 640)
    ParkingApp().run()
