"""signal"""

SIGNAL_COLOR_BLACK   = "k"
SIGNAL_COLOR_WHITE   = "w"
SIGNAL_COLOR_RED     = "r"
SIGNAL_COLOR_YELLOW  = "y"
SIGNAL_COLOR_BLUE    = "b"
SIGNAL_COLOR_GREEN   = "g"
SIGNAL_COLOR_CYAN    = "c"
SIGNAL_COLOR_MAGENTA = "m"

SIGNAL_COLOR_GREY    = "grey"
SIGNAL_COLOR_SILVER  = "silver"

SIGNAL_COLOR_BROWN    = "brown"
SIGNAL_COLOR_TAN    = "tan"

SIGNAL_COLOR_GOLD    = "gold"

SIGNAL_COLOR_ORANGE    = "orange"
SIGNAL_COLOR_ORANGERED = "orangered"

SIGNAL_COLOR_FUCHSIA    = "fuchsia"
SIGNAL_COLOR_ORCHID    = "orchid"
SIGNAL_COLOR_PURPLE    = "purple"

SIGNAL_COLOR_SALMON    = "salmon"

SIGNAL_COLOR_SIENNA    = "sienna"
SIGNAL_COLOR_MAROON    = "maroon"


def create_signal(name, describe="", color=None, result=None):
    """创建信号"""
    signal = {"name": name, "describe": describe, "result": result}
    if color:
        signal["color"] = color
    return signal


