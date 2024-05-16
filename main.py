from local.pyopenttdadmin import Admin, AdminUpdateType, AdminUpdateFrequency, openttdpacket
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from kivymd.uix.list import OneLineListItem
import threading

class MainApp(MDApp):
    def build(self):
        # Setting theme to my favorite theme
        self.theme_cls.primary_palette = "DeepPurple"
        # Start the admin thread
        threading.Thread(target=self.start_admin).start()

    def start_admin(self):
        # Set the IP address and port number for connection
        ip_address = "192.168.1.3"
        port_number = 3977
        # Instantiate the Admin class and establish connection to the server
        with Admin(ip=ip_address, port=port_number, name="AndroidAdmin", password="LenovoT460s") as admin:
            # Subscribe to receive date updates and set the frequency for updates
            admin.send_subscribe(AdminUpdateType.CONSOLE)
            admin.send_subscribe(AdminUpdateType.CHAT)
            admin.send_subscribe(AdminUpdateType.CMD_LOGGING)
            admin.send_subscribe(AdminUpdateType.CLIENT_INFO)
            admin.send_subscribe(AdminUpdateType.DATE, AdminUpdateFrequency.DAILY)
            # Keep the connection open and print incoming date packets
            while True:
                # Receive packets from the server
                packets = admin.recv()
                for packet in packets:
                    # Update UI in the main thread
                    Clock.schedule_once(lambda dt, p=packet: self.update_ui(p))



    # Where stuff happens
    def update_ui(self, packet):
        # Update UI with packet data
        if packet:
            print("Received message:", packet)  # Debugging statement
            # Ensure UI updates are executed on the main thread
            print("Is main thread:", threading.current_thread().name == 'MainThread')  # Debugging statement
            self.update_ui_on_main_thread(str(packet))

    # Recieves Admin from  update_ui and then sends it over
    @mainthread
    def update_ui_on_main_thread(self, packet):
        # Update UI with packet data

        print("Received message:", str(packet))  # Debugging statement
        # Ensure UI updates are executed on the main thread
        print("Is main thread:", threading.current_thread().name == 'MainThread')  # Debugging statement
        self.update_ui_with_message(str(packet))

    def update_ui_with_message(self, message):
        # Add a new item to the MDList
        message_list = self.root.ids.message_list
        message_list.add_widget(OneLineListItem(text=message))

        # Check if the ScrollView is not at the bottom
        if message_list.parent.scroll_y > -1:
            # Ensure that the ScrollView stays at the bottom
            message_list.parent.scroll_y = 0


if __name__ == '__main__':
    app = MainApp()
    app.run()
