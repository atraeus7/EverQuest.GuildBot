from datetime import datetime
from game.logging.entities.log_message import LogMessage
from game.dkp.entities.bid_message import BidMessage, EnqueueBidItemsMessage, StartRoundMessage, BidOnItemMessage, BidMessageType

ENQUEUE_ITEMS_CMD = '#enqueue-items'
START_ROUND_CMD = '#start-round'
ITEM_BID_CMD = '#bid'

def parse_bid_message(tell_message: LogMessage):
    if tell_message.inner_message.startswith(ENQUEUE_ITEMS_CMD):
        return EnqueueBidItemsMessage(
            timestamp = tell_message.timestamp,
            full_message = tell_message.inner_message,
            from_player = tell_message.from_player,
            items = [
                item.strip() for item in
                filter(None, tell_message.inner_message.lstrip(ENQUEUE_ITEMS_CMD).split(';'))
            ]
        )
    if tell_message.inner_message.startswith(START_ROUND_CMD):
        return StartRoundMessage(
            timestamp = tell_message.timestamp,
            full_message = tell_message.inner_message,
            from_player = tell_message.from_player
        )
    if tell_message.inner_message.startswith(ITEM_BID_CMD):
        bid_parts = tell_message.inner_message.lstrip(ITEM_BID_CMD).split(':')

        if len(bid_parts) != 2:
            # TODO: Message player
            return

        bid_attributes = bid_parts[1].strip().split(' ')

        amount_str = bid_attributes[0].strip() 
        if not amount_str or not amount_str.isnumeric():
            # TODO: Message player
            return

        return BidOnItemMessage(
            timestamp = tell_message.timestamp,
            full_message = tell_message.inner_message,
            from_player = tell_message.from_player,
            item = bid_parts[0].strip(),
            amount = int(amount_str),
            is_box_bid = 'box' in bid_attributes,
            is_alt_bid = 'alt' in bid_attributes
        )

    return None