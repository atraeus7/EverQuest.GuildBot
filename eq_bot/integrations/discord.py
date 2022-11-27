from discord import Webhook, RequestsWebhookAdapter, Embed, Color
from utils.config import get_secret

from enum import Enum

WEBHOOK_URL=get_secret('webhooks.discord.url')
GUILD_STATUS_WEBHOOK_URL=get_secret('webhooks.discord.guild_status.url', WEBHOOK_URL)
MONITORING_WEBHOOK_URL=get_secret('webhooks.discord.monitoring.url', WEBHOOK_URL)


class DiscordWebhookType(Enum):
    GUILD_STATUS = 1
    MONITORING = 2


_webhook_type_url_map = {
    DiscordWebhookType.GUILD_STATUS: GUILD_STATUS_WEBHOOK_URL,
    DiscordWebhookType.MONITORING: MONITORING_WEBHOOK_URL
}


def _send_discord_message(webhook_type: DiscordWebhookType, **kwargs):
    Webhook.from_url(
        _webhook_type_url_map[webhook_type],
        adapter=RequestsWebhookAdapter()).send(**kwargs)


def send_message(webhook_type: DiscordWebhookType, text: str) -> None:
    if not text:
        print('Attempted to send discord message, but no text was provided.')
        return

    _send_discord_message(
        webhook_type,
        content=text)


def send_embedded_message(webhook_type: DiscordWebhookType, text: str, color: Color):
    if not text:
        print('Attempted to send embedded discord message, but no text was provided.')
        return

    _send_discord_message(
        webhook_type,
        embed=Embed(description=text, color=color))


def send_bot_started_message():
    send_embedded_message(
        DiscordWebhookType.MONITORING,
        'Bot has been started.',
        Color.green())


def send_bot_stopped_message():
    send_embedded_message(
        DiscordWebhookType.MONITORING,
        'Bot has been stopped.',
        Color.from_rgb(255, 255, 0))


def send_bot_crashed_message():
    send_embedded_message(
        DiscordWebhookType.MONITORING,
        'Bot has crashed! Please notify an administrator.',
        Color.red())
