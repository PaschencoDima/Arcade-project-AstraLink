import arcade
import sys
import os
import random
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player import Player
from database import get_current_user, update_player_progress, get_player_progress, unlock_double_jump_ability, \
    mark_sonic_defeated

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
TITLE = "Main Room"

PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100

CAMERA_LERP = 0.12
DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35 / 3)
DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.45 / 3)


class MainRoomWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, antialiasing=True)
        self.w = SCREEN_WIDTH * 2
        self.h = SCREEN_HEIGHT * 2
        self.filename = "second_room/images/background.png"

        self.world_camera = arcade.camera.Camera2D(
            viewport=arcade.rect.LRBT(
                left=0,
                right=SCREEN_WIDTH,
                bottom=0,
                top=SCREEN_HEIGHT
            )
        )

        self.gui_camera = arcade.camera.Camera2D(
            viewport=arcade.rect.LRBT(
                left=0,
                right=SCREEN_WIDTH,
                bottom=0,
                top=SCREEN_HEIGHT
            )
        )

        self.player = None
        self.platforms = None
        self.walls = None
        self.spikes = None
        self.trampolines = None
        self.background_platforms = None
        self.sonic_boss_sprites = None
        self.sonic_boss = None
        self.health_platforms = None
        self.health_pickups = None
        self.dust_particles = None

        self.physics_engine = None
        self.update_time = 0

        self.level_left = 0
        self.level_right = self.w
        self.level_bottom = 0
        self.level_top = self.h

        self.camera_target_x = 0
        self.camera_target_y = 0

        self.transition_to_first_room = False
        self.transition_timer = 0
        self.transition_duration = 1.0
        self.transition_alpha = 0

        self.death_transition = False
        self.death_timer = 0
        self.death_duration = 1.5
        self.death_alpha = 0
        self.player_visible = True

        self.last_safe_position = (190, 870)
        self.highest_platform_position = (190, 820)
        self.health_pack_position = (1000, 350)
        self.spike_damage_taken = False
        self.sonic_boss_defeated = False

        self.user_id = get_current_user()
        self.player_progress = None

        if self.user_id:
            self.player_progress = get_player_progress(self.user_id)
            if self.player_progress and self.player_progress.get('sonic_defeated'):
                self.sonic_boss_defeated = True
            else:
                self.sonic_boss_defeated = False
        else:
            self.sonic_boss_defeated = False

        self.health_text = None
        self.health_bar_width = 200
        self.health_bar_height = 20

        self.setup()

    def setup(self):
        import os

        self.texture = arcade.load_texture("second_room/images/background.png")
        self.big_platform = arcade.load_texture("second_room/images/platform_big.png")
        self.small_platform = arcade.load_texture("second_room/images/platform_small.png")
        self.platform = arcade.load_texture("second_room/images/platform.png")
        self.wall_texture = arcade.load_texture("second_room/images/wall.png")
        self.floor_texture = arcade.load_texture("second_room/images/floor.png")
        self.spike_texture = arcade.load_texture("second_room/images/spike.png")
        self.reversed_spike_texture = arcade.load_texture("second_room/images/reversed_spike.png")

        if not os.path.exists("second_room/images/health_pack.png"):
            self.health_pack_texture = arcade.make_soft_circle_texture(40, arcade.color.GREEN)
        else:
            self.health_pack_texture = arcade.load_texture("second_room/images/health_pack.png")

        self.platforms = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.spikes = arcade.SpriteList()
        self.trampolines = arcade.SpriteList()
        self.background_platforms = arcade.SpriteList()
        self.sonic_boss_sprites = arcade.SpriteList()
        self.health_platforms = arcade.SpriteList()
        self.health_pickups = arcade.SpriteList()
        self.dust_particles = arcade.SpriteList()

        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        original_cwd = os.getcwd()

        parent_dir = os.path.dirname(script_dir)
        os.chdir(parent_dir)

        dash_unlocked = True

        if self.user_id and self.player_progress:
            double_jump_unlocked = self.player_progress.get('double_jump_unlocked', False)
        else:
            double_jump_unlocked = False

        from player import DustParticle
        self.DustParticle = DustParticle

        self.player = Player(dash_unlocked=dash_unlocked)

        if double_jump_unlocked:
            self.player.unlock_double_jump()

        self.player.center_x = 190
        self.player.center_y = 870

        os.chdir(original_cwd)

        self.sonic_boss = None

        self.create_platforms()

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.platforms,
            gravity_constant=GRAVITY
        )

        bar_width = 300
        bar_x = 20
        bar_y = SCREEN_HEIGHT - 40

        self.health_text = arcade.Text(
            "HP: 100/100",
            bar_x + bar_width / 2,
            bar_y,
            arcade.color.WHITE,
            18,
            bold=True,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        self.world_camera.position = (self.player.center_x, self.player.center_y)
        self.camera_target_x = self.player.center_x
        self.camera_target_y = self.player.center_y

    def create_dust_effect(self):
        for _ in range(random.randint(15, 20)):
            particle = self.DustParticle(self.player.center_x, self.player.bottom)
            self.dust_particles.append(particle)

    def create_platforms(self):
        platforms_data = [
            (190, 820, self.big_platform, 300, 50, True),
            (1000, 180, self.big_platform, 350, 50, True),
            (1300, 180, self.big_platform, 350, 50, True),
            (680, 200, self.big_platform, 350, 50, True),
            (400, 200, self.big_platform, 350, 50, True),
            (80, 150, self.small_platform, 60, 50, True),
            (180, 250, self.small_platform, 60, 50, True),
            (80, 350, self.small_platform, 60, 50, True),
            (280, 450, self.platform, 100, 50, True),
            (480, 550, self.platform, 100, 50, True),
            (1670, 150, self.platform, 100, 50, True),
            (3000, 150, self.small_platform, 60, 50, True),
            (3120, 290, self.small_platform, 60, 50, True),
            (3000, 430, self.small_platform, 60, 50, True),
            (2600, 640, self.platform, 100, 50, True),
            (2400, 640, self.big_platform, 350, 50, True),
            (2080, 640, self.big_platform, 350, 50, True),
            (1790, 640, self.big_platform, 350, 50, True),
            (1490, 640, self.big_platform, 350, 50, True),
            (1250, 780, self.small_platform, 60, 50, True),
            (1400, 900, self.small_platform, 60, 50, True),
        ]

        center_wall_data = [
            (875, 225, self.wall_texture, 50, 50, True),
            (875, 275, self.wall_texture, 50, 50, True),
            (875, 325, self.wall_texture, 50, 50, True),
            (875, 375, self.wall_texture, 50, 50, True),
            (875, 425, self.wall_texture, 50, 50, True),
            (875, 475, self.wall_texture, 50, 50, False),
            (875, 525, self.wall_texture, 50, 50, False),
            (875, 575, self.wall_texture, 50, 50, False),
            (875, 625, self.wall_texture, 50, 50, True),
            (875, 675, self.wall_texture, 50, 50, True),
            (875, 725, self.wall_texture, 50, 50, True),
            (875, 775, self.wall_texture, 50, 50, True),
            (875, 825, self.wall_texture, 50, 50, True),
            (875, 875, self.wall_texture, 50, 50, True),
            (875, 925, self.wall_texture, 50, 50, True),
            (875, 975, self.wall_texture, 50, 50, True),
            (875, 1025, self.wall_texture, 50, 50, True),
            (875, 1075, self.wall_texture, 50, 50, True),
            (825, 1075, self.wall_texture, 50, 50, True),
            (775, 1075, self.wall_texture, 50, 50, True),
            (725, 1075, self.wall_texture, 50, 50, True),
            (675, 1075, self.wall_texture, 50, 50, True),
            (625, 1075, self.wall_texture, 50, 50, True),
            (575, 1075, self.wall_texture, 50, 50, True),
            (525, 1075, self.wall_texture, 50, 50, True),
            (475, 1075, self.wall_texture, 50, 50, True),
            (425, 1075, self.wall_texture, 50, 50, True),
            (375, 1075, self.wall_texture, 50, 50, True),
            (325, 1075, self.wall_texture, 50, 50, True),
            (275, 1075, self.wall_texture, 50, 50, True),
            (225, 1075, self.wall_texture, 50, 50, True),
            (175, 1075, self.wall_texture, 50, 50, True),
            (125, 1075, self.wall_texture, 50, 50, True),
            (75, 1075, self.wall_texture, 50, 50, True),
            (25, 1075, self.wall_texture, 50, 50, True),
        ]

        for x, y, texture, width, height, add_collision in platforms_data:
            platform = arcade.Sprite()
            platform.texture = texture
            platform.center_x = x
            platform.center_y = y
            platform.width = width
            platform.height = height
            if add_collision:
                self.platforms.append(platform)
            self.background_platforms.append(platform)

        for x, y, texture, width, height, add_collision in center_wall_data:
            platform = arcade.Sprite()
            platform.texture = texture
            platform.center_x = x
            platform.center_y = y
            platform.width = width
            platform.height = height
            if add_collision:
                self.platforms.append(platform)
            self.background_platforms.append(platform)

        health_platform_data = [
            (1000, 300, self.big_platform, 300, 50, True),
        ]

        for x, y, texture, width, height, add_collision in health_platform_data:
            platform = arcade.Sprite()
            platform.texture = texture
            platform.center_x = x
            platform.center_y = y
            platform.width = width
            platform.height = height
            if add_collision:
                self.platforms.append(platform)
            self.background_platforms.append(platform)
            self.health_platforms.append(platform)

        health_pickup = arcade.Sprite()
        health_pickup.texture = self.health_pack_texture
        health_pickup.center_x = self.health_pack_position[0]
        health_pickup.center_y = self.health_pack_position[1]
        health_pickup.width = 40
        health_pickup.height = 40
        health_pickup.heal_amount = 30
        self.health_pickups.append(health_pickup)

        spike_locations = [
            (856, 50, self.spike_texture, 90, 36),
            (950, 60, self.spike_texture, 100, 55),
            (1060, 67, self.spike_texture, 120, 70),
            (1270, 155, self.reversed_spike_texture, 100, 85),
            (280, 485, self.spike_texture, 90, 36),
            (500, 280, self.spike_texture, 450, 150),
            (780, 245, self.spike_texture, 140, 55),
            (1420, 220, self.spike_texture, 100, 55),
            (2020, 685, self.spike_texture, 100, 55),
            (2120, 685, self.spike_texture, 100, 55),
            (2220, 685, self.spike_texture, 100, 55),
            (2320, 685, self.spike_texture, 100, 55),
            (2400, 685, self.spike_texture, 80, 55),
        ]

        for x, y, texture, width, height in spike_locations:
            spike = arcade.Sprite()
            spike.texture = texture
            spike.center_x = x
            spike.center_y = y
            spike.width = width
            spike.height = height
            self.spikes.append(spike)

        wall_size = 40
        floor_y = wall_size // 2
        floor_x = wall_size // 2

        while floor_x < self.w:
            floor_decoration = arcade.Sprite()
            floor_decoration.texture = self.floor_texture
            floor_decoration.center_x = floor_x
            floor_decoration.center_y = floor_y
            floor_decoration.width = wall_size
            floor_decoration.height = wall_size
            self.walls.append(floor_decoration)

            floor_collision = arcade.Sprite()
            floor_collision.texture = self.floor_texture
            floor_collision.center_x = floor_x
            floor_collision.center_y = floor_y
            floor_collision.width = wall_size
            floor_collision.height = wall_size
            self.platforms.append(floor_collision)

            floor_x += wall_size

        wall_x = wall_size // 2
        wall_start_y = wall_size + wall_size // 2

        wall_height_available = self.h - wall_start_y - wall_size
        middle_height = wall_start_y + wall_height_available // 2
        exit_start_y = middle_height - wall_size * 2
        exit_end_y = middle_height + wall_size * 2

        wall_y = wall_start_y

        while wall_y < self.h - wall_size:
            if not (exit_start_y <= wall_y < exit_end_y):
                wall = arcade.Sprite()
                wall.texture = self.wall_texture
                wall.center_x = wall_x
                wall.center_y = wall_y
                wall.width = wall_size
                wall.height = wall_size
                self.walls.append(wall)

                wall_collision = arcade.Sprite()
                wall_collision.texture = self.wall_texture
                wall_collision.center_x = wall_x
                wall_collision.center_y = wall_y
                wall_collision.width = wall_size
                wall_collision.height = wall_size
                self.platforms.append(wall_collision)
            wall_y += wall_size

        wall_start_y = wall_size + wall_size // 2
        wall_height_available = self.h - wall_start_y - wall_size
        middle_height = wall_start_y + wall_height_available // 2
        exit_start_y = middle_height - wall_size * 2
        exit_end_y = middle_height + wall_size * 2

        wall_x = self.w - wall_size // 2
        wall_y = wall_start_y

        while wall_y < self.h - wall_size:
            if not (exit_start_y <= wall_y < exit_end_y):
                wall = arcade.Sprite()
                wall.texture = self.wall_texture
                wall.center_x = wall_x
                wall.center_y = wall_y
                wall.width = wall_size
                wall.height = wall_size
                self.walls.append(wall)

                wall_collision = arcade.Sprite()
                wall_collision.texture = self.wall_texture
                wall_collision.center_x = wall_x
                wall_collision.center_y = wall_y
                wall_collision.width = wall_size
                wall_collision.height = wall_size
                self.platforms.append(wall_collision)
            wall_y += wall_size

        ceiling_y = self.h - wall_size // 2
        ceiling_x = wall_size // 2

        while ceiling_x < self.w:
            ceiling = arcade.Sprite()
            ceiling.texture = self.wall_texture
            ceiling.center_x = ceiling_x
            ceiling.center_y = ceiling_y
            ceiling.width = wall_size
            ceiling.height = wall_size
            self.walls.append(ceiling)

            ceiling_collision = arcade.Sprite()
            ceiling_collision.texture = self.wall_texture
            ceiling_collision.center_x = ceiling_x
            ceiling_collision.center_y = ceiling_y
            ceiling_collision.width = wall_size
            ceiling_collision.height = wall_size
            self.platforms.append(ceiling_collision)
            ceiling_x += wall_size

    def on_draw(self):
        self.clear()

        self.world_camera.use()

        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(
                self.w // 2,
                self.h // 2,
                self.w,
                self.h
            )
        )

        self.background_platforms.draw()
        self.walls.draw()
        self.spikes.draw()
        self.trampolines.draw()
        self.health_pickups.draw()
        self.dust_particles.draw()

        if self.sonic_boss and not self.sonic_boss_defeated:
            if hasattr(self.sonic_boss, 'spikes'):
                self.sonic_boss.spikes.draw()
            self.sonic_boss_sprites.draw()

        if self.player_visible:
            self.player.draw()

        if self.sonic_boss and hasattr(self.sonic_boss,
                                       'active') and self.sonic_boss.active and not self.sonic_boss_defeated:
            if hasattr(self.sonic_boss, 'draw_health_bar'):
                self.sonic_boss.draw_health_bar()

        self.gui_camera.use()
        self.draw_health_bar()

        if self.death_transition and self.death_alpha > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                10000, 10000),
                (0, 0, 0, int(self.death_alpha))
            )

        if self.transition_to_first_room and self.transition_alpha > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                10000, 10000),
                (0, 0, 0, int(self.transition_alpha))
            )

    def draw_health_bar(self):
        bar_width = 300
        bar_height = 35
        bar_x = 20
        bar_y = SCREEN_HEIGHT - 40

        health_ratio = max(0, self.player.hp / self.player.max_hp)

        arcade.draw_rect_filled(arcade.rect.XYWH(
            bar_x + bar_width / 2,
            bar_y,
            bar_width + 6,
            bar_height + 6),
            arcade.color.BLACK
        )

        arcade.draw_rect_filled(arcade.rect.XYWH(
            bar_x + bar_width / 2,
            bar_y,
            bar_width,
            bar_height),
            arcade.color.DARK_RED
        )

        if health_ratio > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(
                bar_x + (bar_width * health_ratio) / 2,
                bar_y,
                bar_width * health_ratio,
                bar_height),
                arcade.color.GREEN
            )

        self.health_text.text = f"HP: {int(max(0, self.player.hp))}/{self.player.max_hp}"
        self.health_text.x = bar_x + bar_width / 2
        self.health_text.y = bar_y
        self.health_text.draw()

    def on_update(self, delta_time):
        if self.player is None:
            return

        if self.player.center_x <= 50 and not self.transition_to_first_room:
            self.start_transition_to_first_room()

        if self.transition_to_first_room:
            self.transition_timer -= delta_time
            self.transition_alpha = min(255, (1 - self.transition_timer / self.transition_duration) * 255)

            if self.transition_timer <= 0:
                self.go_to_first_room()
                return

        self.update_time = delta_time

        if self.death_transition:
            self.death_timer -= delta_time
            self.death_alpha = min(255, (1 - self.death_timer / self.death_duration) * 255)

            if self.death_timer <= 0:
                self.reset_player()
                self.death_transition = False
                self.death_alpha = 0
                self.player_visible = True
                return
            else:
                return

        if self.player.dashing:
            self.player.dash_timer -= delta_time
            if self.player.dash_timer <= 0:
                self.player.dashing = False
                if abs(self.player.change_x) > PLAYER_MOVEMENT_SPEED:
                    self.player.change_x = self.player.normal_speed * (1 if self.player.change_x > 0 else -1)

        if self.player.dash_cooldown_timer > 0:
            self.player.dash_cooldown_timer -= delta_time

        self.player.update(delta_time)

        self.physics_engine.update()

        self.dust_particles.update(delta_time)

        was_on_ground = self.player.on_ground
        self.player.on_ground = self.physics_engine.can_jump()

        if self.player.on_ground:
            self.player.jumps_used = 0
            self.player.double_jump_available = self.player.double_jump_unlocked

        if was_on_ground == False and self.player.on_ground == True:
            self.create_dust_effect()

        if not self.player.on_ground:
            self.player.was_jumping = True
        elif self.player.was_jumping:
            self.player.was_jumping = False

        if self.player.left < 0:
            self.player.left = 0
        if self.player.right > self.w:
            self.player.right = self.w

        if self.player.bottom < -100 and not self.death_transition:
            self.start_death_transition()

        health_hit_list = arcade.check_for_collision_with_list(self.player, self.health_pickups)
        for health_pack in health_hit_list:
            if self.player.hp < self.player.max_hp:
                self.player.hp = min(self.player.max_hp, self.player.hp + health_pack.heal_amount)
                self.last_safe_position = (self.health_pack_position[0], self.health_pack_position[1] + 50)
                health_pack.remove_from_sprite_lists()

        if 2200 >= self.player.center_x >= 1500 and self.sonic_boss is None and not self.sonic_boss_defeated:
            try:
                from second_room import sonic as sonic_module
                self.sonic_boss = sonic_module.Sonic(2000, 80, self.player)
                self.sonic_boss_sprites = arcade.SpriteList()
                self.sonic_boss_sprites.append(self.sonic_boss)
            except ImportError:
                self.create_simple_boss()

        if self.sonic_boss and hasattr(self.sonic_boss, 'active') and not self.sonic_boss_defeated:
            if not self.sonic_boss.active:
                self.sonic_boss_sprites.remove(self.sonic_boss)
                self.sonic_boss = None
                self.sonic_boss_defeated = True
                self.unlock_double_jump()
            elif hasattr(self.sonic_boss, 'update'):
                self.sonic_boss.update(delta_time)

        self.check_player_attack()

        spike_hit_list = arcade.check_for_collision_with_list(self.player, self.spikes)
        if spike_hit_list and not self.spike_damage_taken:
            self.player.hp -= 20
            self.player.hp = max(0, self.player.hp)
            self.spike_damage_taken = True
            if self.player.hp <= 0:
                self.start_death_transition()
            else:
                self.start_death_transition()
                return

        if not spike_hit_list:
            self.spike_damage_taken = False

        trampoline_hit_list = arcade.check_for_collision_with_list(self.player, self.trampolines)
        if trampoline_hit_list and self.player.change_y < 0:
            self.player.change_y = PLAYER_JUMP_SPEED * 1.5

        if self.sonic_boss and hasattr(self.sonic_boss,
                                       'spikes') and self.sonic_boss.active and not self.sonic_boss_defeated:
            spike_hit_list = arcade.check_for_collision_with_list(self.player, self.sonic_boss.spikes)
            if spike_hit_list and not self.spike_damage_taken:
                self.player.hp -= 20
                self.player.hp = max(0, self.player.hp)
                self.spike_damage_taken = True
                if self.player.hp <= 0:
                    self.start_death_transition()
                else:
                    self.start_death_transition()
                    return
                for spike in spike_hit_list:
                    spike.remove_from_sprite_lists()

        if self.sonic_boss and hasattr(self.sonic_boss,
                                       'active') and self.sonic_boss.active and not self.sonic_boss_defeated:
            if isinstance(self.sonic_boss, arcade.Sprite):
                if arcade.check_for_collision(self.player, self.sonic_boss):
                    if hasattr(self.sonic_boss, 'contact_damage'):
                        damage_amount = self.sonic_boss.contact_damage
                        damage_taken = self.player.take_damage(damage_amount)
                        if damage_taken:
                            self.player.hp = max(0, self.player.hp)
                            if self.player.hp <= 0:
                                self.start_death_transition()
            else:
                if (self.player.right > self.sonic_boss.left and
                        self.player.left < self.sonic_boss.right and
                        self.player.top > self.sonic_boss.bottom and
                        self.player.bottom < self.sonic_boss.top):

                    if hasattr(self.sonic_boss, 'contact_damage'):
                        damage_amount = self.sonic_boss.contact_damage
                        damage_taken = self.player.take_damage(damage_amount)
                        if damage_taken:
                            self.player.hp = max(0, self.player.hp)
                            if self.player.hp <= 0:
                                self.start_death_transition()

        self.update_camera_position(delta_time)

    def create_simple_boss(self):
        self.sonic_boss = arcade.Sprite()
        self.sonic_boss.center_x = 2000
        self.sonic_boss.center_y = 80
        self.sonic_boss.active = True
        self.sonic_boss.health = 500
        self.sonic_boss.max_health = 500
        self.sonic_boss.left = 1975
        self.sonic_boss.right = 2025
        self.sonic_boss.bottom = 55
        self.sonic_boss.top = 105
        self.sonic_boss.width = 50
        self.sonic_boss.height = 50
        self.sonic_boss.contact_damage = 20

        try:
            self.sonic_boss.texture = arcade.load_texture("second_room/images/sonic.png")
        except:
            self.sonic_boss.texture = arcade.make_soft_square_texture(50, (0, 255, 255))

        self.sonic_boss_sprites = arcade.SpriteList()
        self.sonic_boss_sprites.append(self.sonic_boss)
        self.sonic_boss.spikes = arcade.SpriteList()

        def update(delta_time):
            if hasattr(self.sonic_boss, 'active') and self.sonic_boss.active:
                if not hasattr(self.sonic_boss, 'move_direction'):
                    self.sonic_boss.move_direction = 1
                    self.sonic_boss.move_speed = 2

                self.sonic_boss.center_x += self.sonic_boss.move_speed * self.sonic_boss.move_direction

                if self.sonic_boss.center_x > 2300:
                    self.sonic_boss.move_direction = -1
                elif self.sonic_boss.center_x < 1500:
                    self.sonic_boss.move_direction = 1

        def take_damage(damage):
            self.sonic_boss.health -= damage
            if self.sonic_boss.health <= 0:
                self.sonic_boss.active = False
                self.sonic_boss_defeated = True
                self.unlock_double_jump()
                return True
            return False

        def draw_health_bar():
            bar_width = 150
            bar_height = 15
            bar_x = self.sonic_boss.center_x - bar_width // 2
            bar_y = self.sonic_boss.center_y + 70

            health_ratio = max(0, self.sonic_boss.health / self.sonic_boss.max_health)

            arcade.draw_rectangle_filled(
                bar_x + bar_width // 2,
                bar_y,
                bar_width,
                bar_height,
                arcade.color.BLACK
            )

            arcade.draw_rectangle_filled(
                bar_x + bar_width // 2,
                bar_y,
                bar_width - 4,
                bar_height - 4,
                arcade.color.DARK_RED
            )

            if health_ratio > 0:
                arcade.draw_rectangle_filled(
                    bar_x + (bar_width * health_ratio) // 2,
                    bar_y,
                    bar_width * health_ratio - 4,
                    bar_height - 4,
                    arcade.color.GREEN
                )

        self.sonic_boss.update = update
        self.sonic_boss.take_damage = take_damage
        self.sonic_boss.draw_health_bar = draw_health_bar

    def check_player_attack(self):
        if self.death_transition or not self.player.attacking:
            return

        hitbox = self.player.get_attack_hitbox()
        if not hitbox:
            return

        attack_left, attack_right, attack_bottom, attack_top = hitbox

        if self.sonic_boss and hasattr(self.sonic_boss, 'active') and self.sonic_boss.active:
            if isinstance(self.sonic_boss, arcade.Sprite):
                if (attack_right > self.sonic_boss.left and
                        attack_left < self.sonic_boss.right and
                        attack_top > self.sonic_boss.bottom and
                        attack_bottom < self.sonic_boss.top):

                    damage = self.player.deal_damage()
                    if damage > 0:
                        self.sonic_boss.take_damage(damage)
                        if self.sonic_boss.health <= 0:
                            self.sonic_boss_defeated = True
                            self.unlock_double_jump()
            else:
                if (attack_right > self.sonic_boss.left and
                        attack_left < self.sonic_boss.right and
                        attack_top > self.sonic_boss.bottom and
                        attack_bottom < self.sonic_boss.top):

                    damage = self.player.deal_damage()
                    if damage > 0:
                        self.sonic_boss.take_damage(damage)
                        if self.sonic_boss.health <= 0:
                            self.sonic_boss_defeated = True
                            self.unlock_double_jump()

    def start_transition_to_first_room(self):
        self.transition_to_first_room = True
        self.transition_timer = self.transition_duration
        self.transition_alpha = 0

    def go_to_first_room(self):
        if self.user_id:
            from database import update_current_room
            update_current_room(self.user_id, 1)

        self.close()

        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            from first_room.drawing_first_room_first_lvl import GameWindow
            window = GameWindow()
            arcade.run()
        except ImportError:
            arcade.close_window()

    def unlock_double_jump(self):
        if self.user_id and not self.player.double_jump_unlocked:
            self.player.unlock_double_jump()
            unlock_double_jump_ability(self.user_id)
            update_player_progress(self.user_id, sonic_defeated=True, double_jump_unlocked=True)
            mark_sonic_defeated(self.user_id)

    def start_death_transition(self):
        if not self.death_transition:
            self.death_transition = True
            self.death_timer = self.death_duration
            self.death_alpha = 0
            self.player_visible = False
            self.player.change_x = 0
            self.player.change_y = 0

    def reset_player(self):
        if self.player.hp > 0:
            respawn_x, respawn_y = self.last_safe_position
        else:
            respawn_x, respawn_y = self.highest_platform_position

        safe_spawn = self.find_safe_spawn_location(respawn_x, respawn_y)

        if not self.is_position_safe(safe_spawn[0], safe_spawn[1]):
            if self.player.hp > 0:
                safe_spawn = (0, 870)
            else:
                safe_spawn = (0, 870)

        self.player.center_x = safe_spawn[0]
        self.player.center_y = safe_spawn[1]
        self.player.change_x = 0
        self.player.change_y = 0
        if self.player.hp <= 0:
            self.player.hp = 100

        self.player.dashing = False
        self.player.dash_timer = 0
        self.player.dash_cooldown_timer = 0

        self.player.invincible_timer = 0
        self.spike_damage_taken = False

        self.world_camera.position = (self.player.center_x, self.player.center_y)

        if len(self.health_pickups) == 0:
            self.respawn_health_pickup()

    def is_position_safe(self, x, y):
        temp_sprite = arcade.SpriteSolidColor(20, 40, arcade.color.RED)
        temp_sprite.center_x = x
        temp_sprite.center_y = y

        platform_collisions = arcade.check_for_collision_with_list(temp_sprite, self.platforms)
        spike_collisions = arcade.check_for_collision_with_list(temp_sprite, self.spikes)

        return not (platform_collisions or spike_collisions)

    def find_safe_spawn_location(self, x, y):
        test_positions = [
            (x, y + 20),
            (x, y + 40),
            (x + 50, y + 20),
            (x - 50, y + 20),
            (x, y + 60),
            (x + 30, y + 30),
            (x - 30, y + 30),
        ]

        for pos_x, pos_y in test_positions:
            if self.is_position_safe(pos_x, pos_y):
                return (pos_x, pos_y)

        return (x, y + 20)

    def respawn_health_pickup(self):
        if len(self.health_pickups) == 0:
            health_pickup = arcade.Sprite()
            health_pickup.texture = self.health_pack_texture
            health_pickup.center_x = self.health_pack_position[0]
            health_pickup.center_y = self.health_pack_position[1]
            health_pickup.width = 40
            health_pickup.height = 40
            health_pickup.heal_amount = 30
            self.health_pickups.append(health_pickup)

    def update_camera_position(self, delta_time):
        cam_x, cam_y = self.world_camera.position
        px, py = self.player.center_x, self.player.center_y

        dz_left = cam_x - DEAD_ZONE_W // 2
        dz_right = cam_x + DEAD_ZONE_W // 2
        dz_bottom = cam_y - DEAD_ZONE_H // 2
        dz_top = cam_y + DEAD_ZONE_H // 2

        player_in_dz = (
                px >= dz_left and
                px <= dz_right and
                py >= dz_bottom and
                py <= dz_top
        )

        if not player_in_dz:
            if px < dz_left:
                self.camera_target_x = px + DEAD_ZONE_W // 2
            elif px > dz_right:
                self.camera_target_x = px - DEAD_ZONE_W // 2
            else:
                self.camera_target_x = cam_x

            if py < dz_bottom:
                self.camera_target_y = py + DEAD_ZONE_H // 2
            elif py > dz_top:
                self.camera_target_y = py - DEAD_ZONE_H // 2
            else:
                self.camera_target_y = cam_y
        else:
            self.camera_target_x = cam_x
            self.camera_target_y = cam_y

        half_viewport_w = SCREEN_WIDTH // 2
        half_viewport_h = SCREEN_HEIGHT // 2

        min_camera_x = self.level_left + half_viewport_w
        max_camera_x = self.level_right - half_viewport_w
        min_camera_y = self.level_bottom + half_viewport_h
        max_camera_y = self.level_top - half_viewport_h

        self.camera_target_x = max(min(self.camera_target_x, max_camera_x), min_camera_x)
        self.camera_target_y = max(min(self.camera_target_y, max_camera_y), min_camera_y)

        current_x, current_y = self.world_camera.position
        new_x = current_x + (self.camera_target_x - current_x) * CAMERA_LERP
        new_y = current_y + (self.camera_target_y - current_y) * CAMERA_LERP

        new_x = max(min(new_x, max_camera_x), min_camera_x)
        new_y = max(min(new_y, max_camera_y), min_camera_y)

        self.world_camera.position = (new_x, new_y)

    def on_key_press(self, key, modifiers):
        if self.death_transition:
            return

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.player.on_ground:
                if self.physics_engine.can_jump():
                    success = self.player.jump()
            elif self.player.double_jump_unlocked:
                success = self.player.double_jump()
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
            self.player.set_direction(False)
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
            self.player.set_direction(True)
        elif key == arcade.key.Q:
            self.player.activate_dash()
        elif key == arcade.key.Z or key == arcade.key.L:
            if self.player.can_attack():
                self.player.start_attack()
        elif key == arcade.key.ESCAPE:
            try:
                from start_window.start_window import StoryWindow
                self.close()
                story_window = StoryWindow()
                story_window.setup()
                arcade.run()
            except ImportError:
                arcade.close_window()

    def on_key_release(self, key, modifiers):
        if self.death_transition:
            return

        if key == arcade.key.LEFT or key == arcade.key.A:
            if self.player.change_x < 0:
                self.player.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            if self.player.change_x > 0:
                self.player.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            self.player.jumping = False

    def on_mouse_press(self, x, y, button, modifiers):
        if self.death_transition:
            return

        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.player.can_attack():
                self.player.start_attack()


def start_game():
    window = MainRoomWindow()
    arcade.run()


if __name__ == "__main__":
    start_game()