import os
import pyray as rl

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable

from ftviz.db.utils import setup_database, load_family_tree
from ftviz.models import Node, FamilyTree


# Assets
FONT_PATH = os.path.join("resources", "fonts", "Jura.ttf")
BOLD_FONT_PATH = os.path.join("resources", "fonts", "Jura-Bold.ttf")
STYLE_PATH = os.path.join("resources", "styles", "bluish", "style_bluish.txt.rgs")
DATABASE_URI = "sqlite:///data/ftviz.db"

font = None
bold_font = None
engine = None
ft = None
preview = None

# App configuration
TITLE = "Family Tree"
INITIAL_WIDTH = 800
INITIAL_HEIGHT = 600

BACKGROUND = rl.get_color(0xF0BE4BFF)
FOREGROUND = rl.BLACK
BUTTON_BACKGROUND = rl.LIGHTGRAY
BUTTON_DOWN_BACKGROUND = rl.GRAY
PADDING = 10


def log_err(msg: str):
    raise Exception(msg)


class SCREEN(Enum):
    MAIN_MENU = 1
    LOADING_SCREEN = 2
    SUCCESS_SCREEN = 3
    EDIT_MENU = 4
    PREVIEW_SCREEN = 5


current_screen = SCREEN.MAIN_MENU
exit_requested = False


def go_to_screen(next_screen: SCREEN):
    global current_screen
    current_screen = next_screen


def do_nothing(*args, **kwargs): ...


def center_pos(
    child_size: rl.Vector2 = None,
    parent_pos: rl.Vector2 = None,
    parent_size: rl.Vector2 = None,
) -> rl.Vector2:
    if child_size is None:
        child_size = rl.Vector2(0, 0)
    if parent_pos is None and parent_size is None:
        parent_pos = rl.Vector2(0, 0)
        parent_size = rl.Vector2(*get_screen_size())

    x = (2 * parent_pos.x + parent_size.x - child_size.x) / 2
    y = (2 * parent_pos.y + parent_size.y - child_size.y) / 2

    return rl.Vector2(x, y)


class Button:
    callback = do_nothing

    def __init__(
        self,
        pos: rl.Vector2,
        size: rl.Vector2,
        text: str,
        callback: Optional[Callable] = None,
    ):
        self.pos = pos
        self.size = size
        self.text = text

        if callback:
            self.callback = callback

    def on_press(self, *args, **kwargs):
        self.callback(args, kwargs)


class GoButton(Button):
    """
    Not sure about inhereiting the Button class.

    TODO:
        - Review this inhereitance
    """

    def __init__(
        self,
        pos: rl.Vector2,
        size: rl.Vector2,
        text: str,
        next_screen: SCREEN,
    ):
        self.pos = pos
        self.size = size
        self.text = text
        self.next_screen = next_screen

    def on_press(self):
        go_to_screen(self.next_screen)


class ExitButton(Button):
    """
    Not sure about inhereiting the Button class.

    TODO:
        - Review this inhereitance
    """

    def __init__(
        self,
        pos: rl.Vector2,
        size: rl.Vector2,
        text: str,
    ):
        self.pos = pos
        self.size = size
        self.text = text

    def on_press(self):
        global exit_requested
        exit_requested = True


def get_screen_size():
    return rl.get_screen_width(), rl.get_screen_height()


def load_cyrillic_font(path: os.PathLike, font_size: int = 32) -> rl.Font:
    codepoints = rl.ffi.new("int[]", 512)
    for i in range(0, 95):
        codepoints[i] = 32 + i
    for i in range(0, 255):
        codepoints[96 + i] = 0x0400 + i

    codepoints_ptr = rl.ffi.cast("int *", codepoints)
    return rl.load_font_ex(path, font_size, codepoints_ptr, 512)


def load_fonts():
    global font
    global bold_font

    font = load_cyrillic_font(FONT_PATH)
    bold_font = load_cyrillic_font(BOLD_FONT_PATH, 60)


def load_sprite(path: os.PathLike, fallback=True) -> rl.Texture:
    def _fallback():
        img = rl.gen_image_color(INITIAL_WIDTH, INITIAL_HEIGHT, rl.WHITE)
        text_size = rl.measure_text_ex(bold_font, "Пусто", 32, 1)
        img_pos = rl.Vector2(0, 0)
        img_size = rl.Vector2(INITIAL_WIDTH, INITIAL_HEIGHT)
        pos = center_pos(text_size, img_pos, img_size)
        rl.image_draw_text_ex(img, bold_font, "Пусто", pos, 32, 1, rl.BLACK)
        texture = rl.load_texture_from_image(img)
        return texture

    if not os.path.exists(path):
        if not fallback:
            log_err(f"Couldn't load image: {path}")
            return None
        return _fallback()

    img = rl.load_image(path)
    texture = rl.load_texture_from_image(img)

    rl.unload_image(img)
    return texture


def draw_text(
    text: str,
    font_size: int,
    pos: rl.Vector2,
    text_font: rl.Font = None,
    centered: bool = False,
    color=None,
):
    if text_font is None:
        text_font = rl.get_font_default()
    if centered:
        text_size = rl.measure_text_ex(text_font, text, font_size, 1)
        pos = rl.vector2_subtract(pos, rl.vector2_scale(text_size, 0.5))
    if color is None:
        color = rl.get_color(
            rl.gui_get_style(
                rl.GuiControl.TEXTBOX,
                rl.GuiControlProperty.TEXT_COLOR_NORMAL,
            )
        )

    rl.draw_text_ex(
        text_font,
        text,
        pos,
        font_size,
        1,
        color,
    )


def draw_title():
    title_pos = rl.Vector2(PADDING, PADDING)
    draw_text(
        "Главное меню",
        40,
        title_pos,
        text_font=bold_font,
    )


def draw_button(button: Button) -> bool:
    rl.gui_set_style(rl.GuiControl.DEFAULT, rl.GuiDefaultProperty.TEXT_SIZE, 32)
    if rl.gui_button(
        rl.Rectangle(button.pos.x, button.pos.y, button.size.x, button.size.y),
        button.text,
    ):
        button.on_press()


def draw_preview(bounds: rl.Rectangle, centered: bool = True):
    global preview
    panel_header_height = 24
    panel_padding = 1
    scale = min(
        (bounds.width - 2 * panel_padding) / preview.width,
        (bounds.height - 2 * panel_padding - panel_header_height) / preview.height,
    )
    pos = rl.Vector2(
        bounds.x + panel_padding,
        bounds.y + panel_header_height + panel_padding,
    )

    if centered:
        actual_size = rl.Vector2(preview.width * scale, preview.height * scale)
        pos = center_pos(
            actual_size,
            rl.Vector2(
                bounds.x + panel_padding,
                bounds.y + panel_padding + panel_header_height / 2,
            ),
            rl.Vector2(bounds.width, bounds.height),
        )

    # GIZMO
    rl.gui_panel(bounds, "Preview")
    rl.draw_rectangle(
        int(bounds.x + panel_padding),
        int(bounds.y + panel_padding + panel_header_height),
        int(bounds.width - 2 * panel_padding),
        int(bounds.height - 2 * panel_padding - panel_header_height),
        rl.WHITE,
    )

    if preview:
        rl.draw_texture_ex(preview, pos, 0, scale, rl.WHITE)


def draw_screen(screen: SCREEN):
    if screen == SCREEN.MAIN_MENU:
        button_size = rl.Vector2(300, 50)
        center = center_pos(button_size)
        center.x = PADDING

        button_pos1 = rl.vector2_subtract(
            center, rl.Vector2(0, button_size.y * 2 + PADDING)
        )
        button_pos2 = rl.vector2_subtract(
            center, rl.Vector2(0, button_size.y / 2 + PADDING)
        )
        button_pos3 = rl.vector2_add(
            center,
            rl.Vector2(
                0,
                button_size.y / 2 + PADDING,
            ),
        )
        button_pos4 = rl.vector2_add(
            center,
            rl.Vector2(
                0,
                button_size.y * 2 + PADDING,
            ),
        )
        btn1 = GoButton(
            button_pos1, button_size, "Редактировать древо", SCREEN.EDIT_MENU
        )
        btn2 = Button(button_pos2, button_size, "Просмотреть древо")
        btn3 = Button(button_pos3, button_size, "Сгенерировать PDF")
        exit_btn = ExitButton(button_pos4, button_size, "Выйти")

        draw_title()
        draw_button(btn1)
        draw_button(btn2)
        draw_button(btn3)
        draw_button(exit_btn)
        preview_pos = rl.Vector2(
            button_pos1.x + button_size.x + PADDING,
            2 * PADDING,
        )
        preview_size = rl.vector2_subtract(
            get_screen_size(), rl.vector2_add_value(preview_pos, PADDING)
        )
        draw_preview(
            rl.Rectangle(
                preview_pos.x,
                preview_pos.y,
                preview_size.x,
                preview_size.y,
            ),
        )
    if screen == SCREEN.EDIT_MENU:
        ...


def main():
    global engine
    global ft
    global preview
    rl.init_window(INITIAL_WIDTH, INITIAL_HEIGHT, TITLE)
    rl.set_target_fps(20)

    # Load assets
    load_fonts()
    rl.gui_load_style(STYLE_PATH)
    rl.gui_set_font(font)
    engine = setup_database(DATABASE_URI)
    ft = load_family_tree(engine)
    preview = load_sprite(os.path.join("output", "family-tree.gv.png"))
    # ----------------------------------------------------------------------------------

    while not (rl.window_should_close() or exit_requested):
        rl.begin_drawing()
        rl.clear_background(rl.WHITE)
        rl.clear_background(rl.get_color(0xE8EEF1FF))

        # Update
        draw_screen(current_screen)
        # ------------------------------------------------------------------------------
        rl.end_drawing()

    # Unload assets
    rl.unload_font(font)
    rl.unload_font(bold_font)
    rl.unload_texture(preview)
    # ----------------------------------------------------------------------------------

    rl.close_window()


if __name__ == "__main__":
    main()
