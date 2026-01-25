import arcade
import sys
import os
import random
import time
from player import Player, DustParticle
from database import get_current_user, update_current_room, get_player_progress
from first_room.drawing_first_room_first_lvl import Geyser
from third_room.key_artefact import Key
from third_room.walls import Wall
from third_room.door import Door
from third_room.config import *
from third_room.health_bar import HealthBar
from third_room.platforms import Platforms
from third_room.camera import Camera
from third_room.boss import Boss

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, antialiasing=True)
        self.w = SCREEN_WIDTH * 2
        self.h = SCREEN_HEIGHT * 2
        self.texture = arcade.load_texture("third_room/images/bg.png")

        self.user_id = get_current_user()
        self.dash_unlocked = False

        if self.user_id:
            self.dash_unlocked = get_player_progress(self.user_id)
            update_current_room(self.user_id, 1)

        self.camera = Camera()
        self.player = Player(dash_unlocked=self.dash_unlocked)
        self.platforms = Platforms()
        self.walls = Wall()
        self.door = Door()
        self.health = HealthBar()
        self.key = Key(125, 1650)

        self.spikes = arcade.SpriteList()
        self.dust_particles = arcade.SpriteList()
        self.geysers = arcade.SpriteList()
        self.robots_list = arcade.SpriteList()

        self.dash_cooldown_text = None

        self.physics_engine = None

        self.boss = Boss(1500, 123, self.player)

        self.robots_list = arcade.SpriteList()

        self.setup()

    def setup(self):
        self.spike_texture = arcade.load_texture("first_room/images/spikes.png")

        self.dash_cooldown_text = arcade.Text(
            "",
            0, 0,
            arcade.color.RED,
            12,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )


        self.platforms.create()
        self.create_spikes()
        self.create_geysers()
        self.create_walls()
        self.create_door()
        boss_list = arcade.SpriteList()
        boss_list.append(self.boss)
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            (
                self.platforms.elements,
                self.walls.elements,
                self.door.elements,
                self.geysers,
                boss_list,
                self.boss.bullet_list
            ),
            gravity_constant=GRAVITY
        )
        self.player.unlock_double_jump()
        self.camera.set_position(self.player.center_x, self.player.center_y)

    def create_dust_effect(self):
        for _ in range(random.randint(15, 20)):
            particle = DustParticle(self.player.center_x, self.player.bottom)
            self.dust_particles.append(particle)

    def create_spikes(self):
        end_x = 2380
        x = 1250
        y = 750

        while x < end_x:
            spike = arcade.Sprite()
            spike.texture = self.spike_texture
            spike.center_x = x
            spike.center_y = y
            spike.width = 90
            spike.height = 37
            self.spikes.append(spike)
            x += 90

    def create_geysers(self):
        geyser_x = 460
        geyser_y = 1365
        geyser = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser)
        geyser_x = 1500
        geyser_y = 1315
        geyser = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser)
        geyser_x = 1760
        geyser_y = 1315
        geyser = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser)
        geyser_x = 1960
        geyser_y = 1315
        geyser = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser)


    def create_door(self):
        self.door.create(1180, self.h - self.door.height)

    def create_walls(self):
        self.walls.create_vertical(20, 180, self.h)
        self.walls.create_vertical(self.w - 20, 60, self.h)
        self.walls.create_vertical(1180, 60, self.h - self.door.height)

        self.walls.create_horizontal(self.h - 20, 20, self.w)
        self.walls.create_horizontal(20, 1180, self.w + 20)

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
        self.camera.world_camera.use()

        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(
                self.w // 2,
                self.h // 2,
                self.w,
                self.h
            )
        )

        self.boss.draw()
        self.platforms.draw()
        self.walls.draw()
        self.door.draw()
        self.spikes.draw()
        self.dust_particles.draw()
        self.key.draw()
        self.boss_dead()

        for geyser in self.geysers:
            geyser.draw()

        for robot in self.robots_list:
            robot.draw()

        self.player.draw()

        self.camera.gui_camera.use()

        # Отрисовка плашки HP

        self.health.hp = self.player.hp
        self.health.draw()

        if self.player.dash_cooldown_timer > 0:
            cooldown_percent = self.player.dash_cooldown_timer / DASH_COOLDOWN
            self.dash_cooldown_text.text = f"Dash: {cooldown_percent * 100:.0f}%"
            self.dash_cooldown_text.x = SCREEN_WIDTH // 2
            self.dash_cooldown_text.y = SCREEN_HEIGHT - 50
            self.dash_cooldown_text.draw()

    def on_update(self, delta_time):
        if self.player.hp <= 0:
            self.reset_player()
            self.boss.state = "walk"

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

        was_on_ground = self.player.on_ground
        self.player.on_ground = self.physics_engine.can_jump()

        if not was_on_ground and self.player.on_ground:
            self.create_dust_effect()

        if self.player.bottom < -100:
            self.reset_player()

        self.check_player_attack()

        if self.key.check_collision(self.player):
            self.key.get()
            self.open_door()

        self.boss.update(delta_time)
        self.boss.update_animation(delta_time)

        self.camera.update(self.player.center_x, self.player.center_y)

    def open_door(self):
        self.door.kill_door()
        self.boss.spawn()

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

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
                self.player.jumping = True
                self.player.jumps_used = 0
            elif self.player.double_jump_unlocked:
                self.player.jumps_used = 1
                success = self.player.double_jump()
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

    def boss_dead(self):
        if self.boss.state != "dead":
            return
        bar_width = 400
        bar_height = 200
        bar_y_offset = 200

        arcade.draw_rect_filled(arcade.rect.XYWH(
            self.player.center_x,
            self.player.center_y + bar_y_offset,
            bar_width + 4,
            bar_height + 4),
            arcade.color.WHITE
        )

        arcade.draw_rect_filled(arcade.rect.XYWH(
            self.player.center_x,
            self.player.center_y + bar_y_offset,
            bar_width,
            bar_height),
            arcade.color.LIGHT_PASTEL_PURPLE
        )

        health_text = "Labuda is dead. You won!"
        arcade.draw_text(
            health_text,
            self.player.center_x,
            self.player.center_y + bar_y_offset - 1,
            arcade.color.WHITE,
            25,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )


def start_game():
    window = GameWindow()
    arcade.run()


if __name__ == "__main__":
    start_game()