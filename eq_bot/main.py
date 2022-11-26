import time
import signal
import sys
from datetime import timedelta
from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.input import has_recent_input, get_timedelta_since_input
from game.logging.entities.log_message import LogMessageType
from game.buff.buff_manager import BuffManager
from utils.config import get_config

def sig_handler(_signo, _stack_frame):
    sys.exit(0)

TICK_LENGTH = .1

window = EverQuestWindow()
player_log_reader = window.get_player_log_reader()

guild_tracker = GuildTracker(window)
signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT, sig_handler)

# Configure log message subscriptions
if get_config('buffing.enabled'):
    buff_manager = BuffManager(window, guild_tracker)
    player_log_reader.observe_messages(LogMessageType.TELL_RECEIVE, buff_manager.handle_tell_message)

# Starts a thread which manages a queue of actions to be performed by the window
window.daemon = True
window.start()

# Starts a thread that continuously monitors the log
if get_config('log_parsing.enabled', True):
    window.get_player_log_reader().daemon = True
    window.get_player_log_reader().start()

# Execute services which need to be activated periodically
while True:
    if not has_recent_input():
        if get_config('guild_tracking.enabled'):
            guild_tracker.update_status()
    time.sleep(TICK_LENGTH)
