import arcade
from third_room.config import *
import math


class Boss(arcade.Sprite):
    def __init__(self, x, y, player):
        super().__init__()

        self.center_x = x
        self.center_y = y

        self.width = 130
        self.height = 130

        self.spawned = False
        self.direction = "right"
        self.state = "walk"
        self.contact_damage = 30
        self.bullet_damage = 40

        self.player = player

        self.max_health = 1500
        self.health = 1500

        self.speed = 5

        self.attack_distance = 80
        self.bullet_texture = arcade.load_texture("third_room/images/boss/Rock2.png")
        self.bullet_list = arcade.SpriteList()
        self.shooting_timer = 0

        self.textures = {
            "right": [
                arcade.load_texture("third_room/images/boss/1.png"),
                arcade.load_texture("third_room/images/boss/3.png"),
                arcade.load_texture("third_room/images/boss/4.png"),
                arcade.load_texture("third_room/images/boss/5.png"),
                arcade.load_texture("third_room/images/boss/6.png"),
            ],
            "left": [
                arcade.load_texture("third_room/images/boss/1.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/3.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/4.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/5.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/6.png").flip_left_right(),
            ]
        }
        self.attack_textures = {
            "right": [
                arcade.load_texture("third_room/images/boss/1.png"),
                arcade.load_texture("third_room/images/boss/2.png"),
                arcade.load_texture("third_room/images/boss/attack/3.png"),
                arcade.load_texture("third_room/images/boss/attack/4.png"),
                arcade.load_texture("third_room/images/boss/attack/5.png")
            ],
            "left": [
                arcade.load_texture("third_room/images/boss/1.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/2.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/attack/3.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/attack/4.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/attack/5.png").flip_left_right()
            ]
        }
        self.death_textures = {
            "right": [
                arcade.load_texture("third_room/images/boss/umer/1.png"),
                arcade.load_texture("third_room/images/boss/umer/2.png"),
                arcade.load_texture("third_room/images/boss/umer/3.png"),
                arcade.load_texture("third_room/images/boss/umer/4.png"),
                arcade.load_texture("third_room/images/boss/umer/5.png"),
                arcade.load_texture("third_room/images/boss/umer/6.png"),
                arcade.load_texture("third_room/images/boss/umer/7.png")
            ],
            "left": [
                arcade.load_texture("third_room/images/boss/umer/1.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/umer/2.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/umer/3.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/umer/4.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/umer/5.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/umer/6.png").flip_left_right(),
                arcade.load_texture("third_room/images/boss/umer/7.png").flip_left_right()
            ]
        }
        self.dead_animation_cancel = False
        self.cur_texture = 0
        self.texture = self.textures[self.direction][self.cur_texture]
        self.timer = 0

    def spawn(self):
        self.spawned = True

    def change_direction(self):
        if self.direction == "left":
            self.direction = "right"
        else:
            self.direction = "left"

    def run(self, delta_time):
        if self.center_x + self.width // 2 >= SCREEN_WIDTH * 2 - 20:
            self.direction = "left"
        if self.center_x - self.width // 2 < 1200:
            self.direction = "right"
        coof = 1
        if self.direction == "left":
            coof = -1
        self.center_x += self.speed * coof

    def draw_health_bar(self):
        if not self.spawned or self.state == "dead":
            return

        bar_width = 120
        bar_height = 12
        bar_y_offset = 70
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
        if not self.spawned or self.state == "dead":
            return

        self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.state = "dead"

        return True
 
    def update_animation(self, delta_time):
        if not self.spawned or self.dead_animation_cancel:
            return
        if self.state == "dead":
            self.cur_texture += 1
            # Меняем кадр каждые 0.1 секунды
            if self.cur_texture < len(self.death_textures[self.direction]):
                self.texture = self.death_textures[self.direction][self.cur_texture]
            else:
                self.dead_animation_cancel = True
                self.remove_from_sprite_lists()
        elif self.state != "attack":
            self.timer += delta_time
            # Меняем кадр каждые 0.1 секунды
            if self.timer > 0.1:
                self.cur_texture = (self.cur_texture + 1) % len(self.textures[self.direction])
                self.texture = self.textures[self.direction][self.cur_texture]
                self.timer = 0
        else:
            self.timer += delta_time
            # Меняем кадр каждые 0.1 секунды
            if self.timer > 0.2:
                self.cur_texture = (self.cur_texture + 1) % len(self.attack_textures[self.direction])
                self.texture = self.attack_textures[self.direction][self.cur_texture]
                self.timer = 0

    def reset_player(self):
        self.player.center_x = 0
        self.player.center_y = 100
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.hp = PLAYER_MAX_HP

        self.player.dashing = False
        self.player.dash_timer = 0
        self.player.dash_cooldown_timer = 0

        self.player.invincible_timer = 0

    def next_to_player(self):
        # Вычисляем расстояние
        start_x = self.center_x
        dest_x = self.player.center_x

        x_diff = dest_x - start_x
        angle = math.atan2(0, x_diff)

        # Двигаем врага
        if self.player.center_x > self.center_x:
            self.direction = "right"
        else:
            self.direction = "left"
        self.center_x += self.speed * math.cos(angle)

    def attacking(self, delta_time):
        self.shooting_timer += delta_time
        if self.shooting_timer >= 1.5:
            self.shooting_timer = 0
            self.shoot()
        for bullet in self.bullet_list:
            if bullet.bottom < 40 or bullet.left < 1220 or bullet.right > SCREEN_WIDTH * 2 - 20:
                bullet.remove_from_sprite_lists()

        if arcade.check_for_collision(self, self.player) or \
                abs(self.player.center_x - self.center_x) < self.attack_distance * 2 and\
                abs(self.center_y - self.player.center_x) < 220:
            if hasattr(self.player, 'take_damage'):
                self.player.take_damage(self.contact_damage)

    def player_attack(self):
        hitbox = self.player.get_attack_hitbox()
        if not hitbox:
            return

        attack_left, attack_right, attack_bottom, attack_top = hitbox

        if self.spawned and self.state != "dead":
            if (attack_right > self.left and
                    attack_left < self.right and
                    attack_top > self.bottom and
                    attack_bottom < self.top):

                damage = self.player.deal_damage()
                if damage > 0:
                    self.take_damage(damage)
                    if self.health <= 0:
                        self.state = "dead"

    def shoot(self):
        # Создаем предмет (снаряд)
        bullet = arcade.Sprite(self.bullet_texture)
        bullet.scale = 3
        bullet.center_x = self.center_x
        bullet.center_y = self.center_y

        x_diff = self.player.center_x - self.center_x
        y_diff = -50

        angle = math.atan2(y_diff, x_diff)

        bullet_speed = 5
        bullet.change_x = math.cos(angle) * bullet_speed
        bullet.change_y = math.sin(angle) * bullet_speed

        # Добавляем в список
        self.bullet_list.append(bullet)

    def update(self, delta_time):
        if not self.spawned or self.state == "dead":
            return
        if (self.player.center_y - self.center_y) <= 50 and self.player.center_x > 1200:
            self.state = "pursuit"
        if abs(self.player.center_x - self.center_x) < 300:
            self.state = "attack"
        if self.state == "walk":
            self.run(delta_time)
        if self.state == "pursuit":
            self.next_to_player()
        if self.state == "attack":
            self.attacking(delta_time)
            self.bullet_list.update()
        bullet_hit = arcade.check_for_collision_with_list(self.player, self.bullet_list)
        for bullet in bullet_hit:
            bullet.remove_from_sprite_lists()
            if hasattr(self.player, 'take_damage'):
                self.player.take_damage(self.bullet_damage)
        self.player_attack()

    def draw(self):
        if not self.spawned or self.dead_animation_cancel:
            return
        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(
                self.center_x,
                self.center_y,
                self.width,
                self.height
            )
        )
        self.bullet_list.draw()
        self.draw_health_bar()