import arcade
from third_room.config import SCREEN_HEIGHT, PLAYER_MAX_HP


class HealthBar:
    def __init__(self):
        self.width = 300
        self.height = 35
        self.x = 20
        self.y = SCREEN_HEIGHT - 40

        self.hp = PLAYER_MAX_HP
        self.ratio = max(0, self.hp / PLAYER_MAX_HP)

        self.text = arcade.Text(
            "HP: 100/100",
            self.x + self.width / 2,
            self.y,
            arcade.color.WHITE,
            18,
            bold=True,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

    def draw(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(
            self.x + self.width / 2,
            self.y,
            self.width + 6,
            self.height + 6),
            arcade.color.BLACK
        )

        arcade.draw_rect_filled(arcade.rect.XYWH(
             self.x + self.width / 2,
             self.y,
             self.width,
             self.height),
             arcade.color.DARK_RED
        )

        self.ratio = max(0, self.hp / PLAYER_MAX_HP)
        if self.ratio > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(
                 self.x + (self.width * self.ratio) / 2,
                 self.y,
                 self.width * self.ratio,
                 self.height),
                 arcade.color.GREEN
            )

            self.text.text = f"HP: {int(self.hp)}/{PLAYER_MAX_HP}"
            self.text.x = self.x + self.width / 2
            self.text.y = self.y
            self.text.draw()
