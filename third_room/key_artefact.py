import arcade


class Key:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 80
        self.collected = False
        self.texture = arcade.load_texture("third_room/images/key.png")

    def update(self, delta_time):
        pass

    def draw(self):
        if self.collected:
            return

        arcade.draw_texture_rect(
             self.texture,
             arcade.rect.XYWH(
                 self.x,
                 self.y,
                 self.width,
                 self.height
             )
        )

    def check_collision(self, player):
        if self.collected:
            return False

        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = self.y - self.height / 2
        top = self.y + self.height / 2

        return (
                player.right > left and
                player.left < right and
                player.top > bottom and
                player.bottom < top
        )

    def get(self):
        self.collected = True