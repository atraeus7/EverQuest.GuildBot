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

TICK_LENGTH = .1

window = EverQuestWindow()
player_log_reader = window.get_player_log_reader()

opendkp = OpenDkp()
guild_tracker = GuildTracker(window, opendkp)

if get_config('dkp.bidding.enabled'):
    bidding_manager = BiddingManager(window, guild_tracker, opendkp)
    player_log_reader.observe_messages(LogMessageType.TELL_RECEIVE, bidding_manager.handle_tell_message)

# Configure log message subscriptions
if get_config('buffing.enabled'):
    buff_manager = BuffManager(window, guild_tracker)
    player_log_reader.observe_messages(LogMessageType.TELL_RECEIVE, buff_manager.handle_tell_message)

# Execute services which need to be activated periodically
while(True):
    if not has_recent_input():
        if get_config('log_parsing.enabled', True):
            player_log_reader.process_new_messages()
        if get_config('guild_tracking.enabled'):
            guild_tracker.update_status()
    time.sleep(TICK_LENGTH)
