import arcade
import sys
import os
import random
import math
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player import Player, DustParticle
from database import get_current_user, update_current_room, get_player_progress, update_arena_progress

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
TITLE = "Texture"

PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100

CAMERA_LERP = 0.12
DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35 / 3)
DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.45 / 3)

DASH_SPEED = 30
DASH_DURATION = 0.3
DASH_COOLDOWN = 1.0

GEYSER_DAMAGE = 30
GEYSER_ACTIVE_DURATION = 1.5
GEYSER_COOLDOWN_DURATION = 3.0
GEYSER_WIDTH = 100
GEYSER_HEIGHT = 65
GEYSER_BLAST_SPEED = 15


class GeyserEffect(arcade.SpriteCircle):
    def __init__(self, x, y):
        color = random.choice([
            (100, 150, 255, 180),
            (80, 180, 255, 200),
            (150, 200, 255, 150),
            (200, 220, 255, 120),
            (255, 255, 255, 255)
        ])
        size = random.randint(4, 12)
        super().__init__(size, color)
        self.center_x = x + random.uniform(-GEYSER_WIDTH // 3, GEYSER_WIDTH // 3)
        self.center_y = y
        self.change_x = random.uniform(-0.5, 0.5)
        self.change_y = random.uniform(8, 12)

        self.scale = 1.0
        self.alpha = random.randint(150, 255)
        self.lifetime = random.uniform(0.8, 1.5)
        self.time_alive = 0
        self.gravity = 0.3

    def update(self, delta_time=1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y

        self.change_y -= self.gravity
        self.change_x *= 0.98
        self.scale = (self.scale[0] * 0.98, self.scale[1] * 0.98)

        if self.alpha > 3:
            self.alpha -= 3

        self.time_alive += delta_time

        if self.time_alive > self.lifetime or self.alpha <= 0:
            self.remove_from_sprite_lists()


class Geyser(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.texture = arcade.load_texture("first_room/images/geyser.png")
        self.center_x = x
        self.center_y = y
        self.width = GEYSER_WIDTH
        self.height = GEYSER_HEIGHT

        self.active = False
        self.timer = 0
        self.cycle_time = 0

        self.effects = arcade.SpriteList()

        self.hitbox_left = x - GEYSER_WIDTH // 2
        self.hitbox_right = x + GEYSER_WIDTH // 2
        self.hitbox_bottom = y
        self.hitbox_top = y + GEYSER_HEIGHT

        self.damage_dealt_in_current_cycle = False

        self.platform_sprite = arcade.Sprite()
        self.platform_sprite.texture = self.texture
        self.platform_sprite.center_x = self.center_x
        self.platform_sprite.center_y = self.center_y - self.height // 2 + 5
        self.platform_sprite.width = self.width
        self.platform_sprite.height = 10

    def update(self, delta_time):
        self.cycle_time += delta_time

        cycle_duration = GEYSER_ACTIVE_DURATION + GEYSER_COOLDOWN_DURATION
        cycle_position = self.cycle_time % cycle_duration

        old_active = self.active
        self.active = (cycle_position < GEYSER_ACTIVE_DURATION)

        if not old_active and self.active:
            self.damage_dealt_in_current_cycle = False

        if self.active:
            self.timer = GEYSER_ACTIVE_DURATION - (GEYSER_ACTIVE_DURATION - cycle_position)

            if random.random() < 0.7:
                effect = GeyserEffect(self.center_x, self.hitbox_bottom)
                self.effects.append(effect)
        else:
            self.timer = 0

        self.effects.update(delta_time)

    def draw(self):
        if self.active:
            self.effects.draw()

        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(
            self.center_x,
            self.center_y,
            self.width,
            self.height)
                                 )

    def check_collision(self, player):
        if not self.active or self.damage_dealt_in_current_cycle:
            return False

        player_hitbox = (
            player.left,
            player.right,
            player.bottom,
            player.top
        )

        geyer_hitbox = (
            self.hitbox_left,
            self.hitbox_right,
            self.hitbox_bottom,
            self.hitbox_top
        )

        collision = not (
                player_hitbox[1] < geyer_hitbox[0] or
                player_hitbox[0] > geyer_hitbox[1] or
                player_hitbox[2] > geyer_hitbox[3] or
                player_hitbox[3] < geyer_hitbox[2]
        )

        if collision:
            self.damage_dealt_in_current_cycle = True
            return True

        return False

    def apply_blast(self, player):
        if self.active:
            player.change_y = GEYSER_BLAST_SPEED
            if player.center_x < self.center_x:
                player.change_x = -5
            else:
                player.change_x = 5


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, antialiasing=True)
        self.w = SCREEN_WIDTH * 2
        self.h = SCREEN_HEIGHT * 2
        self.filename = "images/background.png"

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
        self.dust_particles = None
        self.geysers = None

        self.dash_cooldown_text = None
        self.hp_text = None
        self.arena_text = None
        self.robot_hp_text = None

        self.physics_engine = None
        self.update_time = 0

        self.level_left = 0
        self.level_right = self.w
        self.level_bottom = 0
        self.level_top = self.h

        self.camera_target_x = 0
        self.camera_target_y = 0

        self.transition_to_room2 = False
        self.transition_timer = 0
        self.transition_duration = 1.0
        self.transition_alpha = 0

        self.arena_active = False
        self.arena_robots_spawned = False
        self.arena_completed = False
        self.arena_robots = []
        self.arena_start_time = 0
        self.arena_message_timer = 0
        self.arena_message = ""

        self.user_id = get_current_user()
        self.dash_unlocked = False

        if self.user_id:
            self.dash_unlocked = get_player_progress(self.user_id)
            update_current_room(self.user_id, 1)

        self.robots_list = arcade.SpriteList()

        self.setup()

    def setup(self):
        self.texture = arcade.load_texture("first_room/images/background.png")
        self.big_platform = arcade.load_texture("first_room/images/platform1.png")
        self.small_platform = arcade.load_texture("first_room/images/platform3.png")
        self.gray_platform = arcade.load_texture("first_room/images/platform2.png")
        self.platform = arcade.load_texture("first_room/images/platform4.png")
        self.spike_texture = arcade.load_texture("first_room/images/spikes.png")
        self.wall_texture = arcade.load_texture("first_room/images/wall.png")
        self.trampoline_texture = arcade.load_texture("first_room/images/trampoline.png")
        self.falling_lava_texture = arcade.load_texture('first_room/images/falling_lava.png')
        self.geyser_texture = arcade.load_texture("first_room/images/geyser.png")

        self.platforms = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.spikes = arcade.SpriteList()
        self.trampolines = arcade.SpriteList()
        self.background_platforms = arcade.SpriteList()
        self.dust_particles = arcade.SpriteList()
        self.geysers = arcade.SpriteList()
        self.robots_list = arcade.SpriteList()

        self.dash_cooldown_text = arcade.Text(
            "",
            0, 0,
            arcade.color.RED,
            12,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        self.player = Player(dash_unlocked=self.dash_unlocked)

        self.create_platforms()

        geyser_x = 280 * 2
        geyser_y = 1365
        geyser1 = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser1)

        geyser_x = 870 * 2
        geyser_y = 1315
        geyser2 = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser2)

        for geyser in self.geysers:
            self.platforms.append(geyser.platform_sprite)
            self.background_platforms.append(geyser.platform_sprite)

        self.create_arena_robots()

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.platforms,
            gravity_constant=GRAVITY
        )

        self.world_camera.position = (self.player.center_x, self.player.center_y)
        self.camera_target_x = self.player.center_x
        self.camera_target_y = self.player.center_y

    def create_dust_effect(self):
        for _ in range(random.randint(15, 20)):
            particle = DustParticle(self.player.center_x, self.player.bottom)
            self.dust_particles.append(particle)

    def create_arena_robots(self):
        from first_room.robot import Robot

        platform_positions = [
            (720 * 2 + 200, 600),
            (1040 * 2 + 200, 600)
        ]

        for x, y in platform_positions:
            robot = Robot(x=x, y=y + 50, player=self.player, is_arena_robot=True)
            robot.platform_left = x - 200
            robot.platform_right = x + 200
            robot.platform_y = y + 50

            robot.facing_right = True
            robot.scale = 2.0
            robot.health = 1500
            robot.max_health = 1500

            self.robots_list.append(robot)
            self.arena_robots.append(robot)

    def spawn_arena_robots(self):
        if self.arena_robots_spawned:
            return

        try:
            for robot in self.arena_robots:
                if not robot.spawned:
                    robot.spawn(robot.center_x, robot.platform_y)

            self.arena_robots_spawned = True
            self.arena_start_time = time.time()
            self.arena_message = "Арена активирована! Победите роботов!"
            self.arena_message_timer = 3.0
        except Exception:
            pass

    def check_arena_activation(self):
        if not self.dash_unlocked:
            return

        if self.arena_active or self.arena_completed:
            return

        arena_platforms = [
            (720 * 2, 600, 400),
            (830 * 2, 600, 1600),
            (920 * 2, 600, 400),
            (1040 * 2, 600, 400)
        ]

        for x, y, width in arena_platforms:
            platform_left = x - width / 2
            platform_right = x + width / 2

            if (platform_left <= self.player.center_x <= platform_right and
                    y - 100 <= self.player.center_y <= y + 100):
                self.arena_active = True
                self.spawn_arena_robots()
                return

    def check_arena_completion(self):
        if not self.arena_active or self.arena_completed:
            return

        arena_robots_alive = False
        for robot in self.arena_robots:
            if robot.active and robot.spawned:
                arena_robots_alive = True
                break

        if not arena_robots_alive and self.arena_robots_spawned:
            self.arena_completed = True
            self.arena_active = False

            completion_time = int(time.time() - self.arena_start_time)

            if self.user_id:
                try:
                    from database import update_arena_progress
                    update_arena_progress(
                        user_id=self.user_id,
                        arena_completed=True,
                        robots_defeated=2,
                        damage_taken=int(100 - self.player.hp),
                        completion_time=completion_time
                    )
                except Exception:
                    pass

            self.arena_message = "Арена пройдена!"
            self.arena_message_timer = 3.0

    def create_platforms(self):
        floor_segments = 10
        segment_width = self.w / floor_segments
        segment_height = 160

        texture = self.platform

        floor_segment = arcade.Sprite()
        floor_segment.texture = texture
        floor_segment.center_x = segment_width / 2
        floor_segment.center_y = 51
        floor_segment.width = 1800
        floor_segment.height = 800
        self.platforms.append(floor_segment)
        self.background_platforms.append(floor_segment)

        lava = arcade.Sprite()
        lava.texture = arcade.load_texture("first_room/images/falling_lava.png")
        lava.center_x = 2300
        lava.center_y = 1580
        lava.width = 100
        lava.height = 540
        self.spikes.append(lava)

        platforms_data = [
            (280, (92 - 28) * 2, self.small_platform, 2000, 800, True),
            (420, 92 * 2, self.small_platform, 2000, 800, True),
            (560, 240, self.small_platform, 2000, 800, True),
            (820, 148 * 2, self.big_platform, 400, 100, True),
            (640, 258 * 2, self.platform, 1600, 600, True),
            (820, 368 * 2, self.big_platform, 400, 100, True),
            (1040, 368 * 2, self.platform, 1600, 600, True),
            (720 * 2, 600, self.big_platform, 400, 100, True),
            (830 * 2, 600, self.platform, 1600, 600, True),
            (920 * 2, 600, self.big_platform, 400, 100, True),
            (1040 * 2, 600, self.big_platform, 400, 100, True),
            (1340 * 2, 370 * 2, self.platform, 1600, 600, True),
            (285 * 2, 860, self.small_platform, 2000, 800, True),
            (85 * 2, 980, self.platform, 1600, 600, True),
            (15 * 2, 1100, self.small_platform, 2000, 800, True),
            (103 * 2, 1220, self.small_platform, 2000, 800, True),
            (280 * 2, 1340, self.big_platform, 400, 100, True),
            (530 * 2, 1290, self.big_platform, 400, 100, True),
            (665 * 2, 1100, self.small_platform, 2000, 800, True),
            (800 * 2, 1290, self.big_platform, 400, 100, True),
            (940 * 2, 1290, self.big_platform, 400, 100, True),
            (2150, 1410, self.platform, 1600, 600, True),
            (2150, 1430, self.small_platform, 2000, 800, True),
            (3000, 800, self.small_platform, 2000, 800, True),
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

        spike_locations = [
            (850, 386 * 2 - 1),
            (1050, 386 * 2 - 1),
        ]

        for x, y in spike_locations:
            spike = arcade.Sprite()
            spike.texture = self.spike_texture
            spike.center_x = x
            spike.center_y = y
            spike.width = 90
            spike.height = 37
            self.spikes.append(spike)

        trampoline_locations = [
            (460 * 2, 171 * 2, 80 * 2, 45 * 2),
            (285 * 2, 281 * 2, 80 * 2, 45 * 2),
            (2150, 1485, 160, 90)
        ]

        for x, y, width, height in trampoline_locations:
            trampoline = arcade.Sprite()
            trampoline.texture = self.trampoline_texture
            trampoline.center_x = x
            trampoline.center_y = y
            trampoline.width = width
            trampoline.height = height
            self.trampolines.append(trampoline)

            tramp_platform = arcade.Sprite()
            tramp_platform.texture = self.platform
            tramp_platform.center_x = x
            tramp_platform.center_y = y - height // 2 + 5
            tramp_platform.width = width
            tramp_platform.height = 10
            tramp_platform.alpha = 0
            self.platforms.append(tramp_platform)
            self.background_platforms.append(tramp_platform)

        wall_size = 40

        wall_y = 20 + 40 + wall_size * 3
        wall_x = wall_size // 2

        while wall_y < self.h:
            wall = arcade.Sprite()
            wall.texture = self.wall_texture
            wall.center_x = wall_x
            wall.center_y = wall_y
            wall.width = wall_size
            wall.height = wall_size
            self.walls.append(wall)

            wall_platform = arcade.Sprite()
            wall_platform.texture = self.wall_texture
            wall_platform.center_x = wall_x
            wall_platform.center_y = wall_y
            wall_platform.width = wall_size
            wall_platform.height = wall_size
            self.platforms.append(wall_platform)
            wall_y += wall_size

        wall_start_y = 20 + 40
        wall_height_available = self.h - wall_start_y
        middle_height = wall_start_y + wall_height_available // 2
        exit_start_y = middle_height + wall_size
        exit_end_y = exit_start_y + wall_size * 3

        wall_y = wall_start_y
        wall_x = self.w - wall_size // 2

        while wall_y < self.h:
            if not (exit_start_y <= wall_y < exit_end_y):
                wall = arcade.Sprite()
                wall.texture = self.wall_texture
                wall.center_x = wall_x
                wall.center_y = wall_y
                wall.width = wall_size
                wall.height = wall_size
                self.walls.append(wall)

                wall_platform = arcade.Sprite()
                wall_platform.texture = self.wall_texture
                wall_platform.center_x = wall_x
                wall_platform.center_y = wall_y
                wall_platform.width = wall_size
                wall_platform.height = wall_size
                self.platforms.append(wall_platform)
            wall_y += wall_size

        ceiling_y = self.h - wall_size // 2
        ceiling_x = wall_size // 2

        if self.dash_unlocked:
            while ceiling_x < self.w:
                ceiling = arcade.Sprite()
                ceiling.texture = self.wall_texture
                ceiling.center_x = ceiling_x
                ceiling.center_y = ceiling_y
                ceiling.width = wall_size
                ceiling.height = wall_size
                self.walls.append(ceiling)

                ceiling_platform = arcade.Sprite()
                ceiling_platform.texture = self.wall_texture
                ceiling_platform.center_x = ceiling_x
                ceiling_platform.center_y = ceiling_y
                ceiling_platform.width = wall_size
                ceiling_platform.height = wall_size
                self.platforms.append(ceiling_platform)
                ceiling_x += wall_size
        else:
            highest_trampoline_x = 2150
            highest_trampoline_y = 1460
            highest_trampoline_width = 160

            trampoline_left = highest_trampoline_x - highest_trampoline_width // 2
            trampoline_right = highest_trampoline_x + highest_trampoline_width // 2

            gap_left = trampoline_left - wall_size * 1.5
            gap_right = trampoline_right + wall_size * 1.5

            while ceiling_x < self.w:
                if gap_left <= ceiling_x <= gap_right:
                    ceiling_x += wall_size
                    continue

                ceiling = arcade.Sprite()
                ceiling.texture = self.wall_texture
                ceiling.center_x = ceiling_x
                ceiling.center_y = ceiling_y
                ceiling.width = wall_size
                ceiling.height = wall_size
                self.walls.append(ceiling)

                ceiling_platform = arcade.Sprite()
                ceiling_platform.texture = self.wall_texture
                ceiling_platform.center_x = ceiling_x
                ceiling_platform.center_y = ceiling_y
                ceiling_platform.width = wall_size
                ceiling_platform.height = wall_size
                self.platforms.append(ceiling_platform)
                ceiling_x += wall_size

    def update_robots(self, delta_time):
        for robot in self.robots_list:
            robot.update(delta_time)

            if not robot.active or not robot.spawned:
                continue

            for bullet in robot.bullets:
                if arcade.check_for_collision(self.player, bullet):
                    bullet.remove_from_sprite_lists()
                    damage_taken = self.player.take_damage(robot.bullet_damage)
                    if damage_taken and self.player.hp <= 0:
                        self.reset_player()
                    break

            if arcade.check_for_collision(self.player, robot):
                damage_taken = self.player.take_damage(robot.contact_damage)
                if damage_taken:
                    if self.player.center_x < robot.center_x:
                        self.player.change_x = -10
                    else:
                        self.player.change_x = 10
                    self.player.change_y = 5

                    if self.player.hp <= 0:
                        self.reset_player()

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
        self.dust_particles.draw()

        for geyser in self.geysers:
            geyser.draw()

        for robot in self.robots_list:
            robot.draw()

        self.player.draw()

        self.gui_camera.use()

        if self.player.dash_cooldown_timer > 0:
            cooldown_percent = self.player.dash_cooldown_timer / DASH_COOLDOWN
            self.dash_cooldown_text.text = f"Dash: {cooldown_percent * 100:.0f}%"
            self.dash_cooldown_text.x = SCREEN_WIDTH // 2
            self.dash_cooldown_text.y = SCREEN_HEIGHT - 50
            self.dash_cooldown_text.draw()

        if self.transition_to_room2 and self.transition_alpha > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                10000, 10000),
                (0, 0, 0, int(self.transition_alpha))
            )

    def on_update(self, delta_time):
        self.update_time = delta_time

        if self.arena_message_timer > 0:
            self.arena_message_timer -= delta_time

        if self.player.dashing:
            self.player.dash_timer -= delta_time
            if self.player.dash_timer <= 0:
                self.player.dashing = False
                if abs(self.player.change_x) > PLAYER_MOVEMENT_SPEED:
                    self.player.change_x = self.player.normal_speed * (1 if self.player.change_x > 0 else -1)

        if self.player.dash_cooldown_timer > 0:
            self.player.dash_cooldown_timer -= delta_time

        self.player.update(delta_time)

        for geyser in self.geysers:
            geyser.update(delta_time)

            if geyser.active and geyser.check_collision(self.player):
                damage_taken = self.player.take_damage(GEYSER_DAMAGE)
                if damage_taken:
                    geyser.apply_blast(self.player)

                    if self.player.hp <= 0:
                        self.reset_player()

        self.physics_engine.update()

        self.dust_particles.update(delta_time)

        spike_hit_list = arcade.check_for_collision_with_list(self.player, self.spikes)
        if spike_hit_list:
            self.reset_player()

        trampoline_hit_list = arcade.check_for_collision_with_list(self.player, self.trampolines)
        if trampoline_hit_list and self.player.change_y < 0:
            self.player.change_y = PLAYER_JUMP_SPEED * 1.5

        was_on_ground = self.player.on_ground
        self.player.on_ground = self.physics_engine.can_jump()

        self.player.update_texture()

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

        if self.player.bottom < -100:
            self.reset_player()

        if self.dash_unlocked and not self.arena_completed:
            self.check_arena_activation()
            self.check_arena_completion()

        self.check_player_attack()

        self.update_robots(delta_time)

        if self.player.center_y > self.level_top and not self.transition_to_room2:
            if not self.dash_unlocked:
                self.start_transition_to_room2()

        if self.transition_to_room2:
            self.transition_timer -= delta_time
            self.transition_alpha = min(255, (1 - self.transition_timer / self.transition_duration) * 255)

            if self.transition_timer <= 0:
                self.go_to_room2()

        self.update_camera_position(delta_time)

    def start_transition_to_room2(self):
        self.transition_to_room2 = True
        self.transition_timer = self.transition_duration
        self.transition_alpha = 0

    def go_to_room2(self):
        if self.user_id:
            update_current_room(self.user_id, 2)

        self.close()

        import first_room.drawing_second_room_first_lvl
        first_room.drawing_second_room_first_lvl.start_game()

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

        self.world_camera.position = (self.player.center_x, self.player.center_y)

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
        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
                self.player.jumping = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
            self.player.set_direction(False)
            self.player.dash_direction = -1
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
            self.player.set_direction(True)
            self.player.dash_direction = 1
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
        if key == arcade.key.LEFT or key == arcade.key.A:
            if self.player.change_x < 0:
                self.player.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            if self.player.change_x > 0:
                self.player.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            self.player.jumping = False

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.player.can_attack():
                self.player.start_attack()

    def check_player_attack(self):
        if not self.player.attacking:
            return

        hitbox = self.player.get_attack_hitbox()
        if not hitbox:
            return

        attack_left, attack_right, attack_bottom, attack_top = hitbox

        for robot in self.robots_list:
            if not robot.active or not robot.spawned:
                continue

            if (attack_right > robot.left and
                    attack_left < robot.right and
                    attack_top > robot.bottom and
                    attack_bottom < robot.top):

                damage = self.player.deal_damage()
                if damage > 0:
                    robot.take_damage(damage)


def start_game():
    window = GameWindow()
    arcade.run()


if __name__ == "__main__":
    start_game() 
