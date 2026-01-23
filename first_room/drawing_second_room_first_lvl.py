import arcade
import random
import math
import sys
import os
from arcade import SpriteList

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from player import Player, DustParticle
from database import get_current_user, update_player_progress, update_current_room, get_player_progress

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 675
TITLE = "Texture - Комната 2"

PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100

DASH_SPEED = 40
DASH_DURATION = 0.2
DASH_COOLDOWN = 1.0


class DashEnergyCircle:
    def __init__(self, player_x, player_y):
        self.center_x = player_x
        self.center_y = player_y
        self.radius = 200
        self.max_radius = 200
        self.min_radius = 10
        self.shrink_speed = 40
        self.alpha = 255
        self.lifetime = 5.0
        self.time_alive = 0
        self.active = True
        self.line_width = 3

        self.colors = [
            (100, 200, 255),
            (80, 180, 255),
            (150, 220, 255),
            (120, 210, 255)
        ]
        self.current_color = random.choice(self.colors)

    def update(self, delta_time, player_x, player_y):
        if not self.active:
            return False

        self.center_x = player_x
        self.center_y = player_y

        if self.radius > self.min_radius:
            self.radius -= self.shrink_speed * delta_time

        self.time_alive += delta_time

        color_index = int(self.time_alive * 3) % len(self.colors)
        self.current_color = self.colors[color_index]

        if self.time_alive > self.lifetime * 0.7:
            fade_percent = (self.time_alive - self.lifetime * 0.7) / (self.lifetime * 0.3)
            self.alpha = 255 * (1 - fade_percent)

        if self.time_alive >= self.lifetime or self.radius <= self.min_radius:
            self.active = False
            return False

        return True

    def draw(self):
        if not self.active:
            return

        color_with_alpha = (
            self.current_color[0],
            self.current_color[1],
            self.current_color[2],
            int(self.alpha)
        )

        arcade.draw_circle_outline(
            self.center_x,
            self.center_y,
            self.radius,
            color_with_alpha,
            self.line_width
        )

        if self.radius > 30:
            inner_alpha = int(self.alpha * 0.7)
            inner_color = (
                self.current_color[0],
                self.current_color[1],
                self.current_color[2],
                inner_alpha
            )

            arcade.draw_circle_outline(
                self.center_x,
                self.center_y,
                self.radius * 0.8,
                inner_color,
                max(1, self.line_width - 1)
            )


class DashPowerup:
    def __init__(self, x, y):
        self.center_x = x
        self.center_y = y
        self.width = 80
        self.height = 80
        self.collected = False
        self.collection_timer = 0
        self.collection_duration = 5.0

        self.show_dash_image = False
        self.dash_image_alpha = 0
        self.dash_image_timer = 0
        self.dash_image_duration = 3.0

        self.texture = arcade.load_texture("first_room/images/dash_get.png")

        self.pulse_timer = 0
        self.pulse_speed = 2.0
        self.pulse_scale = 1.0

    def update(self, delta_time):
        if not self.collected:
            self.pulse_timer += delta_time * self.pulse_speed
            self.pulse_scale = 1.0 + 0.15 * math.sin(self.pulse_timer)
        else:
            self.collection_timer -= delta_time

            if self.collection_timer <= 0 and not self.show_dash_image:
                self.show_dash_image = True
                self.dash_image_timer = self.dash_image_duration

            if self.show_dash_image:
                self.dash_image_timer -= delta_time
                if self.dash_image_alpha < 255:
                    self.dash_image_alpha = min(255, self.dash_image_alpha + 500 * delta_time)

    def draw(self):
        if not self.collected:
            current_width = self.width * self.pulse_scale
            current_height = self.height * self.pulse_scale

            arcade.draw_texture_rect(
                self.texture,
                arcade.rect.XYWH(
                    self.center_x,
                    self.center_y,
                    current_width,
                    current_height
                )
            )

    def draw_dash_image(self, screen_width, screen_height):
        if self.show_dash_image and self.dash_image_alpha > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(
                    screen_width // 2,
                    screen_height // 2,
                    screen_width,
                    screen_height
                ),
                (0, 0, 0, int(self.dash_image_alpha * 0.8))
            )

            arcade.draw_texture_rect(
                self.texture,
                arcade.rect.XYWH(
                    screen_width // 2,
                    screen_height // 2,
                    self.width * 4,
                    self.height * 4
                ),
                alpha=int(self.dash_image_alpha)
            )

    def check_collision(self, player):
        if self.collected:
            return False

        current_width = self.width * self.pulse_scale
        current_height = self.height * self.pulse_scale

        powerup_left = self.center_x - current_width / 2
        powerup_right = self.center_x + current_width / 2
        powerup_bottom = self.center_y - current_height / 2
        powerup_top = self.center_y + current_height / 2

        player_left = player.left
        player_right = player.right
        player_bottom = player.bottom
        player_top = player.top

        collision = (
                player_right > powerup_left and
                player_left < powerup_right and
                player_top > powerup_bottom and
                player_bottom < powerup_top
        )

        if collision and not self.collected:
            self.collected = True
            self.collection_timer = self.collection_duration
            return True

        return False

    def is_complete(self):
        return self.show_dash_image and self.dash_image_timer <= 0


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.w = width
        self.h = height

        self.physics_engine = None
        self.platforms = None
        self.walls = None
        self.background_platforms = None
        self.player = None
        self.dust_particles = None

        self.dash_powerup = None
        self.powerup_collected = False
        self.player_stuck = False
        self.stuck_timer = 0

        self.energy_circles = []
        self.circle_timer = 0
        self.circle_interval = 0.5

        self.texture = None
        self.wall_texture = None
        self.small_platform = None
        self.platform = None

        self.dash_cooldown_text = arcade.Text(
            "",
            0, 0,
            arcade.color.RED,
            12,
            align="center",
            anchor_x="center",
            anchor_y="center"
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

        # HP плашка параметры
        self.health_bar_width = 200
        self.health_bar_height = 20

        self.user_id = get_current_user()
        self.dash_unlocked = False

        if self.user_id:
            progress = get_player_progress(self.user_id)
            if isinstance(progress, dict):
                self.dash_unlocked = progress.get('dash_unlocked', False)
            else:
                self.dash_unlocked = False

            if self.dash_unlocked:
                self.close()
                import first_room.drawing_first_room_first_lvl
                first_room.drawing_first_room_first_lvl.start_game()
                return

            update_current_room(self.user_id, 2)

        self.setup()

    def setup(self):
        if self.dash_unlocked:
            return

        self.texture = arcade.load_texture("first_room/images/background.png")
        self.wall_texture = arcade.load_texture('first_room/images/wall.png')
        self.small_platform = arcade.load_texture('first_room/images/platform3.png')
        self.platform = arcade.load_texture('first_room/images/platform1.png')

        self.platforms = SpriteList()
        self.walls = arcade.SpriteList()
        self.background_platforms = arcade.SpriteList()
        self.dust_particles = arcade.SpriteList()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        original_cwd = os.getcwd()

        parent_dir = os.path.dirname(script_dir)
        os.chdir(parent_dir)

        self.player = Player(dash_unlocked=False)
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = 140

        os.chdir(original_cwd)

        self.dash_powerup = DashPowerup(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)

        platforms_data = [
            (SCREEN_WIDTH / 4 - 30, 140, self.small_platform, 2000, 800, True),
            (SCREEN_WIDTH / 4 * 3 + 30, 140, self.small_platform, 2000, 800, True),
            (SCREEN_WIDTH / 2 + 100, 260, self.small_platform, 2000, 800, True),
            (SCREEN_WIDTH / 2 - 100, 260, self.small_platform, 2000, 800, True),
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

        wall_size = 40

        wall_y = 0
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

        wall_y = 0
        wall_x = self.w - wall_size // 2

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

            ceiling_platform = arcade.Sprite()
            ceiling_platform.texture = self.wall_texture
            ceiling_platform.center_x = ceiling_x
            ceiling_platform.center_y = ceiling_y
            ceiling_platform.width = wall_size
            ceiling_platform.height = wall_size
            self.platforms.append(ceiling_platform)
            ceiling_x += wall_size

        floor_y = wall_size // 2
        floor_x = wall_size // 2

        while floor_x < self.w:
            floor = arcade.Sprite()
            floor.texture = self.wall_texture
            floor.center_x = floor_x
            floor.center_y = floor_y
            floor.width = wall_size
            floor.height = wall_size
            self.walls.append(floor)

            floor_platform = arcade.Sprite()
            floor_platform.texture = self.wall_texture
            floor_platform.center_x = floor_x
            floor_platform.center_y = floor_y
            floor_platform.width = wall_size
            floor_platform.height = wall_size
            self.platforms.append(floor_platform)
            floor_x += wall_size

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.platforms,
            gravity_constant=GRAVITY
        )

    def create_dust_effect(self):
        for _ in range(random.randint(15, 20)):
            particle = DustParticle(self.player.center_x, self.player.bottom)
            self.dust_particles.append(particle)

    def create_energy_circle(self):
        circle = DashEnergyCircle(self.player.center_x, self.player.center_y)
        self.energy_circles.append(circle)

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h))

        self.walls.draw()
        self.background_platforms.draw()

        self.dash_powerup.draw()

        self.dust_particles.draw()

        for circle in self.energy_circles[:]:
            circle.draw()

        # Отрисовка игрока через метод draw() класса Player
        if hasattr(self.player, 'draw'):
            self.player.draw()

        self.dash_powerup.draw_dash_image(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Отрисовка плашки HP
        self.draw_health_bar()

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

        self.health_text.text = f"HP: {int(self.player.hp)}/{self.player.max_hp}"
        self.health_text.x = bar_x + bar_width / 2
        self.health_text.y = bar_y
        self.health_text.draw()

    def on_update(self, delta_time):
        if self.dash_unlocked:
            return

        if self.player_stuck:
            self.stuck_timer -= delta_time
            if self.stuck_timer <= 0:
                self.player_stuck = False

        if not self.player_stuck:
            if self.player.dashing:
                self.player.dash_timer -= delta_time
                if self.player.dash_timer <= 0:
                    self.player.dashing = False
                    if abs(self.player.change_x) > PLAYER_MOVEMENT_SPEED:
                        self.player.change_x = self.player.normal_speed * (1 if self.player.change_x > 0 else -1)

            if self.player.dash_cooldown_timer > 0:
                self.player.dash_cooldown_timer -= delta_time

            self.physics_engine.update()

            self.player.update(delta_time)

            self.dust_particles.update(delta_time)

            was_on_ground = self.player.on_ground
            self.player.on_ground = self.physics_engine.can_jump()

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

        self.dash_powerup.update(delta_time)

        if not self.powerup_collected and self.dash_powerup.check_collision(self.player):
            self.powerup_collected = True
            self.player_stuck = True
            self.stuck_timer = self.dash_powerup.collection_duration
            self.player.change_x = 0
            self.player.change_y = 0

            self.create_energy_circle()
            self.circle_timer = self.circle_interval

        if self.player_stuck:
            self.circle_timer -= delta_time
            if self.circle_timer <= 0:
                self.circle_timer = self.circle_interval
                self.create_energy_circle()

        active_circles = []
        for circle in self.energy_circles:
            if circle.update(delta_time, self.player.center_x, self.player.center_y):
                active_circles.append(circle)
        self.energy_circles = active_circles

        if self.dash_powerup.is_complete():
            self.complete_dash_powerup()

    def complete_dash_powerup(self):
        self.player.unlock_dash()

        if self.user_id:
            from database import unlock_dash_ability
            unlock_dash_ability(self.user_id)
            update_current_room(self.user_id, 1)

        self.close()
        import first_room.drawing_first_room_first_lvl
        first_room.drawing_first_room_first_lvl.start_game()

    def reset_player(self):
        floor_y = 40
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = floor_y + self.player.height / 2
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.hp = PLAYER_MAX_HP

        self.player.dashing = False
        self.player.dash_timer = 0
        self.player.dash_cooldown_timer = 0

        self.player.invincible_timer = 0

    def on_key_press(self, key, modifiers):
        if self.dash_unlocked or self.player_stuck:
            return

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
                self.player.jumping = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
            self.player.dash_direction = -1
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
            self.player.dash_direction = 1
        elif key == arcade.key.Q:
            if self.player.dash_unlocked:
                self.player.activate_dash()
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
        if self.dash_unlocked or self.player_stuck:
            return

        if key == arcade.key.LEFT or key == arcade.key.A:
            if self.player.change_x < 0:
                self.player.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            if self.player.change_x > 0:
                self.player.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            self.player.jumping = False


def start_game():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
    arcade.run()


if __name__ == "__main__":
    start_game()