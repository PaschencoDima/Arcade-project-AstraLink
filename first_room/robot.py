import arcade
import math
import os


class Robot(arcade.Sprite):
    def __init__(self, x, y, player=None, is_arena_robot=False):
        try:
            super().__init__("first_room/images/robotstand.png", scale=2.0)
        except:
            super().__init__(arcade.make_soft_circle_texture(30, arcade.color.RED), scale=2.0)

        self.center_x = x
        self.center_y = y
        self.player = player

        self.active = True
        self.spawned = False if is_arena_robot else True
        self.health = 300
        self.max_health = 300
        self.bullet_damage = 25
        self.contact_damage = 20

        self.state = "idle"
        self.facing_right = True
        self.animation_timer = 0

        self.bullets = arcade.SpriteList()
        self.gibs = arcade.SpriteList()

        self.textures_dict = {}
        self.gib_textures = []
        self.load_textures()

        self.falling = False
        self.fall_speed = 15
        self.target_y = y
        self.shoot_timer = 0
        self.shoot_cooldown = 2.5

        self.dash_speed = 6
        self.min_dist_to_player = 300

        self.platform_left = x - 200
        self.platform_right = x + 200
        self.platform_y = y

    def load_textures(self):
        main_path = "first_room/images/"
        files = {
            "idle": "robothover1.png", "land": "robothover2.png",
            "hover1": "robothover1.png", "hover2": "robothover2.png",
            "shoot": "robotshoot.png", "fall": "robotfall.png"
        }

        for name, file in files.items():
            path = os.path.join(main_path, file)
            if os.path.exists(path):
                tex_right = arcade.load_texture(path)
                tex_left = tex_right.flip_left_right()
                self.textures_dict[name] = [tex_right, tex_left]

        for i in range(1, 6):
            gib_path = os.path.join(main_path, f"robotgib{i}.png")
            if os.path.exists(gib_path):
                self.gib_textures.append(arcade.load_texture(gib_path))

    def spawn(self, x, y):
        self.center_x = x
        self.center_y = y + 300
        self.target_y = y
        self.falling = True
        self.spawned = True
        self.state = "fall"
        self.animation_timer = 0
        self.active = True

    def update_texture(self):
        if not self.textures_dict:
            return

        idx = 0 if self.facing_right else 1

        current_state = self.state
        if current_state == "dash":
            current_state = "hover1" if int(self.animation_timer * 10) % 2 == 0 else "hover2"

        if current_state in self.textures_dict:
            self.texture = self.textures_dict[current_state][idx]

    def shoot(self):
        self.state = "shoot"
        self.animation_timer = 0

        try:
            rocket = arcade.Sprite("first_room/images/rocket.png", scale=0.05)
        except:
            rocket = arcade.SpriteSolidColor(20, 10, arcade.color.RED)

        rocket.center_x = self.center_x
        rocket.center_y = self.center_y

        if self.player:
            dest_x = self.player.center_x
            dest_y = self.player.center_y
            angle = math.atan2(dest_y - self.center_y, dest_x - self.center_x)

            rocket.change_x = math.cos(angle) * 8
            rocket.change_y = math.sin(angle) * 8
            rocket.angle = math.degrees(angle)

            self.bullets.append(rocket)

    def take_damage(self, damage):
        if self.active and self.spawned:
            self.health -= damage
            if self.health <= 0:
                self.die()
                return True
        return False

    def die(self):
        self.active = False

    def update(self, delta_time):
        self.gibs.update()

        self.bullets.update()

        if not self.active:
            return

        self.animation_timer += delta_time

        if self.falling:
            self.center_y -= self.fall_speed
            if self.center_y <= self.target_y: 
                self.center_y = self.target_y
                self.falling = False
                self.state = "land"
                self.animation_timer = 0
            self.update_texture()
            return

        if self.player and self.spawned:
            dist = arcade.get_distance_between_sprites(self, self.player)
            self.facing_right = self.player.center_x > self.center_x

            if dist > self.min_dist_to_player:
                self.state = "dash"
                angle = math.atan2(self.player.center_y - self.center_y, self.player.center_x - self.center_x)
                self.center_x += math.cos(angle) * self.dash_speed
                self.center_y += math.sin(angle) * self.dash_speed
            else:
                if self.state == "dash":
                    self.state = "idle"

        self.shoot_timer -= delta_time
        if self.shoot_timer <= 0 and self.spawned and self.state not in ["land", "shoot"]:
            self.shoot()
            self.shoot_timer = self.shoot_cooldown

        if self.state in ["land", "shoot"] and self.animation_timer > 0.5:
            self.state = "idle"

        self.update_texture()

    def draw(self, **kwargs):
        self.gibs.draw()

        self.bullets.draw()

        if self.active and self.spawned:
            if hasattr(self, 'texture') and self.texture:
                arcade.draw_texture_rect(
                    self.texture,
                    arcade.rect.XYWH(
                        self.center_x,
                        self.center_y,
                        self.width,
                        self.height
                    )
                )
