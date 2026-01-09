import arcade
import random
import math
from arcade import Sprite

PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100

DASH_SPEED = 30
DASH_DURATION = 0.3
DASH_COOLDOWN = 1.0


class DustParticle(arcade.SpriteCircle):
    def __init__(self, x, y):
        color = random.choice([
            (200, 200, 200, 200),
            (180, 180, 180, 200),
            (220, 220, 220, 200),
            (190, 170, 150, 200)
        ])
        size = random.randint(3, 8)
        super().__init__(size, color)
        self.center_x = x
        self.center_y = y
        self.change_x = random.uniform(-1.5, 1.5)
        self.change_y = random.uniform(0, 2)

        self.scale = 1.0
        self.alpha = 200
        self.lifetime = random.uniform(0.5, 1.2)
        self.time_alive = 0

    def update(self, delta_time=1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y

        self.change_x *= 0.95
        self.change_y *= 0.95

        self.width *= 1.02
        self.height *= 1.005

        if self.alpha > 2:
            self.alpha -= 2

        self.time_alive += delta_time

        if self.time_alive > self.lifetime or self.alpha <= 0:
            self.remove_from_sprite_lists()


class Player(Sprite):
    def __init__(self, dash_unlocked=False):
        super().__init__()
        self.idle_texture = arcade.load_texture(":resources:images/enemies/frog.png")
        self.jump_texture = arcade.load_texture(":resources:images/enemies/frog_move.png")

        self.texture = self.idle_texture
        self.scale = PLAYER_SCALING
        self.center_x = 0
        self.center_y = 100
        self.change_x = 0
        self.change_y = 0

        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.invincible_timer = 0
        self.invincible_duration = 1.0

        self.on_ground = False
        self.jumping = False
        self.was_jumping = False

        self.dash_unlocked = dash_unlocked
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = 1
        self.normal_speed = PLAYER_MOVEMENT_SPEED

        self.last_safe_x = 0
        self.last_safe_y = 100

    def update_texture(self):
        if not self.on_ground:
            self.texture = self.jump_texture
        else:
            self.texture = self.idle_texture

    def take_damage(self, damage_percent):
        if self.invincible_timer <= 0:
            damage = self.max_hp * (damage_percent / 100)
            self.hp = max(0, self.hp - damage)
            self.invincible_timer = self.invincible_duration
            return True
        return False

    def heal(self, heal_amount):
        self.hp = min(self.max_hp, self.hp + heal_amount)

    def update(self, delta_time):
        if self.invincible_timer > 0:
            self.invincible_timer -= delta_time

        if self.dashing:
            self.dash_timer -= delta_time
            if self.dash_timer <= 0:
                self.dashing = False
                if abs(self.change_x) > PLAYER_MOVEMENT_SPEED:
                    self.change_x = self.normal_speed * (1 if self.change_x > 0 else -1)

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= delta_time

        if self.invincible_timer > 0:
            self.alpha = 150 + int(105 * math.sin(self.invincible_timer * 20))
        else:
            self.alpha = 255

    def activate_dash(self):
        if not self.dash_unlocked or self.dash_cooldown_timer > 0:
            return False

        if self.change_x == 0:
            dash_x = self.dash_direction * DASH_SPEED
        else:
            dash_x = (1 if self.change_x > 0 else -1) * DASH_SPEED
            self.dash_direction = 1 if self.change_x > 0 else -1

        self.dashing = True
        self.dash_timer = DASH_DURATION
        self.dash_cooldown_timer = DASH_COOLDOWN

        self.normal_speed = abs(self.change_x) if self.change_x != 0 else PLAYER_MOVEMENT_SPEED
        self.change_x = dash_x
        return True

    def unlock_dash(self):
        self.dash_unlocked = True
        return True

    def update_safe_position(self):
        if self.on_ground:
            self.last_safe_x = self.center_x
            self.last_safe_y = self.center_y

    def respawn_at_safe_position(self):
        self.center_x = self.last_safe_x
        self.center_y = self.last_safe_y + 50
        self.change_x = 0
        self.change_y = 0
        self.invincible_timer = self.invincible_duration

    def reset_position(self, x, y):
        self.center_x = x
        self.center_y = y
        self.last_safe_x = x
        self.last_safe_y = y
        self.change_x = 0
        self.change_y = 0
        self.hp = PLAYER_MAX_HP
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.invincible_timer = 0

    def can_dash(self):
        return self.dash_unlocked and self.dash_cooldown_timer <= 0