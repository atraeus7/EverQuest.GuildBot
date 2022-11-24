from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

from enum import Enum

class BidMessageType(Enum):
    ENQUEUE_BID_ITEMS = 'Qneue Bid Items'
    BID_ON_ITEM = 'Bid On Item'
    START_ROUND = 'Start Round'
    END_ROUND = 'End Round'

@dataclass
class BidMessage:
    timestamp: datetime
    full_message: str
    from_player: str
    message_type: BidMessageType

    def print(self):
        print(vars(self))

@dataclass
class EnqueueBidItemsMessage(BidMessage):
    items: List
