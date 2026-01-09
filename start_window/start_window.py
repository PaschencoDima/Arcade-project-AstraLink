import arcade
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import register_user, login_user, get_current_user

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
TITLE = "Game Menu"


def get_resource_path(filename):
    possible_paths = [
        filename,
        os.path.join("start_window", filename),
        os.path.join("start_window/images", filename),
        os.path.join("images", filename),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return filename


def is_point_in_rect(x, y, rect):
    left = rect.x - rect.width / 2
    right = rect.x + rect.width / 2
    bottom = rect.y - rect.height / 2
    top = rect.y + rect.height / 2

    return left <= x <= right and bottom <= y <= top


def validate_password(password):
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"

    if not re.search(r'\d', password):
        return False, "Пароль должен содержать хотя бы одну цифру (0-9)"

    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну строчную букву (a-z)"

    allowed_special_chars = r'&\(\)/_\-\!#'
    invalid_chars_pattern = f'[^a-zA-Z0-9{allowed_special_chars}]'
    if re.search(invalid_chars_pattern, password):
        return False, f"Пароль содержит недопустимые символы\nДопустимы: буквы a-z, цифры 0-9, спецсимволы &()/_-!#"

    return True, "Пароль надежный"


class LoginWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Вход / Регистрация")
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

        self.mode = "login"
        self.username = ""
        self.password = ""
        self.active_field = "username"

        self.login_button_rect = None
        self.register_button_rect = None
        self.switch_mode_text_rect = None

        self.message = ""
        self.message_color = arcade.color.RED
        self.message_timer = 0

        self.username_text = None
        self.password_text = None
        self.title_text = None
        self.button_text = None
        self.switch_text = None
        self.message_text = None
        self.username_label_text = None
        self.password_label_text = None

        self.setup()

    def setup(self):
        self.background_texture = arcade.load_texture(get_resource_path('images/background.png'))
        self.login_button_texture = arcade.load_texture(get_resource_path('images/log_in.png'))

        center_x = self.w // 2
        center_y = self.h // 2

        self.field_width = 400
        self.field_height = 50
        self.field_y = center_y + 50

        button_width = 300
        button_height = 80

        offset_down = 25

        self.login_button_rect = arcade.rect.XYWH(
            center_x,
            center_y - 115 - offset_down,
            button_width,
            button_height
        )

        self.switch_mode_text_rect = arcade.rect.XYWH(
            center_x,
            center_y - 160 - offset_down,
            500,
            40
        )

        self.create_text_objects()

    def create_text_objects(self):
        center_x = self.w // 2

        self.title_text = arcade.Text(
            "",
            center_x,
            self.h - 150,
            arcade.color.WHITE,
            32,
            align="center",
            anchor_x="center",
            font_name='segoe print'
        )

        self.username_label_text = arcade.Text(
            "Имя пользователя:",
            center_x,
            self.field_y + 40,
            arcade.color.WHITE,
            16,
            align="center",
            anchor_x="center"
        )

        self.username_text = arcade.Text(
            "",
            center_x,
            self.field_y,
            arcade.color.WHITE,
            20,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        password_y = self.field_y - 80
        self.password_label_text = arcade.Text(
            "Пароль:",
            center_x,
            password_y + 40,
            arcade.color.WHITE,
            16,
            align="center",
            anchor_x="center"
        )

        self.password_text = arcade.Text(
            "",
            center_x,
            password_y,
            arcade.color.WHITE,
            20,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        self.switch_text = arcade.Text(
            "",
            self.switch_mode_text_rect.x,
            self.switch_mode_text_rect.y,
            arcade.color.BLUE,
            18,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        self.message_text = arcade.Text(
            "",
            self.w // 2,
            self.field_y - 136,
            arcade.color.RED,
            18,
            align="center",
            anchor_x="center",
            multiline=True,
            width=500
        )

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(
            self.background_texture,
            arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h)
        )

        self.title_text.text = "Вход в систему" if self.mode == "login" else "Регистрация"
        self.title_text.draw()

        field_x = self.w // 2

        username_bg_color = arcade.color.DARK_GRAY if self.active_field == "username" else arcade.color.GRAY
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                field_x,
                self.field_y,
                self.field_width,
                self.field_height
            ),
            username_bg_color
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                field_x,
                self.field_y,
                self.field_width,
                self.field_height
            ),
            arcade.color.WHITE,
            2
        )

        self.username_label_text.draw()

        display_username = self.username if self.username else "Введите имя пользователя"
        self.username_text.text = display_username
        self.username_text.color = arcade.color.WHITE if self.username else arcade.color.LIGHT_GRAY
        self.username_text.draw()

        password_y = self.field_y - 80
        password_bg_color = arcade.color.DARK_GRAY if self.active_field == "password" else arcade.color.GRAY
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                field_x,
                password_y,
                self.field_width,
                self.field_height
            ),
            password_bg_color
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                field_x,
                password_y,
                self.field_width,
                self.field_height
            ),
            arcade.color.WHITE,
            2
        )

        self.password_label_text.draw()

        display_password = "*" * len(self.password) if self.password else "Введите пароль"
        self.password_text.text = display_password
        self.password_text.color = arcade.color.WHITE if self.password else arcade.color.LIGHT_GRAY
        self.password_text.draw()

        arcade.draw_texture_rect(
            self.login_button_texture,
            self.login_button_rect
        )

        self.switch_text.text = "Еще нет аккаунта? Зарегистрируйся сейчас!" if self.mode == "login" else "Уже есть аккаунт? Войти"
        self.switch_text.draw()

        if self.message:
            self.message_text.text = self.message
            self.message_text.color = self.message_color
            self.message_text.draw()

    def on_update(self, delta_time):
        if self.message_timer > 0:
            self.message_timer -= delta_time
            if self.message_timer <= 0:
                self.message = ""

    def on_mouse_press(self, x, y, button, modifiers):
        username_rect = arcade.rect.XYWH(
            self.w // 2,
            self.field_y,
            self.field_width,
            self.field_height
        )

        if is_point_in_rect(x, y, username_rect):
            self.active_field = "username"
            return

        password_rect = arcade.rect.XYWH(
            self.w // 2,
            self.field_y - 80,
            self.field_width,
            self.field_height
        )

        if is_point_in_rect(x, y, password_rect):
            self.active_field = "password"
            return

        if is_point_in_rect(x, y, self.login_button_rect):
            self.process_login_or_register()
            return

        if is_point_in_rect(x, y, self.switch_mode_text_rect):
            self.mode = "register" if self.mode == "login" else "login"
            self.message = ""
            self.message_timer = 0
            return

    def on_key_press(self, key, modifiers):
        if key == arcade.key.TAB:
            self.active_field = "password" if self.active_field == "username" else "username"
            return

        if key == arcade.key.ENTER or key == arcade.key.RETURN:
            self.process_login_or_register()
            return

        if key == arcade.key.BACKSPACE:
            if self.active_field == "username" and self.username:
                self.username = self.username[:-1]
            elif self.active_field == "password" and self.password:
                self.password = self.password[:-1]
            return

        char = None

        if arcade.key.A <= key <= arcade.key.Z:
            char = chr(ord('a') + (key - arcade.key.A))

        elif arcade.key.KEY_0 <= key <= arcade.key.KEY_9:
            char = chr(key)

        elif key == arcade.key.SLASH:
            char = "/"
        elif key == arcade.key.MINUS:
            char = "-"
        elif key == arcade.key.SPACE:
            char = " "

        if modifiers & arcade.key.MOD_SHIFT:
            if arcade.key.KEY_1 <= key <= arcade.key.KEY_9:
                shift_digits = {
                    arcade.key.KEY_1: '!',
                    arcade.key.KEY_3: '#',
                    arcade.key.KEY_7: '&',
                    arcade.key.KEY_9: '(',
                    arcade.key.KEY_0: ')',
                }
                if key in shift_digits:
                    char = shift_digits[key]

        if key == arcade.key.MINUS and (modifiers & arcade.key.MOD_SHIFT):
            char = "_"

        if char:
            if self.active_field == "username":
                self.username += char
            else:
                self.password += char

    def process_login_or_register(self):
        if not self.username or not self.password:
            self.show_message("Заполните все поля!", arcade.color.RED)
            return

        if self.mode == "login":
            success, msg, user_id = login_user(self.username, self.password)
            if success:
                self.show_message("Успешный вход!", arcade.color.GREEN)
                arcade.schedule(self.start_game, 1.0)
            else:
                self.show_message(msg, arcade.color.RED)
        else:
            is_valid, error_msg = validate_password(self.password)
            if not is_valid:
                self.show_message(error_msg, arcade.color.RED)
                return

            success, msg, user_id = register_user(self.username, self.password)
            if success:
                self.show_message(msg, arcade.color.GREEN)
                self.mode = "login"
                self.password = ""
            else:
                self.show_message(msg, arcade.color.RED)

    def show_message(self, message, color):
        self.message = message
        self.message_color = color
        self.message_timer = 3.0

    def start_game(self, delta_time):
        arcade.unschedule(self.start_game)
        self.close()
        window = StartWindow()
        arcade.run()


class StoryWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "История")
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

        self.story_lines = [
            'Лог загрузки.',
            'Идентификатор пользователя: [УДАЛЕНО]',
            'Загрузка агента...',
            'Агент: неизвестный санитар.',
            'Цель: диагностика и очистка.',
            'Система: AstraLink v.7.4.2 "Гелиос".',
            'Статус: аварийное завершение работы, 712 циклов назад.',
            'Запуск...',
        ]

        self.displayed_text = []
        self.current_line = 0
        self.char_index = 0
        self.last_update_time = 0
        self.char_delay = 0.05

        self.animation_complete = False

        self.story_texts = []
        self.instruction_text = None

        self.setup()

    def setup(self):
        self.texture = arcade.load_texture(get_resource_path('images/background.png'))

        y_position = self.h - 200
        for line in self.story_lines:
            text = arcade.Text(
                "",
                self.w // 2,
                y_position,
                arcade.color.DARK_RED,
                24,
                font_name='segoe print',
                align="center",
                anchor_x="center",
                width=self.w - 100
            )
            self.story_texts.append(text)
            y_position -= 40

        self.instruction_text = arcade.Text(
            "Нажмите любую клавишу для продолжения...",
            self.w // 2,
            100,
            arcade.color.DARK_RED,
            20,
            font_name='playbill',
            align="center",
            anchor_x="center"
        )

    def on_draw(self):
        self.clear()

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h),
            arcade.color.BLACK
        )

        for i, line_text in enumerate(self.story_texts):
            if i < len(self.displayed_text):
                line_text.text = self.displayed_text[i]

                if i == self.current_line and not self.animation_complete:
                    line_text.color = arcade.color.RED
                else:
                    line_text.color = arcade.color.DARK_RED

                line_text.draw()

        if self.animation_complete:
            self.instruction_text.draw()

    def on_update(self, delta_time):
        self.last_update_time += delta_time

        if not self.animation_complete and self.last_update_time >= self.char_delay:
            self.last_update_time = 0

            if self.char_index < len(self.story_lines[self.current_line]):
                if len(self.displayed_text) <= self.current_line:
                    self.displayed_text.append("")

                self.displayed_text[self.current_line] += self.story_lines[self.current_line][self.char_index]
                self.char_index += 1
            else:
                self.current_line += 1
                self.char_index = 0

                if self.current_line >= len(self.story_lines):
                    self.animation_complete = True

    def on_key_press(self, key, modifiers):
        if not self.animation_complete:
            self.displayed_text = self.story_lines[:]
            self.animation_complete = True
        else:
            self.close()
            import first_room.drawing_first_room_first_lvl
            first_room.drawing_first_room_first_lvl.start_game()


class StartWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT
        self.button_clicked = False

        self.button_width = 600
        self.button_height = 240

        self.button_x = self.w // 2
        self.button_y = self.h // 2

        self.button_text = None
        self.texture = None
        self.button_texture = None

        self.setup()

    def setup(self):
        self.texture = arcade.load_texture(get_resource_path("images/background.png"))
        self.button_texture = arcade.load_texture(get_resource_path('images/button.png'))

        self.button_text = arcade.Text(
            "НАЧАТЬ ИГРУ",
            self.button_x,
            self.button_y,
            arcade.color.WHITE,
            48,
            align="center",
            anchor_x="center",
            anchor_y="center",
            font_name='segoe print'
        )

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h)
        )

        arcade.draw_texture_rect(
            self.button_texture,
            arcade.rect.XYWH(
                self.button_x,
                self.button_y,
                self.button_width,
                self.button_height
            )
        )

        self.button_text.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        button_left = self.button_x - self.button_width // 2
        button_right = self.button_x + self.button_width // 2
        button_bottom = self.button_y - self.button_height // 2
        button_top = self.button_y + self.button_height // 2

        if (button_left <= x <= button_right and
                button_bottom <= y <= button_top):
            self.button_clicked = True

            self.close()
            story_window = StoryWindow()
            story_window.setup()
            arcade.run()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.close()
            story_window = StoryWindow()
            story_window.setup()
            arcade.run()

    def on_mouse_release(self, x, y, button, modifiers):
        self.button_clicked = False


def main():
    window = StartWindow()
    arcade.run()


def main_login():
    window = LoginWindow()
    arcade.run()


if __name__ == "__main__":
    main_login()