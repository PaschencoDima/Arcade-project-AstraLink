import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database
init_database()


def run_login_window():
    import start_window.start_window as start_module
    start_module.main_login()


def run_story_window():
    from start_window.start_window import StoryWindow
    import arcade
    window = StoryWindow()
    window.setup()
    arcade.run()


def run_first_room():
    import first_room.drawing_first_room_first_lvl as game_module
    game_module.start_game()


def run_second_room():
    import first_room.drawing_second_room_first_lvl as game_module
    game_module.start_game()


def main():
    run_login_window()


if __name__ == "__main__":
    main()