import time
from datetime import timedelta
from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.input import has_recent_input, get_timedelta_since_input
from game.logging.entities.log_message import LogMessageType
from game.buff.buff_manager import BuffManager
from utils.config import get_config
from integrations.discord import send_bot_started_message, send_bot_stopped_message, send_bot_crashed_message

TICK_LENGTH = .1


class Bot:
    def __init__(self):
        self._crash_notification_sent = False

    def _on_start(self):
        print('Bot has been started.')
        if get_config('monitoring.notifications.notify_on_start'):
            send_bot_started_message()

    def _on_stop(self):
        print('Bot has been stopped.')
        if get_config('monitoring.notifications.notify_on_stop') and not self._crash_notification_sent:
            send_bot_stopped_message()

    def _on_crash(self, e: Exception):
        print(f'Bot has crashed: {e}')
        if get_config('monitoring.notifications.notify_on_crash'):
            send_bot_crashed_message()
            self._crash_notification_sent = True

    def _run(self):
        window = EverQuestWindow()
        player_log_reader = window.get_player_log_reader()

        guild_tracker = GuildTracker(window)

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

    def start(self):
        try:
            self._on_start()
            self._run()
        except Exception as e:
            self._on_crash(e)
        finally:
            self._on_stop()
