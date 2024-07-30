import os
import pyray as rl

from ctypes import POINTER, c_int, pointer
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, List

from ftviz.db.utils import setup_database, load_family_tree
from ftviz.models import Node, FamilyTree


# Assets
FONT_PATH = os.path.join("resources", "fonts", "Jura.ttf")
BOLD_FONT_PATH = os.path.join("resources", "fonts", "Jura-Bold.ttf")
STYLE_PATH = os.path.join("resources", "styles", "bluish", "style_bluish.txt.rgs")
DATABASE_URI = "sqlite:///data/ftviz.db"


class AppState:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(AppState, cls).__new__(cls)

        return cls.instance

    def __getattr__(self, attr):
        if str(attr) in self.__dict__:
            return attr

        return None


g = AppState()

# App configuration
TITLE = "Family Tree"
INITIAL_WIDTH = 800
INITIAL_HEIGHT = 600


BACKGROUND = rl.get_color(0xF0BE4BFF)
FOREGROUND = rl.BLACK
BUTTON_BACKGROUND = rl.LIGHTGRAY
BUTTON_DOWN_BACKGROUND = rl.GRAY
PADDING = 10

# CONSTS
PANEL_HEADER_HEIGHT = 24
PANEL_BORDER_WIDTH = 1


def log_err(msg: str):
    raise Exception(msg)


class SCREEN(Enum):
    MAIN_MENU = 1
    LOADING_SCREEN = 2
    SUCCESS_SCREEN = 3
    EDIT_MENU = 4
    PREVIEW_SCREEN = 5


g.current_screen = SCREEN.EDIT_MENU
g.exit_requested = False


def go_to_screen(next_screen: SCREEN):
    g.current_screen = next_screen


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
        g.exit_requested = True


def get_screen_size():
    return rl.get_screen_width(), rl.get_screen_height()


def strs_to_c_str_array(strs: List[str]):
    bytes_list = [rl.ffi.new("char []", s.encode("utf-8")) for s in strs]
    items = rl.ffi.new("char *[]", bytes_list)
    return items


def load_cyrillic_font(path: os.PathLike, font_size: int = 32) -> rl.Font:
    codepoints = rl.ffi.new("int[]", 512)
    for i in range(0, 95):
        codepoints[i] = 32 + i
    for i in range(0, 255):
        codepoints[96 + i] = 0x0400 + i

    codepoints_ptr = rl.ffi.cast("int *", codepoints)
    return rl.load_font_ex(path, font_size, codepoints_ptr, 512)


def load_fonts():
    g.font = load_cyrillic_font(FONT_PATH)
    g.bold_font = load_cyrillic_font(BOLD_FONT_PATH, 60)


def load_sprite(path: os.PathLike, fallback=True) -> rl.Texture:
    def _fallback():
        img = rl.gen_image_color(INITIAL_WIDTH, INITIAL_HEIGHT, rl.WHITE)
        text_size = rl.measure_text_ex(g.bold_font, "Пусто", 32, 1)
        img_pos = rl.Vector2(0, 0)
        img_size = rl.Vector2(INITIAL_WIDTH, INITIAL_HEIGHT)
        pos = center_pos(text_size, img_pos, img_size)
        rl.image_draw_text_ex(img, g.bold_font, "Пусто", pos, 32, 1, rl.BLACK)
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


def draw_title(title: str, pos: rl.Vector2 = rl.Vector2(PADDING, PADDING)):
    draw_text(
        title,
        40,
        pos,
        text_font=g.bold_font,
    )


def draw_button(button: Button) -> bool:
    rl.gui_set_style(rl.GuiControl.DEFAULT, rl.GuiDefaultProperty.TEXT_SIZE, 32)
    if rl.gui_button(
        rl.Rectangle(button.pos.x, button.pos.y, button.size.x, button.size.y),
        button.text,
    ):
        button.on_press()


def draw_preview(bounds: rl.Rectangle, centered: bool = True):
    scale = min(
        (bounds.width - 2 * PANEL_BORDER_WIDTH) / g.preview.width,
        (bounds.height - 2 * PANEL_BORDER_WIDTH - PANEL_HEADER_HEIGHT)
        / g.preview.height,
    )
    pos = rl.Vector2(
        bounds.x + PANEL_BORDER_WIDTH,
        bounds.y + PANEL_HEADER_HEIGHT + PANEL_BORDER_WIDTH,
    )

    if centered:
        actual_size = rl.Vector2(g.preview.width * scale, g.preview.height * scale)
        pos = center_pos(
            actual_size,
            rl.Vector2(
                bounds.x + PANEL_BORDER_WIDTH,
                bounds.y + PANEL_BORDER_WIDTH + PANEL_HEADER_HEIGHT / 2,
            ),
            rl.Vector2(bounds.width, bounds.height),
        )

    # GIZMO
    rl.gui_panel(bounds, "Preview")
    rl.draw_rectangle(
        int(bounds.x + PANEL_BORDER_WIDTH),
        int(bounds.y + PANEL_BORDER_WIDTH + PANEL_HEADER_HEIGHT),
        int(bounds.width - 2 * PANEL_BORDER_WIDTH),
        int(bounds.height - 2 * PANEL_BORDER_WIDTH - PANEL_HEADER_HEIGHT),
        rl.WHITE,
    )

    if g.preview:
        rl.draw_texture_ex(g.preview, pos, 0, scale, rl.WHITE)


def draw_list_view(
    bounds: rl.Rectangle,
    items: List[str],
    scroll_index: POINTER(c_int),
    active_index: POINTER(c_int),
    focus_index: POINTER(c_int),
) -> int:
    c_items = strs_to_c_str_array(map(str, items))
    count = len(items)
    return rl.gui_list_view_ex(
        bounds,
        c_items,
        count,
        scroll_index,
        active_index,
        focus_index,
    )


def draw_nodes_list_view(pos: rl.Vector2, size: rl.Vector2):
    list_view_items = g.ft.nodes

    return draw_list_view(
        rl.Rectangle(
            int(pos.x),
            int(pos.y),
            int(size.x),
            int(size.y),
        ),
        list_view_items,
        g.list_view_scroll_index,
        g.list_view_active_index,
        g.list_view_focus_index,
    )


def draw_screen(screen: SCREEN):
    button_size = rl.Vector2(300, 50)
    center = center_pos(button_size)
    left_center = rl.Vector2(PADDING, center.y)
    if screen == SCREEN.MAIN_MENU:
        button_pos1 = rl.vector2_subtract(
            left_center, rl.Vector2(0, button_size.y * 2 + PADDING)
        )
        button_pos2 = rl.vector2_subtract(
            left_center, rl.Vector2(0, button_size.y / 2 + PADDING)
        )
        button_pos3 = rl.vector2_add(
            left_center,
            rl.Vector2(
                0,
                button_size.y / 2 + PADDING,
            ),
        )
        button_pos4 = rl.vector2_add(
            left_center,
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

        draw_title("Главное меню")
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
    elif screen == SCREEN.EDIT_MENU:
        back_btn_pos = rl.Vector2(PADDING, PADDING)
        back_btn_size = rl.Vector2(60, 40)
        back_btn = GoButton(
            back_btn_pos,
            back_btn_size,
            rl.gui_icon_text(rl.GuiIconName.ICON_ARROW_LEFT_FILL, ""),
            SCREEN.MAIN_MENU,
        )
        draw_button(back_btn)
        title_pos = rl.Vector2(
            back_btn_pos.x + back_btn_size.x + PADDING,
            PADDING,
        )
        draw_title("Меню редактирования", title_pos)
        w, h = get_screen_size()

        panel_pos1 = rl.Vector2(PADDING, back_btn_pos.y + back_btn_size.y + PADDING)
        panel_size1 = rl.Vector2(
            max(0, w / 2 - panel_pos1.x - PADDING),
            max(0, h - panel_pos1.y - PADDING),
        )

        rl.gui_panel(
            rl.Rectangle(
                int(panel_pos1.x),
                int(panel_pos1.y),
                int(panel_size1.x),
                int(panel_size1.y),
            ),
            "Выберите запись",
        )

        list_view_pos = rl.Vector2(panel_pos1.x, panel_pos1.y + PANEL_HEADER_HEIGHT)
        list_view_size = rl.Vector2(
            panel_size1.x,
            panel_size1.y - PANEL_HEADER_HEIGHT,
        )
        draw_nodes_list_view(list_view_pos, list_view_size)

        panel_pos2 = rl.Vector2(
            panel_pos1.x + panel_size1.x + PADDING,
            panel_pos1.y,
        )
        panel_size2 = rl.Vector2(
            max(0, w - panel_pos2.x - PADDING),
            max(0, h - panel_pos2.y - PADDING),
        )
        rl.gui_panel(
            rl.Rectangle(
                int(panel_pos2.x),
                int(panel_pos2.y),
                int(panel_size2.x),
                int(panel_size2.y),
            ),
            "Редактировать информацию",
        )

        current_index = g.list_view_active_index[0]
        draw_text(
            f"{g.ft.nodes[current_index].id}",
            32,
            rl.vector2_add_value(panel_pos2, PANEL_HEADER_HEIGHT),
            centered=False,
        )


def main():
    rl.init_window(INITIAL_WIDTH, INITIAL_HEIGHT, TITLE)
    rl.set_target_fps(20)

    # Load assets
    load_fonts()
    rl.gui_load_style(STYLE_PATH)
    rl.gui_set_font(g.font)
    g.engine = setup_database(DATABASE_URI)
    g.ft = load_family_tree(g.engine)
    g.preview = load_sprite(os.path.join("output", "family-tree.gv.png"))
    # ----------------------------------------------------------------------------------

    # Define AppState
    g.list_view_focus_index = rl.ffi.new("int *", -1)
    g.list_view_scroll_index = rl.ffi.new("int *", 0)
    g.list_view_active_index = rl.ffi.new("int *", 0)
    # ----------------------------------------------------------------------------------

    while not (rl.window_should_close() or g.exit_requested):
        rl.begin_drawing()
        background_color = 2**32 + (
            rl.gui_get_style(
                rl.GuiControl.DEFAULT, rl.GuiDefaultProperty.BACKGROUND_COLOR
            )
        )
        rl.clear_background(rl.get_color(background_color))

        # Update
        draw_screen(g.current_screen)
        # ------------------------------------------------------------------------------
        rl.end_drawing()

    # Unload assets
    rl.unload_font(g.font)
    rl.unload_font(g.bold_font)
    rl.unload_texture(g.preview)
    # ----------------------------------------------------------------------------------

    rl.close_window()


if __name__ == "__main__":
    main()
