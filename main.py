import datetime
import re
from random import choice, uniform

from firebase import firebase
from geopy.geocoders import Nominatim
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.mapview import MapMarkerPopup
from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField


class MarkerInfoPopup(MDDialog):
    zone_number = StringProperty()
    address = StringProperty()
    lots = StringProperty()
    av_lots = StringProperty()
    date = None
    range = None
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

    def show_datepicker(self):
        picker = MDDatePicker()
        picker.bind(on_save=self.on_save, on_cancel=self.on_cancel)
        picker.open()

    def book(self, zone_number):
        if self.date:
            self.app.book(zone_number, self.date)

    def on_save(self, instance, value, date_range):
        self.date = value
        self.range = date_range

    def on_cancel(self, instance, value):
        pass


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

    def cancel_booking(self, zone_number, lot_number):
        self.app.cancel_booking(zone_number, lot_number)


class ParkingApp(MDApp):
    db_link = "https://parkinglotsbookingkivynew-default-rtdb.europe-west1.firebasedatabase.app/"
    getting_markets_timer = None
    marker_info_popup = None
    user = {
        "Email": "admin",
        "Password": "admin",
        "RegistrationDateTime": "none"
    }
    buttons = {}

    def build(self):
        LabelBase.register(name="Montserrat",
                           fn_regular="data/fonts/Montserrat/Montserrat-Regular.ttf",
                           fn_bold="data/fonts/Montserrat/Montserrat-Bold.ttf",
                           fn_italic="data/fonts/Montserrat/Montserrat-Italic.ttf",
                           fn_bolditalic="data/fonts/Montserrat/Montserrat-BoldItalic.ttf")
        Builder.load_file("kv/markerinfo.kv")
        Builder.load_file("kv/bookinginfo.kv")

        screen_manager = ScreenManager()

        screen_manager.add_widget(Builder.load_file("kv/welcome.kv"))
        screen_manager.add_widget(Builder.load_file("kv/login.kv"))
        screen_manager.add_widget(Builder.load_file("kv/signup.kv"))
        screen_manager.add_widget(Builder.load_file("kv/main.kv"))
        screen_manager.add_widget(Builder.load_file("kv/bookings.kv"))
        screen_manager.add_widget(Builder.load_file("kv/accountinfo.kv"))


        return screen_manager

    def on_start(self):

        self.open_map()

        # for i in range(1, 15):
        #     lat = uniform(55.14992, 55.22977)
        #     lon = uniform(30.16737, 30.26140)
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
        #         "Lots": self.make_lots(av_lots, lots),
        #         "Test": 1,
        #     }
        #     self.post_mark(mark)

        pass

    def open_map(self):
        marks = self.get_marks()
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

                self.buttons[i] = button

    def book(self, zone_number, book_date):
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
                "Zone": zone_number,
                "BookingDate": book_date
            }

            if booking is not None:
                k, v = booking
                v["List"].append(lot_data)
                booking_data = {
                    "Email": self.user["Email"],
                    "List": v["List"],
                    "Date": book_date,
                }
                self.update_booking(k, booking_data)
            else:
                booking_data = {
                    "Email": self.user["Email"],
                    "List": [lot_data],
                    "Date": book_date,
                }
                self.post_booking(booking_data)

            self.update_mark(key, val)
            self.update_button_text(key, str(mark[1]["Available"]), mark)

        else:
            self.show_popup("Свободных мест нет!")

    def show_popup(self, text, title="Ошибка"):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="Закрыть", on_release=lambda *args: dialog.dismiss()
                )
            ],
        )
        dialog.open()

    def cancel_booking(self, zone_number, lot_key):
        mark = self.get_mark_by_num(zone_number)
        lot_key = int(lot_key)

        if mark is not None:
            key, val = mark

            if lot_key < len(val["Lots"]) and val["Lots"][lot_key]["Status"] == "Not available":

                val["Lots"][lot_key]["Status"] = "Available"
                mark[1]["Available"] = mark[1]["Available"] + 1
                mark[1]["Lots"][lot_key] = val["Lots"][lot_key]

                self.update_mark(key, val)
                self.update_button_text(key, str(mark[1]["Available"]), mark)

                booking = self.get_booking_by_email(self.user["Email"])
                if booking is not None:
                    k, v = booking
                    for i, book in enumerate(v["List"]):
                        if book["Lot"] == lot_key and book["Zone"] == zone_number:
                            v["List"].pop(i)
                            list_to_add = []
                            if not v["List"]:
                                list_to_add = [{
                                    "Lot": "Empty",
                                    "Zone": "Empty"
                                }]
                            else:
                                list_to_add = v["List"]
                            booking_data = {
                                "Email": self.user["Email"],
                                "List": list_to_add
                            }

                            self.update_booking(k, booking_data)
                            break

    def update_button_text(self, key, new_text, marker_i):
        button = self.buttons[key]
        parent_widget = button.parent

        if parent_widget:
            parent_widget.remove_widget(button)

        new_button = MDFloatingActionButton(
            icon='',
            text=new_text,
            font_style='H6',
            text_color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=('56dp', '56dp'),
        )

        label = Label(
            text=new_button.text,
            font_size=new_button.font_size,
            halign='center',
            valign='middle',
            size_hint=(None, None),
            size=new_button.size,
            pos=new_button.pos,
            color=new_button.text_color,
        )

        new_button.add_widget(label)

        new_button.bind(on_release=lambda btn, marker_info=marker_i[1]: self.show_marker_info(marker_info))

        parent_widget.add_widget(new_button)
        self.buttons[key] = new_button

    def update_mark(self, key, mark_data):
        connection = self.db()
        connection.put(self.db_link + "Marks", key, mark_data)

    def update_user(self, key, user_data):
        connection = self.db()
        connection.put(self.db_link + "Users", key, user_data)

    def get_bookings(self):
        connection = self.db()
        bookings = connection.get(self.db_link + "/Bookings", "")
        return bookings

    def get_booking_by_email(self, email):
        bookings = self.get_bookings()
        if bookings is not None:
            for key, booking in bookings.items():
                if booking["Email"] == email:
                    return key, booking

    def post_booking(self, booking_data):
        connection = self.db()
        connection.post(self.db_link + "Bookings", booking_data)

    def update_booking(self, key, booking_data):
        connection = self.db()
        connection.put(self.db_link + "Bookings", key, booking_data)

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

    def show_marker_info(self, mark):
        key, marker = self.get_mark_by_num(int(mark["Number"]))

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

    def mv(self):
        return self.ms().ids.map_view

    def bkgs(self):
        bookings_screen = self.root.get_screen("bookings")
        return bookings_screen.ids.bookings_list

    def on_login(self, email, password):

        if self.correct_email(email) and self.correct_password(email, password):
            # print(email + " Вы вошли!")
            self.user = {
                "Email": email,
                "Password": password
            }
            self.root.current = "main"
        else:
            self.show_popup("Ошибка входа")
            self.root.email_valid = False
            self.root.password_valid = False

    def on_signup(self, email, password, rep_password):

        emails = self.get_emails()

        validRegistration = True

        validRegistration = self.validate_password(password)


        if password != rep_password:
            validRegistration = False

        # Проверка на то, зарегистрирован ли уже пользователь с введённой почтой
        if emails is not None:
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
            self.show_popup("Ошибка регистрации!")

    def change_password(self, new_password, repeat_password):
        users = self.get_users()

        if new_password == repeat_password:
            if users is not None:
                for key, user in users.items():
                    if user["Email"] == self.user["Email"]:
                        if user["Password"] == new_password:
                            self.show_popup("Старый и новый пароли не могут совпадать")
                        else:
                            if self.validate_password(new_password):
                                user["Password"] = new_password
                                self.update_user(key, user)
                                self.show_popup("Пароль был успешно изменён", "Успех")
                            else:
                                self.show_popup("Пароль должен содержать буквы разных регистров и цифры. \nДлина должна быть больше 3-х символов.")
                        break
        else:
            self.show_popup("Введённые пароли не совпадают")

    def validate_password(self, password):
        validRegistration = True

        if len(password) < 4 or len(password) > 20:
            validRegistration = False

        if not re.search(r"[A-Z]", password):
            validRegistration = False
        if not re.search(r"[a-z]", password):
            validRegistration = False
        if not re.search(r"\d", password):
            validRegistration = False
        return validRegistration

    def db(self):
        return firebase.FirebaseApplication(self.db_link, None)

    def get_users(self):
        connection = self.db()
        users = connection.get(self.db_link + "Users", "")
        return users

    def get_marks(self):
        connection = self.db()
        marks = connection.get(self.db_link + "Marks", "")
        return marks

    def get_mark_by_num(self, num):
        marks = self.get_marks()
        for key, mark in marks.items():
            if mark["Number"] == int(num):
                return key, mark

    def post_user(self, user_data):
        connection = self.db()
        connection.post(self.db_link + "Users", user_data)

    def post_mark(self, mark_data):
        connection = self.db()
        connection.post(self.db_link + "Marks",
                        mark_data)

    def get_emails(self):
        users = self.get_users()
        if users is not None:
            emails = [user['Email'] for user in users.values()]
        else:
            emails = None
        return emails

    def correct_email(self, email):
        emails = self.get_emails()
        self.root.email_valid = email in emails or email == "admin"
        return self.root.email_valid

    def correct_password(self, email, password):
        users = self.get_users()
        for i in users.keys():
            if users[i] is not None and users[i]["Email"] == email:
                if users[i]["Password"] == password:
                    self.root.password_valid = True
                    return True
        self.root.password_valid = False
        return False

    def go_to_account(self):
        self.root.transition.direction = "left"
        self.root.current = "account"

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

        if booking_list is not None:
            key, val = booking_list
            self.bkgs().clear_widgets()

            for item in val["List"]:
                if item["Zone"] != "Empty":
                    lot = str(item["Lot"])
                    zone = item["Zone"]
                    date = item["BookingDate"]

                    booking_text = f'Зона: {zone}, Место №: {lot}, Дата: {date}'
                    booking_item = OneLineListItem(text=booking_text)
                    booking_item.bind(on_release=lambda instance: self.show_booking_info(zone, lot, date))

                    self.bkgs().add_widget(booking_item)

        self.root.transition.direction = "left"
        self.root.current = "bookings"

    def show_booking_info(self, zone, lot, date):
        popup = BookingInfoPopup(self, zone=zone, lot=lot, date=date)
        popup.open()

    def update_map(self):
        self.mv().clear_markers()
        # self.open_map()

    def update_bookings_list(self):
        self.bkgs().clear_widgets()
        self.open_bookings()

    def get_available_lots_number(self, zone_number):
        return self.get_mark_by_num(zone_number)[1]["Available"]

    def ms(self):
        return self.root.get_screen("main")

    def change_label_text(self):
        print(self.ms().ids.label_name.text)
        self.ms().ids.label_name.text = self.user["Email"]
        print(self.ms().ids.label_name.text)


if __name__ == "__main__":
    Window.size = (360, 640)
    ParkingApp().run()
