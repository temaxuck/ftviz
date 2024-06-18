import os
import pyray as rl

from dataclasses import dataclass
from typing import Optional, Callable

# Assets
FONT_PATH = os.path.join("resources", "fonts", "Jura.ttf")
STYLE_PATH = os.path.join("resources", "styles", "sunny", "style_sunny.txt.rgs")
font = None

# App configuration
TITLE = "Family Tree"
INITIAL_WIDTH = 800
INITIAL_HEIGHT = 600

BACKGROUND = rl.get_color(0xF0BE4BFF)
FOREGROUND = rl.BLACK
BUTTON_BACKGROUND = rl.LIGHTGRAY
BUTTON_DOWN_BACKGROUND = rl.GRAY


def get_screen_size():
    return rl.get_screen_width(), rl.get_screen_height()


def load_cyrillic_font() -> rl.Font:
    codepoints = rl.ffi.new("int[]", 512)
    for i in range(0, 95):
        codepoints[i] = 32 + i
    for i in range(0, 255):
        codepoints[96 + i] = 0x0400 + i

    codepoints_ptr = rl.ffi.cast("int *", codepoints)
    return rl.load_font_ex(FONT_PATH, 32, codepoints_ptr, 512)


def center_pos(
    child_size: rl.Vector2,
    parent_pos: rl.Vector2 = None,
    parent_size: rl.Vector2 = None,
) -> rl.Vector2:
    if parent_pos is None and parent_size is None:
        parent_pos = rl.Vector2(0, 0)
        parent_size = rl.Vector2(*get_screen_size())

    x = (2 * parent_pos.x + parent_size.x - child_size.x) / 2
    y = (2 * parent_pos.y + parent_size.y - child_size.y) / 2

    return rl.Vector2(x, y)


def draw_text_at_center(
    text: str,
    font_size: float,
    color: rl.Color,
):
    text_size = rl.measure_text_ex(font, text, font_size, 1)
    w, h = get_width(), get_height()
    pos = center_pos(text_size)
    rl.draw_text_ex(font, text, pos, font_size, 1, color)


def draw_button(
    pos: rl.Vector2, size: rl.Vector2, text: str, callback: Callable
) -> bool:
    rl.gui_set_style(rl.GuiControl.DEFAULT, rl.GuiDefaultProperty.TEXT_SIZE, 32)
    if rl.gui_button(rl.Rectangle(pos.x, pos.y, size.x, size.y), text):
        callback()


def callback():
    print("meh")


def main():
    global font

    rl.init_window(INITIAL_WIDTH, INITIAL_HEIGHT, TITLE)
    rl.set_target_fps(20)

    # Load assets
    font = load_cyrillic_font()
    rl.gui_load_style(STYLE_PATH)
    rl.gui_set_font(font)
    # -----------------------------------------------------------------------------

    while not rl.window_should_close():
        # Update
        rl.begin_drawing()
        rl.clear_background(BACKGROUND)

        button_size = rl.Vector2(300, 50)
        padding = 10
        button_pos1 = rl.vector2_subtract(
            center_pos(button_size), rl.Vector2(0, button_size.y / 2 + padding)
        )
        button_pos2 = rl.vector2_add(
            center_pos(button_size), rl.Vector2(0, button_size.y / 2 + padding)
        )
        draw_button(button_pos1, button_size, "Редактировать древо", callback)
        draw_button(button_pos2, button_size, "Редактировать древо", callback)

        rl.end_drawing()
        # -------------------------------------------------------------------------

    # Unload assets
    rl.unload_font(font)
    # -----------------------------------------------------------------------------

    rl.close_window()


if __name__ == "__main__":
    main()
