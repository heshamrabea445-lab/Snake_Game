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

        game.score = 1
        game.high_score = max(game.high_score, game.score)
        show_trophy_before_restart = (
            game.trophy_unlocked_after_restart
            and game.high_score > 0
            and not (game.starter_card_visible and game.starter_card_context == "launch")
        )
        assert not show_trophy_before_restart, "header trophy should stay hidden before a scoring run is restarted"

        game.high_score = 8
        game.score = 3
        game.game_state = "dead"
        game.starter_card_context = "death"
        game.starter_card_visible = True
        game.show_waiting_start_cue = False
        game._handle_starter_card_play()
        assert game.trophy_unlocked_after_restart, "death-card restart should unlock trophy display"
        assert game.game_state == "waiting", "death-card restart should reset into waiting state"
        assert game.score == 0, "death-card restart should reset the run score"
        assert game.high_score == 8, "death-card restart should keep the best score"
        assert not game.starter_card_visible, "death-card restart should not show the launch card"

        game.trophy_unlocked_after_restart = False
        game.high_score = 0
        game.score = 0
        game.game_state = "dead"
        game.starter_card_context = "death"
        game.starter_card_visible = True
        game.show_waiting_start_cue = False
        game._handle_starter_card_play()
        assert not game.trophy_unlocked_after_restart, "zero-score death restart should not unlock the trophy"

        game.high_score = 5
        game.score = 2
        game.game_state = "dead"
        game.starter_card_visible = False
        handled = game._handle_key_down(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        assert handled, "R on the death screen should trigger a restart"
        assert game.trophy_unlocked_after_restart, "keyboard restart should keep trophy display unlocked"
        assert game.game_state == "waiting", "keyboard restart should reset into waiting state"
        assert game.score == 0, "keyboard restart should reset the run score"
        assert game.high_score == 5, "keyboard restart should keep the best score"

        game.trophy_unlocked_after_restart = False
        game.high_score = 0
        game.score = 0
        game.game_state = "dead"
        game.starter_card_visible = False
        handled = game._handle_key_down(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        assert handled, "R on the death screen should still be handled for zero-score runs"
        assert not game.trophy_unlocked_after_restart, "zero-score keyboard restart should not unlock the trophy"

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
