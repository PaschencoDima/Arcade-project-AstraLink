import arcade


class Wall:
    def __init__(self):
        self.elements = arcade.SpriteList()
        self.size = 40
        self.texture = arcade.load_texture("third_room/images/purple_walls.png")

    def create_horizontal(self, y, start, end):
        x = start
        while x < end:
            self.create_element(x, y)
            x += self.size

    def create_vertical(self, x, start, end):
        y = start
        while y < end:
            self.create_element(x, y)
            y += self.size

    def create_element(self, x, y):
        element = arcade.Sprite()

        element.texture = self.texture
        element.center_x = x
        element.center_y = y
        element.width = self.size
        element.height = self.size

        self.elements.append(element)

    def draw(self):
        self.elements.draw()


