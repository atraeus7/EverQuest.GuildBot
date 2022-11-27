from dataclasses import dataclass
from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.config import get_config
from game.dkp.bid_message_parser import parse_bid_message
from game.dkp.entities.bid_message import BidMessageType
from game.dkp.bidding_round import BiddingRound
from integrations.opendkp.opendkp import OpenDkp

RESTRICT_TO_GUILDIES = get_config('dkp.bidding.restrict_to_guildies', True)

DEFAULT_ROUND_LENGTH = 180

class BiddingManager:
    def __init__(self, eq_window: EverQuestWindow, guild_tracker: GuildTracker, opendkp: OpenDkp):
        self._eq_window = eq_window
        self._opendkp = opendkp
        self._guild_tracker = guild_tracker
        self._bidding_round = BiddingRound()

    def handle_tell_message(self, tell_message):
        # Do not proceed if restrict to guildies enabled and is not a guild member
        if RESTRICT_TO_GUILDIES and not self._guild_tracker.is_a_member(tell_message.from_character):
            # TODO: Log a warning
            return

        bid_message = parse_bid_message(tell_message)

        if not bid_message:
            return

        if bid_message.message_type == BidMessageType.ENQUEUE_BID_ITEMS:
            if len(bid_message.items) == 0:
                print('Received enqueue bid message, but no items were enqueued.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'You must provide a list of items to enqueue, separated by ";"')
                return

            self._bidding_round.enqueue_items(bid_message.items)

            print(f'{bid_message.from_player} has enqueued the following items: {bid_message.items}')

        if bid_message.message_type == BidMessageType.START_ROUND:
            if self._bidding_round.is_enabled():
                print(f'{bid_message.from_player} attempted to start a round of bidding, but a round is currently active.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'A round of bidding is already active. You cannot start a new round.')
                return

            if self._bidding_round.has_items():
                print(f'{bid_message.from_player} attempted to start a round of bidding, but no items are in the next round.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'No items are currently queued for bidding. The round has not been started.')
                return
            
            self._bidding_round.start(bid_message.length or DEFAULT_ROUND_LENGTH)

            for message in self._bidding_round.build_round_messages():
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    message)

        if bid_message.message_type == BidMessageType.BID_ON_ITEM:
            try:
                self._bidding_round.bid_on_item(
                    bid_message.from_player,
                    bid_message.item,
                    bid_message.amount,
                    bid_message.is_box_bid,
                    bid_message.is_alt_bid
                )
            except KeyError:
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    f'{bid_message.item} is not being bid on. Did you spell the name correctly?')

            print(f'{bid_message.from_player} has bid {bid_message.amount} on {bid_message.item}')

        if bid_message.message_type == BidMessageType.BEGIN_RAID:
            self._opendkp.create_raid(bid_message.raid_name)
