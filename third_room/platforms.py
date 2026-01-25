import arcade


class Platforms:
    def __init__(self):
        self.big_platform_texture = arcade.load_texture("third_room/images/platform1.png")
        self.small_platform_texture = arcade.load_texture("third_room/images/platform3.png")
        self.platform_texture = arcade.load_texture("third_room/images/platform4.png")
        self.elements = arcade.SpriteList()

    def create(self):
        platforms_data = [
            (170, 50, self.big_platform_texture, 400, 100),
            (680, (92 - 28) * 2, self.small_platform_texture, 2000, 800),
            (820, 132 * 2, self.small_platform_texture, 2000, 800),
            (420, 198 * 2, self.big_platform_texture, 400, 100),
            (120, 500, self.small_platform_texture, 2000, 800),
            (440, 308 * 2, self.platform_texture, 1600, 600),
            (940, 368 * 2, self.platform_texture, 1600, 600),
            (285 * 2, 860, self.small_platform_texture, 2000, 800),
            (85 * 2, 980, self.platform_texture, 1600, 600),
            (15 * 2, 1100, self.small_platform_texture, 2000, 800),
            (103 * 2, 1220, self.small_platform_texture, 2000, 800),
            (280 * 2, 1340, self.big_platform_texture, 400, 100),
            (63 * 2, 1575, self.small_platform_texture, 2000, 800),
            (143 * 2, 1450, self.small_platform_texture, 2000, 800),
            (430 * 2, 1540, self.big_platform_texture, 400, 100),
            (1350, 1530, self.small_platform_texture, 2000, 800),
            (800 * 2, 1290, self.big_platform_texture, 400, 100),
            (940 * 2, 1290, self.big_platform_texture, 400, 100),
            (1350, 720, self.big_platform_texture, 400, 100),
            (1630, 720, self.big_platform_texture, 400, 100),
            (1910, 720, self.big_platform_texture, 400, 100),
            (2190, 720, self.big_platform_texture, 400, 100),




            (1340 * 2, 370 * 2, self.platform_texture, 1600, 600),
            (685 * 2, 1150, self.small_platform_texture, 2000, 800),
            (2150, 1410, self.platform_texture, 1600, 600),
            (3000, 800, self.small_platform_texture, 2000, 800),
        ]

        for x, y, texture, width, height in platforms_data:
            platform = arcade.Sprite()
            platform.texture = texture
            platform.center_x = x
            platform.center_y = y
            platform.width = width
            platform.height = height

            self.elements.append(platform)

    def draw(self):
        self.elements.draw()