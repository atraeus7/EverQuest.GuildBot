import time
from datetime import timedelta
from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.input import has_recent_input, get_timedelta_since_input
from game.logging.entities.log_message import LogMessageType
from game.buff.buff_manager import BuffManager
from game.dkp.bidding_manager import BiddingManager
from integrations.opendkp.opendkp import OpenDkp
from utils.config import get_config


class Bot:
    def __init__(self):
        self._window = EverQuestWindow()
        self._player_log_reader = self._window.get_player_log_reader()
        self._opendkp = OpenDkp()
        self._guild_tracker = GuildTracker(
            self._window,
            self._opendkp)

    def start(self):
        # Starts a thread which manages a queue of actions to be performed by the window
        self._window.start()

        # Configure DKP Bidding Manager
        if get_config('dkp.bidding.enabled'):
            bidding_manager = BiddingManager(
                self._window,
                self._guild_tracker,
                self._opendkp)

            self._player_log_reader.observe_messages(
                LogMessageType.TELL_RECEIVE,
                bidding_manager.handle_tell_message)

        # Configure Buffing Manager
        if get_config('buffing.enabled'):
            buff_manager = BuffManager(
                self._window,
                self._guild_tracker)

            self._player_log_reader.observe_messages(
                LogMessageType.TELL_RECEIVE,
                buff_manager.handle_tell_message)

        # Starts a thread that continuously monitors the log
        if get_config('log_parsing.enabled', True):
            self._player_log_reader.start()

        # Start a thread to continuously track guild members
        if get_config('guild_tracking.enabled'):
            self._guild_tracker.start()
