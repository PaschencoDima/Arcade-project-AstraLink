import arcade
import random
import math
import os

# Константы
PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100
DASH_SPEED = 40
DASH_DURATION = 0.2
DASH_COOLDOWN = 1.0


class DustParticle(arcade.SpriteCircle):
    def __init__(self, x, y):
        color = random.choice([
            (200, 200, 200, 200), (180, 180, 180, 200),
            (220, 220, 220, 200), (190, 170, 150, 200)
        ])
        size = random.randint(3, 8)
        super().__init__(size, color)
        self.center_x, self.center_y = x, y
        self.change_x = random.uniform(-1.5, 1.5)
        self.change_y = random.uniform(0, 2)
        self.alpha = 200
        self.lifetime = random.uniform(0.5, 1.2)
        self.time_alive = 0

    def update(self, delta_time=1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.change_x *= 0.95
        self.change_y *= 0.95
        if self.alpha > 2: self.alpha -= 2
        self.time_alive += delta_time
        if self.time_alive > self.lifetime or self.alpha <= 0:
            self.remove_from_sprite_lists()


class Player(arcade.Sprite):
    def __init__(self, dash_unlocked=False):
        super().__init__(":resources:images/enemies/frog.png", PLAYER_SCALING)

        # Текстуры игрока
        self.idle_texture = arcade.load_texture(":resources:images/enemies/frog.png")
        self.jump_texture = arcade.load_texture(":resources:images/enemies/frog_move.png")
        self.texture = self.idle_texture

        # Параметры трансформации
        self.center_x, self.center_y = 0, 100
        self.change_x = 0
        self.change_y = 0
        self.scale_x = PLAYER_SCALING
        self.scale_y = PLAYER_SCALING
        self.facing_right = True

        # Состояние здоровья
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.invincible_timer = 0
        self.invincible_duration = 1.0

        # Физические состояния (Добавлены все нужные атрибуты)
        self.on_ground = False
        self.jumping = False
        self.was_jumping = False  # Исправлено: теперь атрибут существует

        # Способности (Dash)
        self.dash_unlocked = dash_unlocked
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = 1
        self.normal_speed = PLAYER_MOVEMENT_SPEED

        # Респаун
        self.last_safe_x = 0
        self.last_safe_y = 100

        # Атака (Рисуется отдельно от игрока)
        self.attacking = False
        self.attack_timer = 0
        self.attack_phase = 0
        self.attack_type = 1
        self.attack_damage = 40
        self.attack_total_damage = 0
        self.attack_duration = 0.05
        self.attack_cooldown = 0.3
        self.can_deal_damage = False
        self.saved_change_x = 0
        self.saved_change_y = 0

        self.dust_list = arcade.SpriteList()
        self.attack_textures_atack1 = []
        self.attack_textures_atack2 = []
        self.load_attack_textures()

    def load_attack_textures(self):
        for i in range(1, 9):
            path = f"player_images/atack_1/phase_{i}.png"
            self.attack_textures_atack1.append(arcade.load_texture(path) if os.path.exists(path)
                                               else arcade.make_soft_square_texture(64, (255, 50, 50, 150)))
        for i in range(1, 7):
            path = f"player_images/atack_2/phase_{i}.png"
            self.attack_textures_atack2.append(arcade.load_texture(path) if os.path.exists(path)
                                               else arcade.make_soft_square_texture(64, (50, 255, 50, 150)))

    def update_texture(self):
        if not self.on_ground:
            self.texture = self.jump_texture
        else:
            self.texture = self.idle_texture

    def start_attack(self):
        if not self.attacking and self.attack_timer <= 0:
            self.attacking, self.attack_phase, self.can_deal_damage = True, 0, True
            self.attack_timer = self.attack_duration
            self.saved_change_x, self.saved_change_y = self.change_x, self.change_y
            return True
        return False

    def update_attack(self, delta_time):
        if self.attacking:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0:
                self.attack_phase += 1
                self.attack_timer = self.attack_duration
                self.can_deal_damage = True
                max_p = 8 if self.attack_type == 1 else 6
                if self.attack_phase >= max_p: self.end_attack()
        elif self.attack_timer > 0:
            self.attack_timer -= delta_time

    def end_attack(self):
        self.attacking = False
        self.attack_type = 2 if self.attack_type == 1 else 1
        self.attack_timer, self.can_deal_damage = self.attack_cooldown, False

    def deal_damage(self):
        if self.can_deal_damage:
            self.can_deal_damage = False
            recoil = 6.0
            if self.facing_right:
                self.center_x -= recoil
            else:
                self.center_x += recoil
            return self.attack_damage
        return 0

    def get_attack_hitbox(self):
        if not self.attacking or not self.can_deal_damage: return None
        hit_w, hit_h = 130, 50
        offset_x = 70 if self.facing_right else -70
        left = (self.center_x + offset_x) - hit_w / 2
        bottom = self.center_y - hit_h / 2
        return (left, left + hit_w, bottom, bottom + hit_h)

    def set_direction(self, facing_right):
        self.facing_right = facing_right
        self.scale_x = -PLAYER_SCALING if facing_right else PLAYER_SCALING

    def activate_dash(self):
        if not self.dash_unlocked or self.dash_cooldown_timer > 0 or self.dashing: return False
        self.dashing, self.dash_timer, self.dash_cooldown_timer = True, DASH_DURATION, DASH_COOLDOWN
        dir = (1 if self.change_x > 0 else -1) if self.change_x != 0 else (1 if self.facing_right else -1)
        self.dash_direction = dir
        self.normal_speed = abs(self.change_x) if self.change_x != 0 else PLAYER_MOVEMENT_SPEED
        self.change_x = dir * DASH_SPEED
        return True

    def reset_position(self, x, y):
        self.center_x, self.center_y = x, y
        self.last_safe_x, self.last_safe_y = x, y
        self.change_x = self.change_y = 0
        self.hp = PLAYER_MAX_HP
        self.dashing = self.attacking = False
        self.dash_timer = self.dash_cooldown_timer = self.invincible_timer = 0
        self.facing_right = True
        self.set_direction(True)

    def take_damage(self, damage_percent):
        if self.invincible_timer <= 0:
            self.hp -= (self.max_hp * damage_percent / 100)
            self.invincible_timer = self.invincible_duration
            return True
        return False

    def update(self, delta_time=1 / 60):
        if self.invincible_timer > 0:
            self.invincible_timer -= delta_time
            self.alpha = 150 + int(105 * math.sin(self.invincible_timer * 20))
        else:
            self.alpha = 255

        if self.dashing:
            self.dash_timer -= delta_time
            if self.dash_timer <= 0:
                self.dashing = False
                if abs(self.change_x) > PLAYER_MOVEMENT_SPEED:
                    self.change_x = self.normal_speed * (1 if self.change_x > 0 else -1)

        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= delta_time

        self.update_attack(delta_time)
        if not self.attacking:
            if self.change_x > 0:
                self.set_direction(True)
            elif self.change_x < 0:
                self.set_direction(False)

        if self.on_ground and abs(self.change_x) > 0.1 and random.random() < 0.1:
            self.dust_list.append(DustParticle(self.center_x, self.bottom))

        self.dust_list.update()
        self.update_texture()
        self.was_jumping = self.jumping

    def draw(self, **kwargs):
        self.dust_list.draw()
        # 1. Тело игрока
        arcade.draw_texture_rect(
            texture=self.texture,
            rect=arcade.rect.XYWH(self.center_x, self.center_y,
                                  self.texture.width * self.scale_x,
                                  self.texture.height * self.scale_y),
            alpha=self.alpha
        )
        if self.attacking:
            textures = self.attack_textures_atack1 if self.attack_type == 1 else self.attack_textures_atack2
            if self.attack_phase < len(textures):
                cur_frame = textures[self.attack_phase]
                attack_scale = 5.0
                offset_x = 70 if self.facing_right else -70
                arcade.draw_texture_rect(
                    texture=cur_frame,
                    rect=arcade.rect.XYWH(self.center_x + offset_x, self.center_y,
                                          cur_frame.width * (attack_scale if self.facing_right else -attack_scale),
                                          cur_frame.height * attack_scale * 0.5),  # Высота уменьшена в 2 раза
                    alpha=255
                )

    # Вспомогательные заглушки
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def unlock_dash(self):
        self.dash_unlocked = True

    def can_dash(self):
        return self.dash_unlocked and self.dash_cooldown_timer <= 0

    def can_attack(self):
        return not self.attacking and self.attack_timer <= 0

    def update_safe_position(self):
        if self.on_ground: self.last_safe_x, self.last_safe_y = self.center_x, self.center_y

    def respawn_at_safe_position(self):
        self.center_x, self.center_y = self.last_safe_x, self.last_safe_y + 50
        self.change_x = self.change_y = 0
