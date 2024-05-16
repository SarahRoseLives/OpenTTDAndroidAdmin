from local.pyopenttdadmin import Admin, AdminUpdateType, AdminUpdateFrequency, openttdpacket
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from kivymd.uix.list import OneLineListItem
import threading
import configparser


BOT_NAME = "ottdAndroidAdmin"
class MainApp(MDApp):
    # Define logging_enabled, password, admin_port, and server as class attributes
    logging_enabled = False  # Set a default value
    password = "Should Probably Pu"  # Set a default value
    admin_port = 3977  # Set a default value
    server = "Your Server URL or IP Here"  # Set a default value

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
        # Instantiate the Admin class and establish connection to the server
        with Admin(ip=self.server, port=self.admin_port, name=f"{BOT_NAME} Listener", password=self.password) as admin:
            # Subscribe to receive date updates and set the frequency for updates
            admin.send_subscribe(AdminUpdateType.CONSOLE)
            admin.send_subscribe(AdminUpdateType.CHAT)
            admin.send_subscribe(AdminUpdateType.CMD_LOGGING)
            admin.send_subscribe(AdminUpdateType.CLIENT_INFO)
            admin.send_subscribe(AdminUpdateType.DATE, AdminUpdateFrequency.ANUALLY)
            # Keep the connection open and print incoming date packets
            while True:
                # Receive packets from the server
                packets = admin.recv()
                for packet in packets:
                    # Update UI in the main thread
                    Clock.schedule_once(lambda dt, p=packet: self.update_ui(p))

    def send_to_admin_port(self, message, send_type, client_id=None):
        try:
            with Admin(ip=self.server, port=self.admin_port, name=f"{BOT_NAME} Sender", password=self.password) as admin:
                if send_type == 'global':
                    admin.send_global(message)
                if send_type == 'rcon':
                    admin.send_rcon(message)
                if send_type == 'private':
                    if client_id is None:
                        raise ValueError("client_id is required for private messages.")
                    admin.send_private(message, client_id)
        except Exception as e:
            print(f"An error occurred: {e}")
            # Handle the error appropriately

    def update_ui(self, packet):
        """
        Update the UI with packet data.

        Args:
            packet: The packet received from the server.
        """
        if packet:
            print("Received message in update_ui:", packet)  # Debugging statement
            # Ensure UI updates are executed on the main thread
            print("Is main thread:", threading.current_thread().name == 'MainThread')  # Debugging statement
            self.update_ui_on_main_thread(packet)

    # Receives packet from update_ui and then sends it over to update the UI on the main thread
    def update_ui_on_main_thread(self, packet):
        """
        Update the UI on the main thread with packet data.

        Args:
            packet: The packet data to update the UI with.
        """
        if packet:
            if isinstance(packet, openttdpacket.ChatPacket):
                print(f'Chat Packet on ui_on_main_thread: {packet}')
                self.update_ui_with_chat_message(packet)
            else:
                if self.logging_enabled is True:
                    self.update_ui_with_log_message(str(packet))
        else:
            # Ensure that the ScrollView stays at the bottom even when packet is empty
            log_message_list = self.root.ids.log_message_list
            log_message_list.parent.scroll_y = 1

    def update_ui_with_chat_message(self, message):
        """
        Update the UI with a chat message.

        Args:
            message: The chat message packet to display in the UI.
        """
        # Add a new item to the MDList

        chat_message_list = self.root.ids.chat_message_list
        try:
            chat_message_list.add_widget(OneLineListItem(text=message.message))
        except:
            pass
        try:
            chat_message_list.add_widget(OneLineListItem(text=message))
        except:
            pass

        # Schedule the scrolling to the bottom after a slight delay
        Clock.schedule_once(lambda dt: self.scroll_chat_view_to_bottom())

    def scroll_chat_view_to_bottom(self):
        """
        Scroll the chat view to the bottom.
        """
        chat_message_list = self.root.ids.chat_message_list
        chat_message_list.parent.scroll_y = 0
        chat_message_list.parent.scroll_to(chat_message_list.children[-1])  # Scroll to the bottom

    def update_ui_with_log_message(self, message):
        """
        Update the UI with a log message and ensure ScrollView stays at the bottom.

        Args:
            message: The log message to display in the UI.
        """
        # Add a new item to the MDList at the bottom
        log_message_list = self.root.ids.log_message_list
        log_message_list.add_widget(OneLineListItem(text=message))

        # Calculate the ScrollView height
        scroll_view_height = log_message_list.parent.height

        # Calculate the total height of the content
        content_height = log_message_list.minimum_height

        # Check if the ScrollView is already scrolled to the bottom
        if content_height > scroll_view_height:
            # Scroll to the bottom to show the newest message
            log_message_list.parent.scroll_y = 0

        # Check if the top message is visible
        if log_message_list.parent.scroll_y == 1:
            # Scroll to the top to show the newest message
            log_message_list.parent.scroll_y = 1

    def send_chat_message(self, message):
        """
        Send a chat message to the OpenTTD server and update the chat scroll view.

        Args:
            message: The chat message to send.
        """


        # Add the sent message to the chat scroll view
        self.update_ui_with_chat_message(message=message)

        # Send the chat message to the OpenTTD server
        self.send_to_admin_port(message=message, send_type='global')

        # Scroll the chat view to the bottom
        self.scroll_chat_view_to_bottom()




if __name__ == '__main__':
    app = MainApp()
    app.run()
