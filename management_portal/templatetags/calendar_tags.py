from django import template
from datetime import datetime, time

register = template.Library()

@register.filter
def time_to_pixels(value):
    """Convert time to pixels for positioning"""
    if isinstance(value, datetime):
        hours = value.hour + (value.minute / 60)
    elif isinstance(value, time):
        hours = value.hour + (value.minute / 60)
    else:
        return 0
    return (hours - 6) * 30  # 30px per hour, starting from 6 AM

@register.filter
def hours_to_pixels(value):
    """Convert duration hours to pixels"""
    return value * 30  # 30px per hour

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    return dictionary.get(key, [])

@register.filter
def modulo(value, arg):
    """Return the modulo of value and arg"""
    return int(value) % int(arg) 