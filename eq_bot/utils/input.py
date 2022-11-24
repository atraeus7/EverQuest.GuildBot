from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
from datetime import datetime, timedelta
from utils.config import get_config

SECONDS_DELAY_IF_RECENT_INPUT = get_config('general.input.seconds_delay_if_recent_input', 60)

_input_observers = []

def _inform_observers(typ, value):
    for observer in _input_observers:
        observer(typ, value)    

def _on_press_key(key):
    _inform_observers('key.press', key)

def _on_release_key(key):
    _inform_observers('key.release', key)

def _on_move_mouse(x, y):
    _inform_observers('mouse.move', (x, y))

def _on_click_mouse(x, y, button, pressed):
    _inform_observers('mouse.click', (x, y, button, pressed))

def _on_scroll_mouse(x, y, dx, dy):
    _inform_observers('mouse.scroll', (x, y, dx, dy))

# Methods for tracking the last input time

_last_input_time = datetime.now() - timedelta(seconds=SECONDS_DELAY_IF_RECENT_INPUT) 
_seconds_delay_if_recent_input = timedelta(seconds=SECONDS_DELAY_IF_RECENT_INPUT)

_keyboard_listener = KeyboardListener(
    on_press=_on_press_key,
    on_release=_on_release_key)

_mouse_listener = MouseListener(
    on_move=_on_move_mouse,
    on_click=_on_click_mouse,
    on_scroll=_on_scroll_mouse)

def observe_input(callback):
    _keyboard_listener.stop()
    _mouse_listener.stop()
    _input_observers.append(callback)
    _mouse_listener.start()
    _keyboard_listener.start()

def _set_last_input_time():
    global _last_input_time
    _last_input_time = datetime.now()

def _update_last_input_time(action, key):
    _set_last_input_time()

def get_timedelta_since_input():
    return datetime.now() - _last_input_time

def has_recent_input():
    return get_timedelta_since_input() < _seconds_delay_if_recent_input

observe_input(_update_last_input_time)
