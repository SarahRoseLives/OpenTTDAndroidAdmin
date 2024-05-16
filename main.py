from local.pyopenttdadmin import Admin, AdminUpdateType, AdminUpdateFrequency, openttdpacket
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from kivymd.uix.list import OneLineListItem
import threading
import configparser

class MainApp(MDApp):
    # Define logging_enabled, password, admin_port, and server as class attributes
    logging_enabled = False  # Set a default value
    password = ""  # Set a default value
    admin_port = 0  # Set a default value
    server = ""  # Set a default value

    def build(self):
        # Setting theme to my favorite theme
        self.theme_cls.primary_palette = "DeepPurple"
        # Load configuration settings
        self.load_settings()
        # Start the admin thread
        threading.Thread(target=self.start_admin).start()
        # Assign settings to UI fields
        self.assign_settings_to_ui()

    def assign_settings_to_ui(self):
        # Assign loaded settings to UI fields
        self.root.ids.openttd_server.text = self.server
        self.root.ids.admin_port.text = str(self.admin_port)
        self.root.ids.admin_password.text = self.password
        self.root.ids.enable_logging.active = self.logging_enabled

    def load_settings(self):
        # Read configuration settings
        filename = 'OpenTTDAdmin.conf'
        config = self.read_config(filename)
        openTTDAdmin_config = config['OpenTTDAdmin']
        # Load settings into variables
        self.server = openTTDAdmin_config['server']
        self.admin_port = int(openTTDAdmin_config['admin_port'])
        self.password = openTTDAdmin_config['password']
        # Convert logging_enabled to a boolean
        self.logging_enabled = openTTDAdmin_config.getboolean('logging_enabled')
        # Print loaded settings for debugging
        print("Loaded settings - Server:", self.server, "Port:", self.admin_port, "Password:", self.password,
              "Logging Enabled:", self.logging_enabled)

    def read_config(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        return config

    def save_settings(self, server, admin_port, password, logging_enabled):
        # Update configuration settings
        filename = 'OpenTTDAdmin.conf'
        config = self.read_config(filename)
        openTTDAdmin_config = config['OpenTTDAdmin']
        openTTDAdmin_config['server'] = server
        openTTDAdmin_config['admin_port'] = admin_port
        openTTDAdmin_config['password'] = password
        openTTDAdmin_config['logging_enabled'] = str(logging_enabled)
        # Save changes to the configuration file
        with open(filename, 'w') as configfile:
            config.write(configfile)
        # Print saved settings for debugging
        print("Settings saved - Server:", server, "Port:", admin_port, "Password:", password, "Logging Enabled:",
              logging_enabled)
        # Reload settings
        self.load_settings()
        # Restart Admin Thread
        self.restart_admin_thread()

    def restart_admin_thread(self):
        # Stop the admin thread if it's running
        if hasattr(self, 'admin_thread') and self.admin_thread.is_alive():
            self.stop_admin_thread()

        # Start the admin thread again
        threading.Thread(target=self.start_admin).start()

    def start_admin(self):
        # Set the IP address and port number for connection
        #ip_address = "192.168.1.3"
        #port_number = 3977
        # Instantiate the Admin class and establish connection to the server
        with Admin(ip=self.server, port=self.admin_port, name="AndroidAdmin", password=self.password) as admin:
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


    def process_welcome_packet(self):
        pass


    # Where stuff happens
    def update_ui(self, packet):
        # Update UI with packet data
        if packet:
            if self.logging_enabled is True:
                print("Received message:", packet)  # Debugging statement
                # Ensure UI updates are executed on the main thread
                print("Is main thread:", threading.current_thread().name == 'MainThread')  # Debugging statement
                self.update_ui_on_main_thread(str(packet))

    # Recieves Admin from  update_ui and then sends it over
    @mainthread
    def update_ui_on_main_thread(self, packet):
        # Update UI with packet data
        if packet:
            print("Received message:", str(packet))  # Debugging statement
            # Ensure UI updates are executed on the main thread
            print("Is main thread:", threading.current_thread().name == 'MainThread')  # Debugging statement
            self.update_ui_with_log_message(str(packet))
        else:
            # Ensure that the ScrollView stays at the bottom even when packet is empty
            log_message_list = self.root.ids.log_message_list
            log_message_list.parent.scroll_y = 0

    def update_ui_with_log_message(self, message):
        # Add a new item to the MDList
        log_message_list = self.root.ids.log_message_list
        log_message_list.add_widget(OneLineListItem(text=message))

        # Ensure that the ScrollView stays at the bottom
        log_message_list.parent.scroll_y = 0


if __name__ == '__main__':
    app = MainApp()
    app.run()
