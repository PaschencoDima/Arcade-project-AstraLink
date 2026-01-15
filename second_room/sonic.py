import arcade
import math
import os


class Sonic(arcade.Sprite):
    def __init__(self, x, y, player=None):
        try:
            super().__init__("images/underground.png", scale=1.0)
        except:
            super().__init__(arcade.make_soft_circle_texture(50, arcade.color.BLUE), scale=1.0)

        self.center_x = x
        self.center_y = y
        self.player = player

        self.active = True
        self.health = 500
        self.max_health = 500
        self.contact_damage = 35
        self.spike_damage = 10

        self.state = "UNDERGROUND"
        self.animation_timer = 0
        self.texture_index = 0
        self.emerging_speed = 150

        self.spikes = arcade.SpriteList()
        self.attack_timer = 0
        self.attack_cooldown = 3.0

        self.textures_dict = {}
        self.scales_dict = {
            "underground": 0.8,
            "standing": 1.0,
            "scream": 1.2,
            "rolling": 0.9,
            "DEAD": 0.5
        }
        self.default_scale = 1.0

        self.load_textures()

        self.initial_y = y
        self.center_y = y - 100
        self.scale = self.scales_dict["underground"]

    def load_textures(self):
        main_path = "images/"

        self.textures_dict["standing"] = []
        for i in range(1, 4):
            texture_path = f"{main_path}stand_{i}.png"
            if os.path.exists(texture_path):
                texture = arcade.load_texture(texture_path)
                self.textures_dict["standing"].append(texture)
            else:
                self.textures_dict["standing"].append(
                    arcade.make_soft_circle_texture(30,
                                                    [arcade.color.BLUE, arcade.color.DARK_BLUE,
                                                     arcade.color.LIGHT_BLUE][i - 1])
                )

        underground_path = f"{main_path}underground.png"
        if os.path.exists(underground_path):
            self.textures_dict["underground"] = arcade.load_texture(underground_path)
        else:
            self.textures_dict["underground"] = arcade.make_soft_circle_texture(40, arcade.color.BROWN)

        scream_path = f"{main_path}scream.png"
        if os.path.exists(scream_path):
            self.textures_dict["scream"] = arcade.load_texture(scream_path)
        else:
            self.textures_dict["scream"] = arcade.make_soft_circle_texture(35, arcade.color.RED)

        ball_path = f"{main_path}ball.png"
        if os.path.exists(ball_path):
            self.textures_dict["rolling"] = arcade.load_texture(ball_path)
        else:
            self.textures_dict["rolling"] = arcade.make_soft_circle_texture(25, arcade.color.DARK_BLUE)

        self.texture = self.textures_dict["underground"]

    def set_scale_for_state(self, state):
        scale_map = {
            "UNDERGROUND": 0.15,
            "EMERGING": 0.2,
            "STANDING": 0.5,
            "SCREAM": 0.2,
            "ROLLING": 0.2,
            "DEAD": 0.5
        }

        if state in scale_map:
            self.scale = scale_map[state]
        else:
            self.scale = self.default_scale

    def spawn_spikes(self):
        if self.state == "DEAD":
            return

        self.state = "SCREAM"
        self.animation_timer = 0
        self.texture = self.textures_dict["scream"]
        self.set_scale_for_state("SCREAM")

        self.spikes.clear()

        angles = [0, 45, 90, 135, 180, 225, 270, 315]

        spike_texture_path = "images/enemy_spike.png"
        spike_texture = None
        if os.path.exists(spike_texture_path):
            spike_texture = arcade.load_texture(spike_texture_path)

        for angle in angles:
            if spike_texture:
                spike = arcade.Sprite()
                spike.texture = spike_texture
                spike.scale = 0.1
            else:
                spike = arcade.SpriteSolidColor(15, 15, arcade.color.RED)

            spike.center_x = self.center_x
            spike.center_y = self.center_y

            rad = math.radians(angle)
            speed = 6
            spike.change_x = math.cos(rad) * speed
            spike.change_y = math.sin(rad) * speed

            spike.change_angle = 5 if angle % 2 == 0 else -5

            spike.damage = self.spike_damage

            self.spikes.append(spike)

    def update_animation(self, delta_time ):
        self.animation_timer += delta_time

        if self.state == "UNDERGROUND":
            self.texture = self.textures_dict["underground"]
            self.set_scale_for_state("UNDERGROUND")
            self.center_y += self.emerging_speed * delta_time
            if self.center_y >= self.initial_y:
                self.center_y = self.initial_y
                self.state = "EMERGING"
                self.animation_timer = 0
                self.set_scale_for_state("EMERGING")

        elif self.state == "EMERGING":
            self.texture = self.textures_dict["underground"]
            if self.animation_timer > 1.0:
                self.state = "STANDING"
                self.animation_timer = 0
                self.texture = self.textures_dict["standing"][0]
                self.set_scale_for_state("STANDING")

        elif self.state == "STANDING":
            if self.animation_timer > 0.2:
                self.animation_timer = 0
                self.texture_index = (self.texture_index + 1) % len(self.textures_dict["standing"])
                self.texture = self.textures_dict["standing"][self.texture_index]

        elif self.state == "SCREAM":
            self.texture = self.textures_dict["scream"]
            self.set_scale_for_state("SCREAM")

            if self.animation_timer > 1.0:
                self.state = "STANDING"
                self.animation_timer = 0
                self.texture_index = 0
                self.texture = self.textures_dict["standing"][0]
                self.set_scale_for_state("STANDING")

        elif self.state == "DEAD":
            self.alpha = max(0, self.alpha - 100 * delta_time)
            for spike in self.spikes:
                spike.alpha = max(0, spike.alpha - 150 * delta_time)
            if self.alpha <= 0:
                self.active = False
                self.remove_from_sprite_lists()

    def update(self, delta_time):
        if not self.active:
            return

        self.spikes.update()
        self.update_animation(delta_time)

        if self.state == "STANDING":
            self.attack_timer += delta_time
            if self.attack_timer >= self.attack_cooldown:
                self.spawn_spikes()
                self.attack_timer = 0

        screen_width = 1600
        screen_height = 900
        margin = 100

        for spike in self.spikes:
            if (spike.center_x < -margin or spike.center_x > screen_width + margin or
                    spike.center_y < -margin or spike.center_y > screen_height + margin):
                spike.remove_from_sprite_lists()

        if self.player:
            if arcade.check_for_collision(self, self.player):
                if hasattr(self.player, 'take_damage'):
                    self.player.take_damage(self.contact_damage)

            hit_spikes = arcade.check_for_collision_with_list(self.player, self.spikes)
            for spike in hit_spikes:
                if hasattr(self.player, 'take_damage'):
                    self.player.take_damage(self.spike_damage)
                spike.remove_from_sprite_lists()

    def draw_health_bar(self):
        if not self.active or self.state == "DEAD":
            return

        bar_width = 120
        bar_height = 12
        bar_y_offset = 60
        health_ratio = max(0, self.health / self.max_health)

        arcade.draw_rect_filled(arcade.rect.XYWH(
            self.center_x,
            self.center_y + bar_y_offset,
            bar_width + 4,
            bar_height + 4),
            arcade.color.BLACK
        )

        arcade.draw_rect_filled(arcade.rect.XYWH(
            self.center_x,
            self.center_y + bar_y_offset,
            bar_width,
            bar_height),
            arcade.color.DARK_RED
        )

        if health_ratio > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(
                self.center_x - (bar_width / 2) + (bar_width * health_ratio / 2),
                self.center_y + bar_y_offset,
                bar_width * health_ratio,
                bar_height),
                arcade.color.GREEN
            )

        health_text = f"{int(self.health)}/{self.max_health}"
        arcade.draw_text(
            health_text,
            self.center_x,
            self.center_y + bar_y_offset - 1,
            arcade.color.BLACK,
            10,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

    def take_damage(self, damage):
        if not self.active or self.state == "DEAD":
            return

        self.health -= damage

        if self.alpha == 255:
            self.alpha = 180
        else:
            self.alpha = 255

        if self.health <= 0:
            self.health = 0
            self.state = "DEAD"
            self.animation_timer = 0
            self.set_scale_for_state("DEAD")
            self.alpha = 255

    def reset(self):
        self.active = True
        self.health = self.max_health
        self.state = "UNDERGROUND"
        self.center_y = self.initial_y - 100
        self.animation_timer = 0
        self.texture_index = 0
        self.attack_timer = 0
        self.spikes.clear()
        self.texture = self.textures_dict["underground"]
        self.set_scale_for_state("UNDERGROUND")
        self.alpha = 255