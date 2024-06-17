from local.pyopenttdadmin import Admin, AdminUpdateType, AdminUpdateFrequency, openttdpacket
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from kivymd.uix.list import OneLineListItem
import threading
import configparser
from kivymd.uix.list import ThreeLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import DictProperty
from kivy.metrics import dp
import re



# Define a dictionary with data
data_dict = {
    "Item 1": {
        "line1": "Detail 1 Line 1",
        "line2": "Detail 1 Line 2",
        "line3": "Detail 1 Line 3"
    },
    "Item 2": {
        "line1": "Detail 2 Line 1",
        "line2": "Detail 2 Line 2",
        "line3": "Detail 2 Line 3"
    },
    "Item 3": {
        "line1": "Detail 3 Line 1",
        "line2": "Detail 3 Line 2",
        "line3": "Detail 3 Line 3"
    },
    "Item 4": {
        "line1": "Detail 4 Line 1",
        "line2": "Detail 4 Line 2",
        "line3": "Detail 4 Line 3"
    }
}


BOT_NAME = "ottdAndroidAdmin"

class MainApp(MDApp):
    # Define logging_enabled, password, admin_port, and server as class attributes
    logging_enabled = False  # Set a default value
    password = ""  # Set a default value
    admin_port = 3977  # Set a default value
    server = ""  # Set a default value
    server_alias = ""
    logging_chat_enabled = False
    logging_console_enabled = False
    logging_clientinfo_enabled = False
    logging_rcon_enabled = False

    data = DictProperty(data_dict)

    def build(self):
        # Setting theme to my favorite theme
        self.theme_cls.primary_palette = "DeepPurple"
        # Load configuration settings
        self.load_settings()
        # Start the admin thread
        threading.Thread(target=self.start_admin).start()
        # Assign settings to UI fields after UI is loaded
        Clock.schedule_once(lambda dt: self.assign_settings_to_ui())

        Clock.schedule_interval(lambda dt: self.update_clientlist(), 5)

    def assign_settings_to_ui(self):
        # Assign loaded settings to UI fields
        self.root.ids.openttd_server.text = self.server
        self.root.ids.server_alias.text = self.server_alias
        self.root.ids.admin_port.text = str(self.admin_port)
        self.root.ids.admin_password.text = self.password
        self.root.ids.enable_logging.active = self.logging_enabled
        self.root.ids.enable_chat_logging.active = self.logging_chat_enabled
        self.root.ids.enable_console_logging.active = self.logging_console_enabled
        self.root.ids.enable_clientinfo_logging.active = self.logging_clientinfo_enabled
        self.root.ids.enable_rcon_logging.active = self.logging_rcon_enabled

    def load_settings(self):
        # Read configuration settings
        filename = 'OpenTTDAdmin.conf'
        config = configparser.ConfigParser()
        config.read(filename)
        # Load settings into variables
        self.server = config.get('OpenTTDAdmin', 'server')
        self.server_alias = config.get('OpenTTDAdmin', 'server_alias',
                                       fallback='')  # Load server_alias with a default value
        self.admin_port = config.getint('OpenTTDAdmin', 'admin_port')
        self.password = config.get('OpenTTDAdmin', 'password')
        # Convert logging_enabled to a boolean
        self.logging_enabled = config.getboolean('OpenTTDAdmin', 'logging_enabled')
        self.logging_chat_enabled = config.getboolean('OpenTTDAdmin', 'logging_chat_enabled')
        self.logging_console_enabled = config.getboolean('OpenTTDAdmin', 'logging_console_enabled')
        self.logging_clientinfo_enabled = config.getboolean('OpenTTDAdmin', 'logging_clientinfo_enabled')
        self.logging_rcon_enabled = config.getboolean('OpenTTDAdmin', 'logging_rcon_enabled')
        # Print loaded settings for debugging
        print("Loaded settings - Server:", self.server, "Alias:", self.server_alias, "Port:", self.admin_port,
              "Password:", self.password, "Logging Enabled:", self.logging_enabled,
              "Chat Logging Enabled:", self.logging_chat_enabled,
              "Console Logging Enabled:", self.logging_console_enabled,
              "Client Info Logging Enabled:", self.logging_clientinfo_enabled,
              "Rcon Logging Enabled:", self.logging_rcon_enabled)

    def save_settings(self, server, server_alias, admin_port, password, logging_enabled, logging_chat_enabled,
                      logging_console_enabled, logging_clientinfo_enabled, logging_rcon_enabled):
        # Update configuration settings
        filename = 'OpenTTDAdmin.conf'
        config = configparser.ConfigParser()
        config.read(filename)
        config['OpenTTDAdmin']['server'] = server
        config['OpenTTDAdmin']['server_alias'] = server_alias  # Save server_alias
        config['OpenTTDAdmin']['admin_port'] = str(admin_port)
        config['OpenTTDAdmin']['password'] = password
        config['OpenTTDAdmin']['logging_enabled'] = str(logging_enabled)
        config['OpenTTDAdmin']['logging_chat_enabled'] = str(logging_chat_enabled)
        config['OpenTTDAdmin']['logging_console_enabled'] = str(logging_console_enabled)
        config['OpenTTDAdmin']['logging_clientinfo_enabled'] = str(logging_clientinfo_enabled)
        config['OpenTTDAdmin']['logging_rcon_enabled'] = str(logging_rcon_enabled)
        # Save changes to the configuration file
        with open(filename, 'w') as configfile:
            config.write(configfile)
        # Print saved settings for debugging
        print("Settings saved - Server:", server, "Alias:", server_alias, "Port:", admin_port, "Password:", password,
              "Logging Enabled:", logging_enabled, "Chat Logging Enabled:", logging_chat_enabled,
              "Console Logging Enabled:", logging_console_enabled,
              "Client Info Logging Enabled:", logging_clientinfo_enabled,
              "Rcon Logging Enabled:", logging_rcon_enabled)
        # Reload settings
        self.load_settings()
        # Restart Admin Thread
        self.restart_admin_thread()

    def on_start(self):
        pass

    def update_clientlist(self):
        try:
            def rcon_send(command: str) -> str:
                response = []
                with Admin(ip=self.server, port=self.admin_port, name="pyOpenTTDAdmin", password="toor") as admin:
                    admin.send_rcon(command)
                    while True:
                        packets = admin.recv()
                        for packet in packets:
                            if isinstance(packet, openttdpacket.RconPacket):
                                response.append(packet.response)
                            elif isinstance(packet, openttdpacket.RconEndPacket):
                                return "\n".join(response).strip()

            raw_output = rcon_send('clients')
            print("Raw Output:\n", raw_output)
            client_dict = self.process_clients_output(raw_output)
            print("\nProcessed Clients Dictionary:\n", client_dict)
            self.update_data_and_list(client_dict)
        except:
            pass


    def process_clients_output(self, output: str) -> dict:
        """
        Processes the output from the RCON 'clients' command and structures it into a dictionary.

        Args:
            output (str): The raw output from the 'clients' command.

        Returns:
            dict: A dictionary with structured client information in the expected format.
        """
        clients_dict = {}
        client_lines = output.split('\n')

        for i, line in enumerate(client_lines):
            if 'server' in line:
                continue  # Skip the server entry

            # Extract client details
            parts = line.split()
            print(parts)
            client_id = parts[1].strip('#')  # Extract the client ID
            client_name = parts[3].strip("'")  # Extract the client name
            company = parts[6]  # Extract the company number
            client_ip = parts[-1]  # Extract the IP address

            # Create dictionary entry with the expected structure
            clients_dict[f"Client {client_id}"] = {
                "line1": f"Name: {client_name}",
                "line2": f"Company: {company}",
                "line3": f"IP: {client_ip}"
            }

        return clients_dict

    def update_data_and_list(self, new_data_dict):
        # Update the internal data dictionary
        self.data = new_data_dict

        # Call populate_list to refresh the UI with the updated data
        self.populate_list()

    def populate_list(self, *args):
        client_list = self.root.ids.client_list
        client_list.clear_widgets()

        for key, value in self.data.items():
            list_item = ThreeLineListItem(
                text=key,
                secondary_text=value["line1"],
                tertiary_text=f"{value['line2']}\n{value['line3']}"
            )
            list_item.bind(on_release=lambda instance, k=key: self.client_menu(instance, k))
            client_list.add_widget(list_item)

    def client_menu(self, instance, client_key):
        menu_items = [
            {
                "text": "Kick",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.menu_action("kick", client_key),
            },
            {
                "text": "Ban",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.menu_action("ban", client_key),
            },
            {
                "text": "Delete Company",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.menu_action("delete_company", client_key),
            },
        ]

        self.menu = MDDropdownMenu(
            caller=instance,
            items=menu_items,
            width=dp(160),  # Adjust the width as necessary
        )

        self.menu.open()



    def menu_action(self, action, client_key):
        self.menu.dismiss()
        # Regex pattern to capture numbers
        pattern = re.compile(r'\d+')
        # Find all numbers in client_key
        numbers = pattern.findall(client_key)
        # Join the numbers list into a single string (if there are multiple numbers)
        client_id = ''.join(numbers)

        if action == "kick":
            self.send_to_admin_port(message=f'kick {client_id}', send_type='rcon')
        elif action == "ban":
            self.send_to_admin_port(message=f'ban {client_id}', send_type='rcon')
        elif action == "delete_company":
            pass

    def restart_admin_thread(self):
        # Stop the admin thread if it's running
        if hasattr(self, 'admin_thread') and self.admin_thread.is_alive():
            self.stop_admin_thread()
        # Start the admin thread again
        threading.Thread(target=self.start_admin).start()

    def start_admin(self):
        try:
            # Instantiate the Admin class and establish connection to the server
            with Admin(ip=self.server, port=self.admin_port, name=f"{BOT_NAME} Listener", password=self.password) as admin:
                # Subscribe to receive date updates and set the frequency for updates
                if self.logging_console_enabled:
                    admin.send_subscribe(AdminUpdateType.CONSOLE)
                admin.send_subscribe(AdminUpdateType.CHAT)
                admin.send_subscribe(AdminUpdateType.CMD_LOGGING)
                if self.logging_clientinfo_enabled:
                    admin.send_subscribe(AdminUpdateType.CLIENT_INFO)
                admin.send_subscribe(AdminUpdateType.DATE, AdminUpdateFrequency.ANUALLY)
                # Keep the connection open and print incoming date packets
                while True:
                    # Receive packets from the server
                    packets = admin.recv()
                    for packet in packets:
                        # Update UI in the main thread
                        Clock.schedule_once(lambda dt, p=packet: self.update_ui(p))
        except:
            pass

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

    def update_ui_on_main_thread(self, packet):
        """
        Update the UI on the main thread with packet data.

        Args:
            packet: The packet data to update the UI with.
        """
        if packet:
            if isinstance(packet, openttdpacket.ConsolePacket):
                if '[All]' in packet.message:
                    packet = str(packet.message).replace('[All] ', '')
                    print(f'Chat Packet on ui_on_main_thread: {packet}')
                    self.update_ui_with_chat_message(packet)
            if isinstance(packet, openttdpacket.WelcomePacket):
                server_name = packet.server_name
                map_name = packet.map_name
                seed = packet.seed
                version = packet.version
                mapwidth = packet.mapwidth
                landscape = packet.landscape
                mapheight = packet.mapheight
                startdate = packet.startdate
                # Update the label_main_header text
                main_header_label1 = self.root.ids.label_main_header1
                main_header_label2 = self.root.ids.label_main_header2
                main_header_label3 = self.root.ids.label_main_header3
                main_header_label1.text = f"[color=#000000][size=45][b]{self.server_alias} V: {version}[/b][/size][/color]\r\n"
                main_header_label2.text = f"[color=#000000][size=35][b]Map Size: {map_name} {mapwidth}X{mapheight} Start Date: {startdate}[/b][/size][/color]"

            else:
                if self.logging_enabled:
                    if isinstance(packet, openttdpacket.ConsolePacket):
                        self.update_ui_with_log_message(packet.message)
                    if isinstance(packet, openttdpacket.ClientInfoPacket):
                        self.update_ui_with_log_message(str(packet))
                    if isinstance(packet, openttdpacket.RconPacket):
                        if self.logging_rcon_enabled:
                            self.update_ui_with_log_message(packet.response)
                    if isinstance(packet, openttdpacket.CmdLoggingPacket):
                        self.update_ui_with_log_message(str(packet))
        else:
            # Ensure that the ScrollView stays at the bottom even when packet is empty
            log_message_list = self.root.ids.log_message_list
            log_message_list.parent.scroll_y = 1

    def update_ui_with_chat_message(self, message, is_sent=False):
        """
        Update the UI with a chat message.

        Args:
            message: The chat message packet to display in the UI.
            is_sent: Boolean indicating whether the message is sent by the user.
        """
        # Add a new item to the chat message list
        chat_message_list = self.root.ids.chat_message_list

        try:
            chat_message_list.add_widget(OneLineListItem(text=message.message))
        except AttributeError:  # Catch the AttributeError if message doesn't have 'message' attribute
            chat_message_list.add_widget(OneLineListItem(text=message))

        # Scroll to the bottom if the message is sent, otherwise maintain the current position
        if is_sent:
            Clock.schedule_once(lambda dt: self.scroll_chat_view_to_bottom())
        else:
            chat_message_list.parent.scroll_y = 0

    def send_chat_message(self, message):
        """
        Send a chat message to the OpenTTD server and update the chat scroll view.

        Args:
            message: The chat message to send.
        """

        # Send the chat message to the OpenTTD server
        self.send_to_admin_port(message=message, send_type='global')

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


if __name__ == '__main__':
    app = MainApp()
    app.run()



'''
class MainApp(MDApp):
    # Existing code...

    def update_data_and_list(self, new_data_dict):
        # Update the internal data dictionary
        self.data = new_data_dict

        # Call populate_list to refresh the UI with the updated data
        self.populate_list()

    def populate_list(self, *args):
        client_list = self.root.ids.client_list
        client_list.clear_widgets()
        for key, value in self.data.items():
            client_list.add_widget(
                ThreeLineListItem(
                    text=key,
                    secondary_text=value["line1"],
                    tertiary_text=f"{value['line2']}\n{value['line3']}"
                )
            )

# Example of using the update_data_and_list function
if __name__ == '__main__':
    app = MainApp()
    # Define new data to update the list
    new_data_dict = {
        "New Item 1": {
            "line1": "New Detail 1 Line 1",
            "line2": "New Detail 1 Line 2",
            "line3": "New Detail 1 Line 3"
        },
        "New Item 2": {
            "line1": "New Detail 2 Line 1",
            "line2": "New Detail 2 Line 2",
            "line3": "New Detail 2 Line 3"
        },
        # Add more items as needed
    }
    # Call the update function
    app.update_data_and_list(new_data_dict)
    app.run()
    '''