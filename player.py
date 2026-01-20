import arcade
import random
import math
import os

PLAYER_SCALING = 0.3
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100
DASH_SPEED = 30
DASH_DURATION = 0.3
DASH_COOLDOWN = 1.0
ATTACK_DURATION = 0.02
ATTACK_COOLDOWN = 0.3
ANIMATION_SPEED = 0.2

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
        if self.alpha > 2:
            self.alpha -= 2
        self.time_alive += delta_time
        if self.time_alive > self.lifetime or self.alpha <= 0:
            self.remove_from_sprite_lists()

class Player(arcade.Sprite):
    def __init__(self, dash_unlocked=False):
        super().__init__(scale=PLAYER_SCALING)
        self.animations = {
            "stand": [],
            "run": [],
            "jump_start": [],
            "jump": [],
            "dash": [],
        }
        self.animation_scales = {
            "stand": [1.2, 1.2],
            "run": [1.0, 1.0],
            "jump_start": [1.2],
            "jump": [1.0, 0.9],
            "dash": [1.1, 1.1, 1.1],
        }
        self.attack_textures_atack1 = []
        self.attack_textures_atack2 = []
        self.load_animations()
        self.load_attack_textures()
        self.center_x, self.center_y = 0, 100
        self.change_x = 0
        self.change_y = 0
        self.facing_right = True
        self.state = "stand"
        self.animation_timer = 0
        self.current_frame = 0
        self.current_scale = 1.0
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
        self.attacking = False
        self.attack_timer = 0
        self.attack_phase = 0
        self.attack_type = 1
        self.attack_damage = 10
        self.attack_total_damage = 0
        self.can_deal_damage = False
        self.saved_change_x = 0
        self.saved_change_y = 0
        self.dust_list = arcade.SpriteList()
        self.texture = self.animations["stand"][0] if self.animations["stand"] else None

    def load_animations(self):
        try:
            self.animations["stand"] = [
                arcade.load_texture("player_images/stand_1.png"),
                arcade.load_texture("player_images/stand_1.png")
            ]
        except:
            self.animations["stand"] = [
                arcade.make_soft_square_texture(50, (100, 200, 100)),
                arcade.make_soft_square_texture(50, (120, 220, 120))
            ]
        try:
            self.animations["run"] = [
                arcade.load_texture("player_images/run_1.png"),
                arcade.load_texture("player_images/stand_2.png")
            ]
        except:
            self.animations["run"] = [
                arcade.make_soft_square_texture(50, (100, 150, 200)),
                arcade.make_soft_square_texture(50, (120, 170, 220))
            ]
        try:
            self.animations["jump_start"] = [
                arcade.load_texture("player_images/jump_start.png")
            ]
        except:
            self.animations["jump_start"] = [
                arcade.make_soft_square_texture(50, (200, 150, 100))
            ]
        try:
            self.animations["jump"] = [
                arcade.load_texture("player_images/jump_1.png"),
                arcade.load_texture("player_images/jump_2.png")
            ]
        except:
            self.animations["jump"] = [
                arcade.make_soft_square_texture(50, (200, 200, 100)),
                arcade.make_soft_square_texture(50, (220, 220, 120))
            ]
        try:
            self.animations["dash"] = [
                arcade.load_texture("player_images/dash_1.png"),
                arcade.load_texture("player_images/dash_2.png"),
                arcade.load_texture("player_images/dash_3.png")
            ]
        except:
            self.animations["dash"] = [
                arcade.make_soft_square_texture(50, (255, 100, 100)),
                arcade.make_soft_square_texture(50, (255, 150, 150)),
                arcade.make_soft_square_texture(50, (255, 100, 100))
            ]

    def load_attack_textures(self):
        for i in range(1, 9):
            path = f"player_images/atack_1/phase_{i}.png"
            if os.path.exists(path):
                self.attack_textures_atack1.append(arcade.load_texture(path))
            else:
                self.attack_textures_atack1.append(arcade.make_soft_square_texture(64, (255, 50, 50, 150)))
        for i in range(1, 7):
            path = f"player_images/atack_2/phase_{i}.png"
            if os.path.exists(path):
                self.attack_textures_atack2.append(arcade.load_texture(path))
            else:
                self.attack_textures_atack2.append(arcade.make_soft_square_texture(64, (50, 255, 50, 150)))
        self.animations["attack"] = [
            arcade.load_texture("player_images/atack_pose_1.png"),
            arcade.load_texture("player_images/atack_pose_2.png"),
            arcade.load_texture("player_images/atack_pose_3.png")
        ]
        self.animation_scales["attack"] = [0.85, 0.85, 0.85]

    def update_animation(self, delta_time):
        if self.state == "attack":
            attack_frames = self.animations.get("attack", [])
            if attack_frames:
                frame_num = min(self.attack_phase, len(attack_frames) - 1)
                self.texture = attack_frames[frame_num]
                if frame_num < len(self.animation_scales["attack"]):
                    self.current_scale = self.animation_scales["attack"][frame_num]
                return
        frames = self.animations.get(self.state, [])
        scales = self.animation_scales.get(self.state, [1.0])
        if not frames:
            return
        if self.state == "dash" and self.dashing:
            self.animation_timer += delta_time * 1.0
        elif self.state == "run" and abs(self.change_x) > 0.5:
            speed_mult = abs(self.change_x) / PLAYER_MOVEMENT_SPEED
            self.animation_timer += delta_time * speed_mult * 2
        else:
            self.animation_timer += delta_time
        if self.animation_timer >= ANIMATION_SPEED:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(frames)
        if self.state == "dash" and self.dashing:
            frame_idx = min(int(self.dash_timer / DASH_DURATION * len(frames)), len(frames) - 1)
            self.texture = frames[frame_idx]
            if frame_idx < len(scales):
                self.current_scale = scales[frame_idx]
            else:
                self.current_scale = scales[-1] if scales else 1.0
        else:
            if self.current_frame < len(frames):
                self.texture = frames[self.current_frame]
                if self.current_frame < len(scales):
                    self.current_scale = scales[self.current_frame]
                else:
                    self.current_scale = scales[-1] if scales else 1.0

    def update_state(self):
        if self.attacking:
            self.state = "attack"
        elif self.dashing:
            self.state = "dash"
        elif not self.on_ground:
            if self.jumping and self.change_y > 0:
                if self.state != "jump_start" and self.change_y > 5:
                    self.state = "jump_start"
                    self.current_frame = 0
                    self.animation_timer = 0
                else:
                    self.state = "jump"
            else:
                self.state = "jump"
        elif abs(self.change_x) > 0.5:
            self.state = "run"
        else:
            self.state = "stand"

    def set_direction(self, facing_right):
        self.facing_right = facing_right

    def start_attack(self):
        if not self.attacking and self.attack_timer <= 0:
            self.attacking = True
            self.attack_phase = 0
            self.can_deal_damage = True
            self.attack_timer = ATTACK_DURATION
            self.saved_change_x = self.change_x
            self.saved_change_y = self.change_y
            self.current_frame = 0
            self.animation_timer = 0
            return True
        return False

    def update_attack(self, delta_time):
        if self.attacking:
            self.attack_timer -= delta_time * 0.5
            if self.attack_timer <= 0:
                self.attack_phase += 1
                self.attack_timer = ATTACK_DURATION
                self.can_deal_damage = True
                attack_frames = self.attack_textures_atack1 if self.attack_type == 1 else self.attack_textures_atack2
                max_p = len(attack_frames)
                if self.attack_phase >= max_p:
                    self.end_attack()
        elif self.attack_timer > 0:
            self.attack_timer -= delta_time * 0.5

    def end_attack(self):
        self.attacking = False
        self.attack_type = 2 if self.attack_type == 1 else 1
        self.attack_timer = ATTACK_COOLDOWN
        self.can_deal_damage = False

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
        if not self.attacking or not self.can_deal_damage:
            return None
        hit_w, hit_h = 130, 50
        offset_x = 70 if self.facing_right else -70
        left = (self.center_x + offset_x) - hit_w / 2
        bottom = self.center_y - hit_h / 2
        return (left, left + hit_w, bottom, bottom + hit_h)

    def activate_dash(self):
        if not self.dash_unlocked or self.dash_cooldown_timer > 0 or self.dashing:
            return False
        self.dashing = True
        self.dash_timer = DASH_DURATION
        self.dash_cooldown_timer = DASH_COOLDOWN
        if self.change_x != 0:
            dir = 1 if self.change_x > 0 else -1
        else:
            dir = 1 if self.facing_right else -1
        self.dash_direction = dir
        self.normal_speed = abs(self.change_x) if self.change_x != 0 else PLAYER_MOVEMENT_SPEED
        self.change_x = dir * DASH_SPEED
        self.current_frame = 0
        self.animation_timer = 0
        return True

    def reset_position(self, x, y):
        self.center_x = x
        self.center_y = y
        self.last_safe_x = x
        self.last_safe_y = y
        self.change_x = 0
        self.change_y = 0
        self.hp = PLAYER_MAX_HP
        self.dashing = False
        self.attacking = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.invincible_timer = 0
        self.facing_right = True
        self.state = "stand"
        self.current_frame = 0
        self.animation_timer = 0
        self.current_scale = 1.0
        self.attack_phase = 0

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
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= delta_time
        self.update_attack(delta_time)
        if not self.attacking:
            if self.change_x > 0:
                self.set_direction(True)
            elif self.change_x < 0:
                self.set_direction(False)
        self.update_state()
        self.update_animation(delta_time)
        if self.on_ground and abs(self.change_x) > 0.1 and random.random() < 0.1:
            self.dust_list.append(DustParticle(self.center_x, self.bottom))
        self.dust_list.update()
        self.was_jumping = self.jumping

    def draw(self, **kwargs):
        self.dust_list.draw()
        if self.texture:
            scale = PLAYER_SCALING * self.current_scale
            texture_width = self.texture.width * scale
            texture_height = self.texture.height * scale
            if not self.facing_right:
                texture_width = -texture_width
            draw_y = self.center_y
            if self.attacking:
                draw_y = self.center_y + 18
            arcade.draw_texture_rect(
                texture=self.texture,
                rect=arcade.rect.XYWH(
                    self.center_x,
                    draw_y,
                    texture_width,
                    texture_height
                ),
                alpha=self.alpha
            )
        if self.attacking:
            textures = self.attack_textures_atack1 if self.attack_type == 1 else self.attack_textures_atack2
            if self.attack_phase < len(textures):
                cur_frame = textures[self.attack_phase]
                attack_scale = 5.0
                offset_x = 70 if self.facing_right else -70
                attack_y = self.center_y + 20
                arcade.draw_texture_rect(
                    texture=cur_frame,
                    rect=arcade.rect.XYWH(self.center_x + offset_x, attack_y,
                                          cur_frame.width * (attack_scale if self.facing_right else -attack_scale),
                                          cur_frame.height * attack_scale * 0.5),
                    alpha=255
                )

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def unlock_dash(self):
        self.dash_unlocked = True

    def can_dash(self):
        return self.dash_unlocked and self.dash_cooldown_timer <= 0

    def can_attack(self):
        return not self.attacking and self.attack_timer <= 0

    def update_safe_position(self):
        if self.on_ground:
            self.last_safe_x = self.center_x
            self.last_safe_y = self.center_y

    def respawn_at_safe_position(self):
        self.center_x = self.last_safe_x
        self.center_y = self.last_safe_y + 50
        self.change_x = 0
        self.change_y = 0
        self.state = "stand"
        self.current_frame = 0
        self.animation_timer = 0
        self.current_scale = 1.0
        self.attack_phase = 0