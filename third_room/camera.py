import arcade
from third_room.config import SCREEN_HEIGHT, SCREEN_WIDTH, DEAD_ZONE_W, DEAD_ZONE_H, CAMERA_LERP


class Camera:
    def __init__(self):
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

        self.camera_target_x = 0
        self.camera_target_y = 0

    def set_position(self, x, y):
        self.world_camera.position = (x, y)
        self.camera_target_x = x
        self.camera_target_y = y

    def update(self, x, y):
        self.world_camera.position = (x, y)

        cam_x, cam_y = self.world_camera.position

        dz_left = cam_x - DEAD_ZONE_W // 2
        dz_right = cam_x + DEAD_ZONE_W // 2
        dz_bottom = cam_y - DEAD_ZONE_H // 2
        dz_top = cam_y + DEAD_ZONE_H // 2

        player_in_dz = (x >= dz_left and x <= dz_right and y >= dz_bottom and y <= dz_top)

        if not player_in_dz:
            if x < dz_left:
                self.camera_target_x = x + DEAD_ZONE_W // 2
            elif x > dz_right:
                self.camera_target_x = x - DEAD_ZONE_W // 2
            else:
                self.camera_target_x = cam_x

            if y < dz_bottom:
                self.camera_target_y = y + DEAD_ZONE_H // 2
            elif y > dz_top:
                self.camera_target_y = y - DEAD_ZONE_H // 2
            else:
                self.camera_target_y = cam_y
        else:
            self.camera_target_x = cam_x
            self.camera_target_y = cam_y

        half_viewport_w = SCREEN_WIDTH // 2
        half_viewport_h = SCREEN_HEIGHT // 2

        min_camera_x = half_viewport_w
        max_camera_x = SCREEN_WIDTH * 2 - half_viewport_w
        min_camera_y = 0 + half_viewport_h
        max_camera_y = SCREEN_HEIGHT * 2 - half_viewport_h

        self.camera_target_x = max(min(self.camera_target_x, max_camera_x), min_camera_x)
        self.camera_target_y = max(min(self.camera_target_y, max_camera_y), min_camera_y)

        current_x, current_y = self.world_camera.position
        new_x = current_x + (self.camera_target_x - current_x) * CAMERA_LERP
        new_y = current_y + (self.camera_target_y - current_y) * CAMERA_LERP

        new_x = max(min(new_x, max_camera_x), min_camera_x)
        new_y = max(min(new_y, max_camera_y), min_camera_y)

        self.world_camera.position = (new_x, new_y)