from dataclasses import dataclass
from game.window import EverQuestWindow
from game.guild.guild_tracker import GuildTracker
from utils.config import get_config
from game.dkp.bid_message_parser import parse_bid_message
from game.dkp.entities.bid_message import BidMessageType

RESTRICT_TO_GUILDIES = get_config('dkp.bidding.restrict_to_guildies', True)

MAX_GUILD_MESSAGE_LENGTH = 508
ITEM_JOIN_STR = ' | '

@dataclass
class Bid:
    from_player: str
    amount: int
    is_box_bid: bool
    is_alt_bid: bool


class BiddableItem:
    def __init__(self, name):
        self.count = 1
        self.name = name
        self.bids = []
    
    def increase_count(self):
        self.count += 1

    def print(self):
        return self.name if self.count == 1 else f'{self.name} x{self.count}'

class BiddingManager:
    def __init__(self, eq_window: EverQuestWindow, guild_tracker: GuildTracker):
        self._eq_window = eq_window
        self._guild_tracker = guild_tracker
        self._next_round_items = []
        self._round_enabled = False

    def handle_tell_message(self, tell_message):
        # Do not proceed if restrict to guildies enabled and is not a guild member
        if RESTRICT_TO_GUILDIES and not self._guild_tracker.is_a_member(tell_message.from_player):
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

            for item in bid_message.items:
                existing_item = next((i for i in self._next_round_items if i.name == item), None)
                if existing_item:
                    existing_item.increase_count()
                else:
                    self._next_round_items.append(BiddableItem(item))

        if bid_message.message_type == BidMessageType.START_ROUND:
            if self._round_enabled:
                print(f'{bid_message.from_player} attempted to start a round of bidding, but a round is currently active.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'A round of bidding is already active. You cannot start a new round.')
                return

            if len(self._next_round_items) == 0:
                print(f'{bid_message.from_player} attempted to start a round of bidding, but no items are in the next round.')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    'No items are currently queued for bidding. The round was not started.')
                return
            
            self._round_enabled = True

            messages_to_send = []
            guild_message = f'BIDDING CURRENTLY OPEN ON: {self._next_round_items[0].print()}'

            for item in self._next_round_items[1:]:
                item_message = item.print()
                if len(guild_message) + len(item_message) + len(ITEM_JOIN_STR) <= MAX_GUILD_MESSAGE_LENGTH:
                    guild_message += f'{ITEM_JOIN_STR}{item_message}'
                else:
                    messages_to_send.append(guild_message)

                    # start the next message with the current item
                    guild_message = item_message
            
            messages_to_send.append(guild_message)

            for message in messages_to_send:
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    message)

        if bid_message.message_type == BidMessageType.BID_ON_ITEM:
            item = next((i for i in self._next_round_items if i.name == bid_message.item), None)
            if not item:
                print(f'{bid_message.from_player} attempted to bid on an item which was not in the round: {bid_message.item}')
                self._eq_window.send_tell_message(
                    bid_message.from_player,
                    f'{bid_message.item} is not being bid on. Did you spell the name correctly?')
                pass

            existing_bid = next((b for b in item.bids if b.from_player == bid_message.from_player), None)
            if existing_bid:
                existing_bid.amount = bid_message.amount
                existing_bid.is_box_bid = bid_message.is_box_bid
                existing_bid.is_alt_bid = bid_message.is_alt_bid
            else:
                item.bids.append(Bid(
                    from_player = bid_message.from_player,
                    amount = bid_message.amount,
                    is_box_bid = bid_message.is_box_bid,
                    is_alt_bid = bid_message.is_alt_bid
                ))

            print(f'{bid_message.from_player} has bid {bid_message.amount} on {item.name}')
