import sys
import pyfiglet
import pycowsay.main
from random import randint
from typing import Optional


def __cow_message(message: str):
    temp = sys.argv[1:]
    sys.argv[1:] = message
    pycowsay.main.main()
    sys.argv[1:] = temp


def __3d_message(message: str, preferred: Optional[bool] = True):
    all_fonts = pyfiglet.FigletFont.getFonts()
    preferred_fonts = [
        "big_money-se",
        "big_money-ne",
        "the_edge",
        "poison",
        "sweet",
        "soft",
        "bloody",
        "modular",
        "future",
        "univers",
        "3d-ascii"
    ]
    fonts = preferred_fonts if preferred is not None and preferred else all_fonts
    fonts_count = len(fonts)
    font_index = randint(0, fonts_count - 1)
    font = fonts[font_index]
    ascii_art = pyfiglet.figlet_format(message, font=font)
    print("\n")
    print(ascii_art)


def Greetings(message: str, is_cow: Optional[bool] = False):
    def decorator(function):
        def wrapper(*args, **kwargs):
            __cow_message(message) if is_cow is not None and is_cow else __3d_message(
                message)
            result = function(*args, **kwargs)
            return result
        return wrapper
    return decorator
