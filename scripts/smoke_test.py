import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import SnakeGame


def run_smoke_test():
    original_main_loop = SnakeGame._main_loop
    SnakeGame._main_loop = lambda self: None

    try:
        game = SnakeGame()
        assert game.starter_card_visible, "starter card should be visible on boot"
        assert "snake_card" in game._raw, "startup assets should be loaded"

        game._handle_starter_card_play()
        assert "start_box" in game._raw, "start box should load on demand"

        game._toggle_fullscreen()
        assert "not_full_screen" in game._raw, "fullscreen exit icon should load on demand"

        game._toggle_audio_mute()
        assert "volume_muted" in game._raw, "muted icon should load on demand"

        game._ensure_lazy_animations("mouth", "eyes", "tongue", "death_face", "collision_effect")
        game._ensure_assets()
        game._draw()

        assert game.mouth_frames, "mouth frames should load"
        assert game.eye_frames, "eye frames should load"
        assert game.snake_tongue, "tongue frames should load"
        assert game.death_face_frames, "death face frames should load"
        assert game.collision_effect_frames, "collision effect frames should load"
    finally:
        SnakeGame._main_loop = original_main_loop
        pygame.quit()


if __name__ == "__main__":
    run_smoke_test()
