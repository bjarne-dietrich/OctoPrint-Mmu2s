import datetime
import termios
import threading
import time
import uuid
from enum import Enum
from typing import List

import flask
import octoprint.plugin
import serial
from serial.tools.list_ports import comports

# (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.


class CommandState(Enum):
    Created = 0
    Scheduled = 1
    Running = 2
    Error = 3
    Success = 4


class CommandHandle:
    __uuid: uuid.uuid4()
    __command: bytes
    __dateCreated: datetime.datetime
    __dateStarted: datetime.datetime
    __dateFinished: datetime.datetime

    __state = CommandState

    @property
    def get_state(self):
        return self.__state

    def __init__(self, cmd: bytes):
        self.__uuid = uuid.uuid4()
        self.__command = cmd
        self.__dateCreated = datetime.datetime.now()
        self.__dateStarted = datetime.datetime.fromtimestamp(0)
        self.__dateFinished = datetime.datetime.fromtimestamp(0)


class MMU2S:
    __ser: serial.Serial
    __is_waiting: bool
    __is_connected: bool = False

    __comm_loop_thread: threading.Thread
    __heart_loop_thread: threading.Thread

    __port_list: List = []

    __command_queue: List[CommandHandle] = []

    __old_command_queue: List[CommandHandle] = []

    def comm_loop(self):
        try:
            print("Entering command loop.")
            while True:
                if len(self.__command_queue) == 0:
                    self.__ser.flushInput()
                    print(datetime.datetime.now(), "Sending S0...", end="")
                    self.__ser.write(b"S0\n")
                    line = self.__ser.readline()
                    if line.endswith(b"ok\n"):
                        print(line)

                else:
                    cmd = self.__command_queue[0]
                    self.__command_queue.pop(0)
                    self.__ser.flushInput()
                    print(datetime.datetime.now(), "Sending", cmd, "...", end="")
                    self.__ser.write(cmd)
                    line = self.__ser.readline()
                    if line.endswith(b"ok\n"):
                        print(line)

                for _i in range(1, 50):
                    if len(self.__command_queue) > 0:
                        break
                    time.sleep(0.01)

        except termios.error:
            self.__is_connected = False
            print("Connection broke...")

    def __init__(self, port: str = ""):
        self.__ser = serial.Serial()
        print(self.getPorts())
        if port != "":
            self.connect(port)

    def schedule_command(self, cmd: bytes):
        handle = CommandHandle(cmd)
        self.__command_queue.append(handle)
        return handle

    def __heartbeat_loop(self):
        while True:
            while self.__is_connected:
                # self.schedule_command(Command.ReturnOk)

                time.sleep(0.5)

            time.sleep(0.5)

    def connect(self, port=""):
        print("Starting connection.")
        if self.__is_connected:
            print("MMU seems to be already connected.")
            return
        if port != "":
            self.__ser.setPort(port)
        try:
            self.__ser.open()
            self.__is_connected = True
            self.__comm_loop_thread = threading.Thread(target=self.comm_loop)
            self.__comm_loop_thread.start()
        except serial.SerialException:
            print("An Error occured, connection to MMU was not possible.")
            pass

    def getPorts(self):
        ports = comports()
        port_names = []
        for port in ports:
            port_names.append(port.name)
        self.__port_list = port_names
        return port_names

    def waitForRelease(self):
        self.__is_waiting = True
        start = datetime.datetime.now()
        self.__ser.timeout = 90

        while datetime.datetime.now() < (start + datetime.timedelta(seconds=90)):
            r = self.__ser.readline()
            print("waiting..", r)
            if r == b"ok\n":
                self.__ser.flush()
                self.__is_waiting = False
                return 0
        return -1

    def isAvailable(self):
        if self.__ser.is_open:
            if not self.__is_waiting:
                return True
        return False


class Mmu2sPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SimpleApiPlugin,
):

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            timeout=60,
            stealth_config=dict(
                has_stealth=True,
                stealth_on_command="M1",
                stealth_off_command="M0",
            ),
            command_config=dict(
                change_filament="T",
                load_filament="L",
                cut_filament="K",
                submit_with_newline=True,
                submit_with_carriage_return=True,
            ),
            channel_config=dict(
                count=5,
                first_channel_index=0,
            ),
            heartbeat_config=dict(
                use_heartbeat=True,
                heartbeat_command="S0",
                heartbeat_interval=1000,
            ),
            communication_config=dict(reply_on_success="ok\n"),
        )

    # ~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/mmu2s.js"],
            "css": ["css/mmu2s.css"],
            "less": ["less/mmu2s.less"],
        }

    def gcode_queuing_handler(
        self,
        comm_instance,
        phase,
        cmd,
        cmd_type,
        gcode,
        subcode=None,
        tags=None,
        *args,
        **kwargs
    ):
        if cmd.startswith("T"):
            print(cmd)
            self._printer.set_job_on_hold(True)
            number = 0
            if cmd == "T0":
                number = 0
            elif cmd == "T1":
                number = 1
            elif cmd == "T2":
                number = 2
            elif cmd == "T3":
                number = 3
            elif cmd == "T4":
                number = 4
            else:
                return Exception
            self._logger.info("got", cmd, number)
            # t1 = threading.Thread(target=self.mmu2s.changeFilament, args=(number,))
            # t1.start()
            # t2 = threading.Thread(target=self.resumePrint, args=(t1,))
            # t2.start()
            return ""

    def sent_callback(
        self,
        comm_instance,
        phase,
        cmd,
        cmd_type,
        gcode,
        subcode=None,
        tags=None,
        *args,
        **kwargs
    ):
        if gcode.startswith("T"):
            print("Code... :", gcode)
        return None

    def get_api_commands(self):
        return dict(
            change=["id"], load=["id"], stealth=["value"], connect=["port"], get_ports=[]
        )

    def on_after_startup(self):
        self.mmu2s = MMU2S("")
        self._logger.info("Hello World! (more: %s)" % self._settings.get(["url"]))

    def get_template_configs(self):
        return [
            dict(type="tab", custom_bindings=True, template="mmu2s4everyone_tab.jinja2"),
            dict(
                type="settings",
                custom_bindings=True,
                template="mmu2s4everyone_settings.jinja2",
            ),
            dict(
                type="sidebar",
                icon="rocket",
                custom_bindings=True,
                template="mmu2s4everyone_sidebar.jinja2",
            ),
        ]

    def get_termination(self):
        cr = self._settings.get(["command_config", "submit_with_carriage_return"])
        nl = self._settings.get(["command_config", "submit_with_newline"])

        resp = ""
        if cr:
            resp += "\r"
        if nl:
            resp += "\n"

        return resp

    def on_api_command(self, command, data):
        self._logger.info(data)
        if command == "change":
            char = self._settings.get(["command_config", "change_filament"])
            slot_id = data["id"]
            end = self.get_termination()

            cmd = bytes(str(char) + str(slot_id) + str(end), encoding="utf8")
            self._logger.info(cmd)
            self.mmu2s.schedule_command(cmd)

        elif command == "load":
            char = self._settings.get(["command_config", "load_filament"])
            slot_id = data["id"]
            end = self.get_termination()

            cmd = bytes(str(char) + str(slot_id) + str(end), encoding="utf8")
            self._logger.info(cmd)
            self.mmu2s.schedule_command(cmd)
        elif command == "stealth":
            if data["value"] == 1:
                self.mmu2s.stealthMode(True)
            else:
                self.mmu2s.stealthMode(False)
            self._logger.info(data)
        elif command == "unload":
            self._logger.info(data)
        elif command == "eject":
            self._logger.info(data)
        elif command == "recover":
            self._logger.info(data)
        elif command == "connect":
            self._logger.info(data)
            self.mmu2s.connect()
        elif command == "get_ports":
            ports = self.mmu2s.getPorts()
            return flask.jsonify(ports=ports)
        else:
            self._logger.info("No command.")

    def on_api_get(self, request):
        return flask.jsonify(foo="bar")

    def on_settings_save(self, data):
        self._logger.info("Saving...1.")
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

    # ~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "mmu2s": {
                "displayName": "Mmu2s Plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "bjarne-dietrich",
                "repo": "OctoPrint-Mmu2s",
                "current": self._plugin_version,
                # update method: pip
                "pip": "https://github.com/bjarne-dietrich/OctoPrint-Mmu2s/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Mmu2s Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Mmu2sPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.gcode_queuing_handler,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.sent_callback,
    }
