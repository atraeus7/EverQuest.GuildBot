import time
from os.path import exists
from utils.file import move_file
from datetime import datetime
from game.entities.player import CurrentPlayer
from game.logging.entities.log_message import LogMessageType
from game.logging.log_message_parser import create_log_message
from utils.config import get_config
from threading import Thread

PLAYER_LOG_TIMESTAMP_FORMAT='%Y%m%d-%H%M%S'

# TODO: Move to configuration file
MAX_LINES_READ = 100
TICK_LENGTH = .1

class EverQuestLogReader(Thread):

    def __init__(self, log_folder: str, player: CurrentPlayer, daemon: bool = True):
        super().__init__(daemon=daemon)
        self.log_folder = log_folder
        self.player = player
        self.observers = {}
        self._iterator = self._init_iterator()
        
        if get_config('log_parsing.cycle_on_start'):
            self.cycle_player_log()

    # Run this as a daemon so the thread will be cleaned up if the process is destroyed
    def run(self) -> None:
        while True:
            self.process_new_messages()
            time.sleep(TICK_LENGTH)

    def _get_log_filename(self):
        return f'eqlog_{self.player.name}_{self.player.server.lower()}'

    def get_player_log(self, filename=None):
        if not filename:
            filename = self._get_log_filename()
        return f'{self.log_folder}\\{filename}.txt'

    def cycle_player_log(self):
        current_player_log = self.get_player_log()
        if not exists(current_player_log):
            return
        new_filename = f'{self._get_log_filename()}-{datetime.now().strftime(PLAYER_LOG_TIMESTAMP_FORMAT)}'
        move_file(current_player_log, self.get_player_log(new_filename))

    def _init_iterator(self):
        current_player_log = self.get_player_log()
        if not exists(current_player_log):
            return

        iterator = open(current_player_log, 'r')
        # Skip to end
        iterator.seek(0, 2)

        return iterator

    def get_observers(self, message_type: LogMessageType):
        if message_type not in self.observers:
            self.observers[message_type] = []
        return self.observers[message_type]

    def observe_messages(self, message_type: LogMessageType, callback):
        self.get_observers(message_type).append(callback)
    
    def remove_observation(self, message_type: LogMessageType, callback):
        self.get_observers(message_type).remove(callback)

    def _build_new_messages(self, lines_to_read):
        new_messages = []
        while len(new_messages) < lines_to_read:
            next_line = self._iterator.readline()
            if not next_line:
                break
            try:
                new_messages.append(create_log_message(next_line))
            except Exception as e:
                # TODO: Switch to logger.error
                print(f"Failed to process message: {next_line}. Exception: {e}")
        return new_messages

    def process_new_messages(self, lines_to_read=0):
        for message in self._build_new_messages(lines_to_read if lines_to_read > 0 else MAX_LINES_READ):
            for observer_fn in self.get_observers(message.message_type):
                observer_fn(message)
