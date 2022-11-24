from datetime import datetime
from game.logging.entities.log_message import LogMessage
from game.dkp.entities.bid_message import BidMessage, EnqueueBidItemsMessage, BidMessageType

ENQUEUE_ITEMS_CMD = '#enqueue-items:'
START_ROUND_CMD = '#start-round'

def parse_bid_message(tell_message: LogMessage):
    print('TELL MESSAGE', tell_message, tell_message.inner_message.strip().startswith(ENQUEUE_ITEMS_CMD))
    if tell_message.inner_message.startswith(ENQUEUE_ITEMS_CMD):
        return EnqueueBidItemsMessage(
            timestamp = tell_message.timestamp,
            full_message = tell_message.inner_message,
            from_player = tell_message.from_player,
            message_type = BidMessageType.ENQUEUE_BID_ITEMS,
            items = [
                item.strip() for item in
                filter(None, tell_message.inner_message.lstrip(ENQUEUE_ITEMS_CMD).split(';'))
            ]
        )
    if tell_message.inner_message.startswith(START_ROUND_CMD):
        return BidMessage(
            timestamp = tell_message.timestamp,
            full_message = tell_message.inner_message,
            from_player = tell_message.from_player,
            message_type = BidMessageType.START_ROUND
        )

    return None
