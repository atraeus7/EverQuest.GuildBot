from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from enum import Enum

class LogMessageType(Enum):
    UNKNOWN = 'Unknown'
    TELL_RECEIVE = 'Receive Tell'
    TELL_SEND = 'Send Tell'
    GUILD = 'Guild'
    CHANNEL = 'Channel'
    AUCTION = 'Auction'
    OUT_OF_CHARACTER = 'Out of Character'
    SAY = 'Say'
    GROUP = 'Group'
    SHOUT = 'Shout'
    GUILD_STAT = 'Guild Stat'

@dataclass
class LogMessage:
    timestamp: datetime
    full_message: str
    inner_message: str
    from_character: str
    to: str
    message_type: LogMessageType

    def print(self):
        print(vars(self))
