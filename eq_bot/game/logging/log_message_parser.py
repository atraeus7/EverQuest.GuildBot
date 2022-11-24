import re
from datetime import datetime
from game.logging.entities.log_message import LogMessage, LogMessageType

COMMUNICATION_MESSAGES = [
    LogMessageType.AUCTION,
    LogMessageType.CHANNEL,
    LogMessageType.GROUP,
    LogMessageType.GUILD,
    LogMessageType.OUT_OF_CHARACTER,
    LogMessageType.SAY,
    LogMessageType.SHOUT,
    LogMessageType.TELL_SEND,
    LogMessageType.TELL_RECEIVE
]

def _parse_timestamp(input):
    return datetime.strptime(input, "[%a %b %d %H:%M:%S %Y]")

# TODO: Simplify with a regex->LogMessageType map
def _parse_message_type(full_message, message_split):
    if message_split[1] == 'tells':
        # e.g. General:3
        if len(message_split[2].split(':')) > 1:
            return LogMessageType.CHANNEL
        elif message_split[2] == 'you,':
            return LogMessageType.TELL_RECEIVE
        elif message_split[2] == 'the':
            if message_split[3] == 'group,':
                return LogMessageType.GROUP
            elif message_split[3] == 'guild,':
                return LogMessageType.GUILD
    elif message_split[1] == 'says':
        if ' '.join(message_split[2:]).startswith('out of character,'):
            return LogMessageType.OUT_OF_CHARACTER
    elif message_split[1] == 'auctions,':
        return LogMessageType.AUCTION
    elif message_split[1] == 'shouts,':
        return LogMessageType.SHOUT
    elif message_split[1] == 'says,':
        if len(message_split) == 3:
            return LogMessageType.SAY
    elif full_message.startswith('You tell'):
        return LogMessageType.TELL_SEND
    elif ' '.join(message_split[1:]).startswith('is the rank of'):
        return LogMessageType.GUILD_STAT
    return LogMessageType.UNKNOWN

def _parse_message_to(full_message, message_split, message_type):
    if message_type not in [LogMessageType.CHANNEL, LogMessageType.TELL_RECEIVE, LogMessageType.TELL_SEND]:
        return
    
    if message_type == LogMessageType.CHANNEL:
        return message_split[2].split(':')[0]
    elif message_type == LogMessageType.TELL_RECEIVE or message_type == LogMessageType.TELL_SEND:
        return message_split[2].rstrip(',').capitalize()
    # TODO: Log warning

def _parse_inner_message(full_message):
    result = re.search(", '(.*)'$", full_message)
    if not result or len(result.groups()) == 0:
        raise ValueError('Failed to parse inner message.')
    return result.group(1)

def create_log_message(raw_text):
    full_message = raw_text[27:].rstrip('\n')
    message_split = full_message.split(' ')
    message_type = _parse_message_type(full_message, message_split)
    is_communication_message = message_type in COMMUNICATION_MESSAGES

    return LogMessage(
        timestamp = _parse_timestamp(raw_text[0:26]),
        from_character = message_split[0] if is_communication_message else None,
        to = _parse_message_to(full_message, message_split, message_type),
        # remove the surrounding quotes from player message
        # e.g. Soandso tells you, 'this is the inner message'
        inner_message = _parse_inner_message(full_message) if is_communication_message else None,
        full_message = full_message,
        message_type = message_type)
