import arcade
import math
import os
import random


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

        self.walking_speed = 2.5
        self.walk_range = 300
        self.start_x = x
        self.direction = 1
        self.is_facing_right = True

        self.ball_attack_distance = 500
        self.ball_start_x = 0
        self.ball_target_x = 0
        self.ball_speed = 2
        self.ball_max_speed = 8
        self.ball_acceleration = 1.5
        self.ball_attacking = False
        self.ball_damage = 40

        self.spikes = arcade.SpriteList()
        self.attack_timer = 0
        self.attack_cooldown = 3.0

        self.textures_dict = {}
        self.scales_dict = {
            "UNDERGROUND": 0.3,
            "EMERGING": 0.3,
            "STANDING": 0.5,
            "SCREAM": 0.2,
            "BALL_ATTACK": 0.15,
            "DEAD": 0.5
        }
        self.default_scale = 1.0

        self.load_textures()

        self.initial_y = y
        self.center_y = y - 50
        self.scale = self.scales_dict["UNDERGROUND"]
        self.angle = 0

    def load_textures(self):
        main_path = "images/"

        self.textures_dict["standing"] = []
        for i in range(1, 4):
            texture_path = f"{main_path}stand_{i}.png"
            if os.path.exists(texture_path):
                texture = arcade.load_texture(texture_path)
                self.textures_dict["standing"].append({
                    "right": texture,
                    "left": texture.flip_left_right()
                })
            else:
                texture_right = arcade.make_soft_circle_texture(30, [arcade.color.BLUE, arcade.color.DARK_BLUE,
                                                                     arcade.color.LIGHT_BLUE][i - 1])
                texture_left = texture_right
                self.textures_dict["standing"].append({
                    "right": texture_right,
                    "left": texture_left
                })

        underground_path = f"{main_path}underground.png"
        if os.path.exists(underground_path):
            texture = arcade.load_texture(underground_path)
            self.textures_dict["underground"] = {
                "right": texture,
                "left": texture.flip_left_right()
            }
        else:
            texture = arcade.make_soft_circle_texture(40, arcade.color.BROWN)
            self.textures_dict["underground"] = {
                "right": texture,
                "left": texture
            }

        scream_path = f"{main_path}scream.png"
        if os.path.exists(scream_path):
            texture = arcade.load_texture(scream_path)
            self.textures_dict["scream"] = {
                "right": texture,
                "left": texture.flip_left_right()
            }
        else:
            texture = arcade.make_soft_circle_texture(35, arcade.color.RED)
            self.textures_dict["scream"] = {
                "right": texture,
                "left": texture
            }

        ball_path = f"{main_path}ball.png"
        if os.path.exists(ball_path):
            texture = arcade.load_texture(ball_path)
            self.textures_dict["rolling"] = {
                "right": texture,
                "left": texture.flip_left_right()
            }
        else:
            texture = arcade.make_soft_circle_texture(25, arcade.color.DARK_BLUE)
            self.textures_dict["rolling"] = {
                "right": texture,
                "left": texture
            }

        self.texture = self.textures_dict["underground"]["right"]

    def get_texture_for_state(self):
        direction_key = "right" if self.is_facing_right else "left"

        if self.state == "STANDING":
            return self.textures_dict["standing"][self.texture_index][direction_key]
        elif self.state == "UNDERGROUND":
            return self.textures_dict["underground"][direction_key]
        elif self.state == "EMERGING":
            return self.textures_dict["underground"][direction_key]
        elif self.state == "SCREAM":
            return self.textures_dict["scream"][direction_key]
        elif self.state == "BALL_ATTACK":
            return self.textures_dict["rolling"][direction_key]
        elif self.state == "DEAD":
            return self.texture

        return self.texture

    def set_scale_for_state(self, state):
        try:
            if state in self.scales_dict:
                self.scale = self.scales_dict[state]
            else:
                self.scale = self.default_scale
        except Exception as e:
            self.scale = self.default_scale

    def start_ball_attack(self):
        if self.state == "DEAD" or self.ball_attacking:
            return

        self.state = "BALL_ATTACK"
        self.ball_attacking = True
        self.animation_timer = 0

        if self.player and self.player.center_x > self.center_x:
            self.direction = 1
            self.is_facing_right = True
        else:
            self.direction = -1
            self.is_facing_right = False

        self.ball_start_x = self.center_x
        self.ball_target_x = self.center_x + (self.ball_attack_distance * self.direction)

        self.ball_speed = 4
        self.animation_timer = 0
        self.angle = 0

        self.texture = self.get_texture_for_state()
        self.set_scale_for_state("BALL_ATTACK")

    def update_ball_attack(self, delta_time):
        if not self.ball_attacking or self.state == "DEAD":
            return False

        self.ball_speed = min(self.ball_speed + self.ball_acceleration * delta_time * 60, self.ball_max_speed)

        self.center_x += self.ball_speed * self.direction

        self.angle += 20 * self.direction * self.ball_speed * delta_time

        distance_traveled = abs(self.center_x - self.ball_start_x)

        if distance_traveled >= self.ball_attack_distance:
            self.ball_attacking = False
            self.state = "STANDING"
            self.animation_timer = 0
            self.texture_index = 0
            self.angle = 0
            self.texture = self.get_texture_for_state()
            self.set_scale_for_state("STANDING")
            return True

        return False

    def spawn_spikes(self):
        if self.state == "DEAD":
            return

        self.state = "SCREAM"
        self.animation_timer = 0
        self.texture = self.get_texture_for_state()
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
                spike = arcade.SpriteSolidColor(25, 25, arcade.color.RED)

            spike.center_x = self.center_x
            spike.center_y = self.center_y

            rad = math.radians(angle)
            speed = 6
            spike.change_x = math.cos(rad) * speed
            spike.change_y = math.sin(rad) * speed

            spike.change_angle = 5 if angle % 2 == 0 else -5

            spike.damage = self.spike_damage

            self.spikes.append(spike)

    def walk_patrol(self):
        if self.state not in ["STANDING", "SCREAM"]:
            return

        left_bound = self.start_x - self.walk_range / 2
        right_bound = self.start_x + self.walk_range / 2

        old_direction = self.is_facing_right

        if self.center_x >= right_bound:
            self.direction = -1
            self.is_facing_right = False
        elif self.center_x <= left_bound:
            self.direction = 1
            self.is_facing_right = True

        self.center_x += self.walking_speed * self.direction

        if old_direction != self.is_facing_right:
            self.texture = self.get_texture_for_state()

    def face_player(self):
        if not self.player:
            return

        distance_to_player = abs(self.center_x - self.player.center_x)

        if distance_to_player < 400 and self.state == "STANDING":
            old_direction = self.is_facing_right

            if self.player.center_x < self.center_x:
                self.is_facing_right = False
                self.direction = -1
            else:
                self.is_facing_right = True
                self.direction = 1

            if old_direction != self.is_facing_right:
                self.texture = self.get_texture_for_state()

    def update_animation(self, delta_time):
        self.animation_timer += delta_time

        if self.state == "UNDERGROUND":
            self.texture = self.get_texture_for_state()
            self.set_scale_for_state("UNDERGROUND")
            self.center_y += self.emerging_speed * delta_time
            if self.center_y >= self.initial_y:
                self.center_y = self.initial_y
                self.state = "EMERGING"
                self.animation_timer = 0
                self.set_scale_for_state("EMERGING")

        elif self.state == "EMERGING":
            self.texture = self.get_texture_for_state()
            self.set_scale_for_state("EMERGING")
            if self.center_y < self.initial_y + 20:
                self.center_y += self.emerging_speed * delta_time * 0.5
            if self.animation_timer > 1.0:
                self.state = "STANDING"
                self.animation_timer = 0
                self.texture_index = 0
                self.texture = self.get_texture_for_state()
                self.set_scale_for_state("STANDING")

        elif self.state == "STANDING":
            self.set_scale_for_state("STANDING")
            if self.animation_timer > 0.2:
                self.animation_timer = 0
                self.texture_index = (self.texture_index + 1) % len(self.textures_dict["standing"])
                self.texture = self.get_texture_for_state()

        elif self.state == "SCREAM":
            self.texture = self.get_texture_for_state()
            self.set_scale_for_state("SCREAM")

            if self.animation_timer > 1.0:
                self.state = "STANDING"
                self.animation_timer = 0
                self.texture_index = 0
                self.texture = self.get_texture_for_state()
                self.set_scale_for_state("STANDING")

        elif self.state == "DEAD":
            self.set_scale_for_state("DEAD")
            if self.animation_timer > 0.5:
                self.alpha = max(0, self.alpha - 300 * delta_time)
            for spike in self.spikes:
                spike.alpha = max(0, spike.alpha - 150 * delta_time)
            if self.alpha <= 0:
                self.active = False

    def update(self, delta_time):
        if not self.active:
            return

        self.spikes.update()
        self.update_animation(delta_time)

        if self.state == "BALL_ATTACK":
            self.update_ball_attack(delta_time)
        elif self.state == "STANDING":
            self.walk_patrol()
            self.face_player()

            self.attack_timer += delta_time
            if self.attack_timer >= self.attack_cooldown:
                if self.player and random.random() < 0.5:
                    distance_to_player = abs(self.center_x - self.player.center_x)
                    if distance_to_player < 600:
                        self.start_ball_attack()
                    else:
                        self.spawn_spikes()
                else:
                    self.spawn_spikes()
                self.attack_timer = 0

        screen_width = 3200
        screen_height = 1800
        margin = 500

        for spike in self.spikes:
            if (spike.center_x < -margin or spike.center_x > screen_width + margin or
                    spike.center_y < -margin or spike.center_y > screen_height + margin):
                spike.remove_from_sprite_lists()

        if self.player:
            if self.state == "BALL_ATTACK" and arcade.check_for_collision(self, self.player):
                if hasattr(self.player, 'take_damage'):
                    self.player.take_damage(self.ball_damage)

            elif self.state != "BALL_ATTACK" and arcade.check_for_collision(self, self.player):
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

        if self.alpha < 255:
            self.alpha = 255

        if self.health <= 0:
            self.health = 0
            self.state = "DEAD"
            self.animation_timer = 0
            self.scale = self.scales_dict["DEAD"]
            self.ball_attacking = False
            self.angle = 0
            self.ball_speed = 0
            self.texture = self.get_texture_for_state()

    def reset(self):
        self.active = True
        self.health = self.max_health
        self.state = "UNDERGROUND"
        self.center_x = self.start_x
        self.center_y = self.initial_y - 100
        self.animation_timer = 0
        self.texture_index = 0
        self.attack_timer = 0
        self.direction = 1
        self.is_facing_right = True
        self.ball_attacking = False
        self.angle = 0
        self.spikes.clear()
        self.texture = self.get_texture_for_state()
        self.set_scale_for_state("UNDERGROUND")
        self.alpha = 255