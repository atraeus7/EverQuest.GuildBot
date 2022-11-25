from typing import List

from game.dkp.entities.biddable_item import BiddableItem
from game.dkp.entities.player_bid import PlayerBid

MAX_GUILD_MESSAGE_LENGTH = 508
ITEM_JOIN_STR = ' | '

class BiddingRound:
    def __init__(self):
        self._items = []
        self._enabled = False
        self._length = 0
    
    def start(self, length) -> None:
        self._enabled = True
        self._length = length
    
    def add_items(self, items) -> None:
        self._items.extend(items)
    
    def has_items(self) -> bool:
        return len(self._items) >= 0

    def is_enabled(self) -> bool:
        return self._enabled

    def build_round_messages(self) -> List[str]:
        messages_to_send = []
        guild_message = f'BIDDING CURRENTLY OPEN ON: {self._items[0].print()}'

        for item in self._items[1:]:
            item_message = item.print()
            if len(guild_message) + len(item_message) + len(ITEM_JOIN_STR) <= MAX_GUILD_MESSAGE_LENGTH:
                guild_message += f'{ITEM_JOIN_STR}{item_message}'
            else:
                messages_to_send.append(guild_message)

                # start the next message with the current item
                guild_message = item_message

        messages_to_send.append(guild_message)

    def enqueue_items(self, items):
        for item in items:
            existing_item = next((i for i in self._items if i.name == item), None)
            if existing_item:
                existing_item.increase_count()
            else:
                self._items.append(BiddableItem(item))

    def bid_on_item(self, from_player, item, amount, is_box_bid, is_alt_bid):
        biddable_item = next((i for i in self._items if i.name == item), None)
        if not biddable_item:
            raise KeyError(f'{from_player} attempted to bid on an item which was not in the round: {item}')

        existing_bid = next((b for b in biddable_item.bids if b.from_player == from_player), None)
        if existing_bid:
            existing_bid.amount = amount
            existing_bid.is_box_bid = is_box_bid
            existing_bid.is_alt_bid = is_alt_bid
        else:
            biddable_item.bids.append(PlayerBid(
                from_player = from_player,
                amount = amount,
                is_box_bid = is_box_bid,
                is_alt_bid = is_alt_bid
            ))
