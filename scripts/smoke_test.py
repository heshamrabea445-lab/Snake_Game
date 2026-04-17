import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import SnakeGame


def run_smoke_test():
    repo_root = Path(__file__).resolve().parents[1]
    original_main_loop = SnakeGame._main_loop
    SnakeGame._main_loop = lambda self: None

    try:
        game = SnakeGame()
        assert (repo_root / "audio" / "eating.mp3").exists(), "desktop eat audio asset should exist"
        assert (repo_root / "docs" / "assets" / "audio" / "eating.mp3").exists(), "web eat audio asset should exist"
        assert game.starter_card_visible, "starter card should be visible on boot"
        assert "snake_card" in game._raw, "startup assets should be loaded"
        assert "start_box" in game._raw, "waiting cue assets should load on boot"
        assert "not_full_screen" in game._raw, "fullscreen exit icon should load on boot"
        assert "volume_muted" in game._raw, "muted icon should load on boot"

        assert game.mouth_frames, "mouth frames should load on boot"
        assert game.eye_frames, "eye frames should load on boot"
        assert game.snake_tongue, "tongue frames should load on boot"
        assert game.death_face_frames, "death face frames should load on boot"
        assert game.collision_effect_frames, "collision effect frames should load on boot"
        assert game._scaled_eye_frames, "scaled eye frames should be ready on boot"
        assert game.eat_sound is not None, "eat sound should load on boot"

        game._handle_starter_card_play()
        assert game.show_waiting_start_cue, "play should show the waiting cue"
        assert not game.starter_card_visible, "play should hide the starter card"

        game._toggle_fullscreen()
        game._toggle_audio_mute()
        game._ensure_assets()
        game._draw()

        assert game._scaled_mouth_frames, "scaled mouth frames should be ready"
        assert game._scaled_tongue_frames, "scaled tongue frames should be ready"
        assert game._scaled_death_face_frames, "scaled death face frames should be ready"
        assert game._scaled_collision_effect_frames, "scaled collision effect frames should be ready"
    finally:
        SnakeGame._main_loop = original_main_loop
        pygame.quit()


if __name__ == "__main__":
    run_smoke_test()
