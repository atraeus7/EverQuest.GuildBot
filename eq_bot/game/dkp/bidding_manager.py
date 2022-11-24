from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.config import get_config
from game.dkp.bid_message_parser import parse_bid_message
from game.dkp.entities.bid_message import BidMessageType

RESTRICT_TO_GUILDIES = get_config('dkp.bidding.restrict_to_guildies', True)

MAX_GUILD_MESSAGE_LENGTH = 508

class Bid:
    def __init__(self):
        pass



class BiddingManager:
    def __init__(self, eq_window: EverQuestWindow, guild_tracker: GuildTracker):
        self._eq_window = eq_window
        self._guild_tracker = guild_tracker
        self._next_round = {}
        self._round_enabled = False

    def handle_tell_message(self, tell_message):
        print('TELL!', tell_message)
        # Do not proceed if restrict to guildies enabled and is not a guild member
        if RESTRICT_TO_GUILDIES and not self._guild_tracker.is_a_member(tell_message.from_player):
            # TODO: Log a warning
            return
        print('GONNA PARSE')
        bid_message = parse_bid_message(tell_message)

        # TODO: Check if allowed
        #if tell_message.from_player

        if bid_message.message_type == BidMessageType.ENQUEUE_BID_ITEMS:
            if len(bid_message.items) == 0:
                print('Received enqueue bid message, but no items were enqueued.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'You must provide a list of items to enqueue, separated by ";"')
                return

            for item in bid_message.items:
                self._next_round[item] = {}
            print('BID MESSAGE PARSED!')
        if bid_message.message_type == BidMessageType.START_ROUND:
            next_round_keys = list(self._next_round.keys())
            if len(next_round_keys) == 0:
                print('Received start round message, but no items are in the next round.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'No items are currently queued for bidding. The round was not started.')
                return
            
            self._round_enabled = True

            messages_to_send = []
            guild_message = f'BIDDING CURRENTLY OPEN ON: {next_round_keys[0]}'

            for item in next_round_keys[1:]:
                if len(guild_message) + len(item) + 2 <= MAX_GUILD_MESSAGE_LENGTH:
                    guild_message += f', {item}'
                else:
                    messages_to_send.append(guild_message)

                    # start the next message with the current item
                    guild_message = item
            
            messages_to_send.append(guild_message)

            for message in messages_to_send:
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    message)

        print('ITEMS IN NEXT ROUND', self._next_round)
