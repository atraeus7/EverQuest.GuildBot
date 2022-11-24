import time
from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.config import get_config, get_from_path

# TODO: Validate configuration
BUFFING_SPELLS = get_config('buffing.spells')
RESTRICT_TO_GUILDIES = get_config('buffing.restrict_to_guildies')

class BuffManager:
    def __init__(self, eq_window: EverQuestWindow, guild_tracker: GuildTracker):
        self._eq_window = eq_window
        self._guild_tracker = guild_tracker

    def handle_tell_message(self, tell_message):
        # TODO: Enqueue and process messages when window is not busy given that messages will come in asynchronously

        # Do not proceed if restrict to guildies enabled and is not a guild member
        if RESTRICT_TO_GUILDIES and not self._guild_tracker.is_a_member(tell_message.from_player):
            # TODO: Log a warning
            return
        
        spells_to_cast = []

        for spell_name in BUFFING_SPELLS:
            if spell_name.lower() in tell_message.inner_message.lower():
                spells_to_cast.append(spell_name)
    
        if len(spells_to_cast) == 0:
            return

        self._eq_window.activate()
        # TODO: Check if player was not found in zone and inform them
        self._eq_window.target(tell_message.from_player)
        self._eq_window.send_chat_message(f"/tell {tell_message.from_player} Incoming")
        # TODO: Check if player was too far and inform them

        for spell_name in spells_to_cast:
            spell_config = BUFFING_SPELLS[spell_name]
            self._eq_window.cast_spell(tell_message.from_player, spell_name, spell_config['spell_slot'])
            recast_time = spell_config.get('recast_time', 1)
            time.sleep(spell_config['cast_time'] + recast_time)

        self._eq_window.sit()
