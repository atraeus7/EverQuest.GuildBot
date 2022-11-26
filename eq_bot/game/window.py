import re
import time
import win32gui
from queue import Queue
from threading import Thread
from pynput.keyboard import Key
from dataclasses import dataclass
from game.entities.player import CurrentPlayer

from game.logging.log_reader import EverQuestLogReader
from game.logging.entities.log_message import LogMessageType

from utils.output import send_text, send_multiple_keys, send_key
from utils.config import get_config
from utils.file import get_latest_modified_file


EVERQUEST_ROOT_FOLDER=get_config('game.root_folder').rstrip("\\")


class EverQuestWindow(Thread):
    def __init__(self, daemon: bool = False):
        super().__init__(daemon=daemon)
        self.player = CurrentPlayer(
            name=get_config('player.name'),
            server=get_config('player.server'),
            guild=get_config('player.guild'))

        self._queue = Queue()

        if get_config('player.autodetect'):
            if not self.player.name or not self.player.server:
                self._lookup_current_player()
            if not self.player.guild:
                self._lookup_current_guild()

    # Run this as a daemon so the thread will be cleaned up if the process is destroyed
    def run(self) -> None:
        while True:
            handler = self._queue.get(block=True)
            handler()

    def handle_window_action(self, action):
        self._queue.put(action)

    def _lookup(self):
        return win32gui.FindWindow(None, "EverQuest")

    def activate(self):
        win32gui.SetForegroundWindow(self._lookup())
        time.sleep(.5)

    def clear_chat(self):
        send_multiple_keys([Key.shift, Key.delete])
        send_key(Key.enter)

    def send_chat_message(self, message):
        self.clear_chat()
        send_text(message)
        send_key(Key.enter)

    def guild_dump(self, outputfile):
        self.activate()
        return self.send_chat_message(f"/outputfile guild {outputfile}")

    def get_player_log_reader(self):
        return EverQuestLogReader(f'{EVERQUEST_ROOT_FOLDER}\\Logs', self.player, daemon=True)

    def target(self, target):
        self.send_chat_message(f"/target {target}")

    def cast_spell(self, target, spell_name, spell_slot):
        self.send_chat_message(f"/cast {spell_slot}")

    def sit(self):
        self.send_chat_message("/sit")

    def _lookup_current_player(self):
        self.activate()
        self.send_chat_message("/log on")
        print('Looking up recently modified log file.')

        latest_file = get_latest_modified_file(f"{EVERQUEST_ROOT_FOLDER}\\Logs\\eqlog_*")
        if not latest_file:
            raise ValueError('Failed to find any log files. Is EverQuest running?')

        search_result = re.search(r"eqlog_(.*)_(.*).txt", latest_file.split('\\')[-1])
        if not search_result or len(search_result.groups()) < 2:
            raise ValueError('Failed to parse player name and/or server from log file.')

        if not self.player.name:
            self.player.name = search_result.group(1)
        if not self.player.server:
            self.player.server = search_result.group(2).capitalize()

    def _update_current_guild(self, message):
        # TODO: Handle during parsing with concrete message classes
        search_result = re.search(r"is the rank of .* in (.*).$", message.full_message)
        self.player.guild = search_result.group(1)

    def _lookup_current_guild(self):
        log_reader = self.get_player_log_reader()
        log_reader.observe_messages(
            LogMessageType.GUILD_STAT,
            self._update_current_guild)

        self.activate()
        self.send_chat_message(f"/target {self.player.name}")
        self.send_chat_message(f"/guildstat")
        log_reader.process_new_messages()

        while not self.player.guild:
            log_reader.process_new_messages()
            print('Guild name has not been found. Waiting...')
            time.sleep(1)

        log_reader.remove_observation(
            LogMessageType.GUILD_STAT,
            self._update_current_guild)
