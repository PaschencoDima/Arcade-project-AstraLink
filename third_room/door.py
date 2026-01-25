import arcade


class Door:
    def __init__(self):
        self.elements = arcade.SpriteList()
        self.size = 40
        self.height = 100
        self.texture = arcade.load_texture("third_room/images/door_texture.jpg")

    def create_element(self, x, y):
        element = arcade.Sprite()

        element.texture = self.texture
        element.center_x = x
        element.center_y = y
        element.width = self.size
        element.height = self.size

        self.elements.append(element)

    def create(self, x, start):
        y = start
        end = start + self.height - self.size
        while y < end:
            self.create_element(x, y)
            y += self.size

    def draw(self):
        self.elements.draw()

    def kill_door(self):
        self.elements.clear()