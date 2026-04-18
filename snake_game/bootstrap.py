import ctypes
import sys
from pathlib import Path

import pygame

from .constants import (
    AUDIO_MIXER_BUFFER,
    AUDIO_MIXER_CHANNELS,
    AUDIO_MIXER_FREQUENCY,
    AUDIO_MIXER_SIZE,
    AUDIO_RESERVED_CHANNELS,
    COLLISION_EFFECT_SCALE,
    COLLISION_SFX_CHANNEL_INDEX,
    COLLISION_SFX_VOLUME,
    CROPPED_UI_CANVAS_METADATA,
    DEATH_FACE_SCALE,
    EAT_SFX_VOLUME,
    EYE_SCALE,
    MOUTH_SCALE,
    TONGUE_SCALE,
    TURN_SFX_STACK_CHANNELS,
    TURN_SFX_VOLUME,
    WINDOW_H,
    WINDOW_W,
)


def configure_window(game):
    game.window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Snake")
    game.clock = pygame.time.Clock()
    game._set_window_icon()


def init_runtime_state(game):
    game._init_ui_state()
    game._init_asset_state()
    game._init_audio_state()


def init_ui_state(game):
    game.cursor_hand = pygame.SYSTEM_CURSOR_HAND
    game.cursor_default = pygame.SYSTEM_CURSOR_ARROW
    game.high_score = 0
    game.trophy_unlocked_after_restart = False
    game.fullscreen = False
    game.x_rect = None
    game.fs_rect = None
    game.vol_rect = None
    game._reset_overlay_state()


def init_asset_state(game):
    game._last_scale = None
    game._last_win_size = None
    game._scaled_assets = {}
    game._scaled_mouth_frames = []
    game._scaled_tongue_frames = []
    game._scaled_eye_frames = []
    game._scaled_death_face_frames = []
    game._scaled_collision_effect_frames = []

    game._raw = {}
    game.mouth_frames = []
    game.mouth_frame_open_amounts = []
    game.mouth_peak_frame_idx = 0
    game.snake_tongue = []
    game.eye_frames = []
    game.death_face_frames = []
    game.collision_effect_frames = []


def init_audio_state(game):
    game.turn_sound = None
    game.eat_sound = None
    game.collision_sound = None
    game.turn_channels = []
    game.next_turn_channel_idx = 0
    game.collision_channel = None
    game._audio_initialized = False
    game.audio_muted = False


def bootstrap_game(game):
    # Phase 1 - draw the launch screen as soon as the window is ready.
    game._load_startup_assets()
    game.new_game()
    game._show_starter_card("launch", run_score=0)
    game._ensure_assets()
    game._draw()

    # Phase 2 - finish loading the remaining runtime assets.
    game._load_remaining_assets()
    if game._last_scale is not None:
        game._refresh_scaled_animation_assets(game._last_scale)


def load_startup_assets(game):
    """Load assets required for the first visible frame (tiles, UI, mouth, eyes)."""
    game._load_raw_images()
    game._load_mouth_frames()
    game._load_eye_frames()


def load_remaining_assets(game):
    """Load assets needed after the first frame is already on screen."""
    game._load_tongue_frames()
    game._load_death_face_frames()
    game._load_collision_effect_frames()
    game._init_audio()


def resolve_asset_root():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # The original game resolved assets next to root-level main.py.
    # In the organized layout bootstrap.py lives under snake_game/, so we step
    # back to the repo root to preserve the same runtime asset paths.
    return Path(__file__).resolve().parents[1]


def asset_path(game, *parts):
    return str(game.base_dir.joinpath(*parts))


def restore_ui_canvas(name, surf):
    meta = CROPPED_UI_CANVAS_METADATA.get(name)
    if meta is None:
        return surf

    canvas_size = meta["canvas_size"]
    if surf.get_size() == canvas_size:
        return surf

    surf_w, surf_h = surf.get_size()
    canvas_w, canvas_h = canvas_size
    if surf_w > canvas_w or surf_h > canvas_h:
        return surf

    restored = pygame.Surface(canvas_size, pygame.SRCALPHA)
    restored.blit(surf, meta["offset"])
    return restored


def show_starter_card(game, context, run_score=0, reveal_ms=None):
    game.starter_card_context = context
    game.starter_card_run_score = max(0, int(run_score))
    game.starter_card_reveal_ms = reveal_ms
    game.starter_card_visible = reveal_ms is None
    game.show_waiting_start_cue = False
    game.play_button_rect = None


def hide_starter_card(game):
    game._reset_overlay_state(keep_waiting_cue=game.show_waiting_start_cue)


def reset_overlay_state(game, *, keep_waiting_cue=False):
    game.play_button_rect = None
    game.starter_card_visible = False
    game.starter_card_context = None
    game.starter_card_reveal_ms = None
    game.starter_card_run_score = 0
    game.show_waiting_start_cue = keep_waiting_cue


def show_waiting_start_cue(game):
    game.show_waiting_start_cue = True
    game._hide_starter_card()


def refresh_starter_card_visibility(game):
    if game.starter_card_visible or game.starter_card_reveal_ms is None:
        return
    if pygame.time.get_ticks() < game.starter_card_reveal_ms:
        return
    game.starter_card_visible = True
    game.starter_card_reveal_ms = None


def start_waiting_run(game, start_dir):
    if start_dir == (-game.direction[0], -game.direction[1]):
        return False

    now = pygame.time.get_ticks()
    game.show_waiting_start_cue = False
    game.game_state = "playing"
    game.last_frame_ms = now
    game.direction = start_dir
    game.next_dir = game.direction
    game.start_move_locked = True
    game.prev_direction = game.direction
    game.head_angle_deg = game._dir_to_angle(game.direction)
    game.turn_from_deg = game.head_angle_deg
    game.turn_to_deg = game.head_angle_deg
    game.turn_start_ms = now
    game.turn_end_ms = now
    game._cancel_tongue_rattle(now, reschedule=True)
    return True


def handle_starter_card_play(game):
    context = game.starter_card_context
    if context == "death":
        # Only unlock the header trophy after restarting from a scoring run.
        game.trophy_unlocked_after_restart = (
            game.trophy_unlocked_after_restart
            or game.starter_card_run_score > 0
            or game.score > 0
        )
        game.new_game()
        return
    game._show_waiting_start_cue()


def set_window_icon(game):
    try:
        icon_png = game._asset_path("images", "snake_icon.png")
        icon_ico = game._asset_path("images", "snake_icon.ico")
        pygame.display.set_icon(pygame.image.load(icon_png))
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("heshamrabea.snakegame")
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                image_icon = 1
                icon_small = 0
                icon_big = 1
                wm_seticon = 0x0080
                load_flags = 0x00000010 | 0x00000040
                hicon = ctypes.windll.user32.LoadImageW(None, icon_ico, image_icon, 0, 0, load_flags)
                if hicon:
                    ctypes.windll.user32.SendMessageW(hwnd, wm_seticon, icon_small, hicon)
                    ctypes.windll.user32.SendMessageW(hwnd, wm_seticon, icon_big, hicon)
    except Exception:
        pass


def quit_game(_game):
    pygame.quit()
    raise SystemExit


def scale_frame_set(_game, frames, scale, extra_scale=1.0, smooth=True):
    scaled_frames = []
    for src in frames:
        width = max(1, int(src.get_width() * scale * extra_scale))
        height = max(1, int(src.get_height() * scale * extra_scale))
        if (width, height) == src.get_size():
            scaled_frames.append(src)
        elif smooth:
            scaled_frames.append(pygame.transform.smoothscale(src, (width, height)))
        else:
            scaled_frames.append(pygame.transform.scale(src, (width, height)))
    return scaled_frames


def refresh_scaled_animation_assets(game, scale):
    game._scaled_mouth_frames = game._scale_frame_set(game.mouth_frames, scale, MOUTH_SCALE)
    game._scaled_tongue_frames = game._scale_frame_set(game.snake_tongue, scale, TONGUE_SCALE)
    game._scaled_eye_frames = game._scale_frame_set(game.eye_frames, scale, EYE_SCALE, smooth=False)
    game._scaled_death_face_frames = game._scale_frame_set(game.death_face_frames, scale, DEATH_FACE_SCALE)
    game._scaled_collision_effect_frames = game._scale_frame_set(
        game.collision_effect_frames,
        scale,
        COLLISION_EFFECT_SCALE,
    )


def init_audio(game):
    """Initialise the mixer once the window and first frame are ready."""
    if game._audio_initialized:
        return
    game._audio_initialized = True
    try:
        pygame.mixer.pre_init(
            AUDIO_MIXER_FREQUENCY,
            AUDIO_MIXER_SIZE,
            AUDIO_MIXER_CHANNELS,
            AUDIO_MIXER_BUFFER,
        )
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels(), AUDIO_RESERVED_CHANNELS))
        pygame.mixer.set_reserved(AUDIO_RESERVED_CHANNELS)
        game.turn_channels = [pygame.mixer.Channel(i) for i in range(TURN_SFX_STACK_CHANNELS)]
        game.collision_channel = pygame.mixer.Channel(COLLISION_SFX_CHANNEL_INDEX)
    except Exception:
        game.turn_channels = []
        game.collision_channel = None
        return

    game.turn_sound = game._load_sound("audio", "turn_sfx.mp3", volume=TURN_SFX_VOLUME)
    game.eat_sound = game._load_sound("audio", "eating.mp3", volume=EAT_SFX_VOLUME)
    game.collision_sound = game._load_sound("audio", "end_audio DEATH.mp3", volume=COLLISION_SFX_VOLUME)
    game._apply_audio_mute_state()


def load_sound(game, *parts, volume):
    try:
        sound = pygame.mixer.Sound(game._asset_path(*parts))
    except Exception:
        return None
    sound.set_volume(volume)
    return sound


def play_turn_sfx(game):
    if game.turn_sound is None or not game.turn_channels:
        return
    for channel in game.turn_channels:
        if not channel.get_busy():
            channel.play(game.turn_sound)
            return
    game.turn_channels[game.next_turn_channel_idx].play(game.turn_sound)
    game.next_turn_channel_idx = (game.next_turn_channel_idx + 1) % len(game.turn_channels)


def play_collision_sfx(game):
    for channel in game.turn_channels:
        channel.stop()
    if game.collision_sound is None or game.collision_channel is None:
        return
    game.collision_channel.play(game.collision_sound)


def play_eat_sfx(game):
    if game.eat_sound is None or not game.turn_channels:
        return
    for channel in game.turn_channels:
        if not channel.get_busy():
            channel.play(game.eat_sound)
            return
    game.turn_channels[game.next_turn_channel_idx].play(game.eat_sound)
    game.next_turn_channel_idx = (game.next_turn_channel_idx + 1) % len(game.turn_channels)


def stop_audio(game):
    for channel in game.turn_channels:
        channel.stop()
    if game.collision_channel is not None:
        game.collision_channel.stop()


def apply_audio_mute_state(game):
    turn_volume = 0.0 if game.audio_muted else TURN_SFX_VOLUME
    eat_volume = 0.0 if game.audio_muted else EAT_SFX_VOLUME
    collision_volume = 0.0 if game.audio_muted else COLLISION_SFX_VOLUME
    if game.turn_sound is not None:
        game.turn_sound.set_volume(turn_volume)
    if game.eat_sound is not None:
        game.eat_sound.set_volume(eat_volume)
    if game.collision_sound is not None:
        game.collision_sound.set_volume(collision_volume)


def toggle_audio_mute(game):
    game.audio_muted = not game.audio_muted
    if game._audio_initialized:
        game._apply_audio_mute_state()
    if game.audio_muted and game._audio_initialized:
        game._stop_audio()


def attach_bootstrap_methods(cls):
    cls._configure_window = configure_window
    cls._init_runtime_state = init_runtime_state
    cls._init_ui_state = init_ui_state
    cls._init_asset_state = init_asset_state
    cls._init_audio_state = init_audio_state
    cls._bootstrap_game = bootstrap_game
    cls._load_startup_assets = load_startup_assets
    cls._load_remaining_assets = load_remaining_assets
    cls._resolve_asset_root = staticmethod(resolve_asset_root)
    cls._asset_path = asset_path
    cls._restore_ui_canvas = staticmethod(restore_ui_canvas)
    cls._show_starter_card = show_starter_card
    cls._hide_starter_card = hide_starter_card
    cls._reset_overlay_state = reset_overlay_state
    cls._show_waiting_start_cue = show_waiting_start_cue
    cls._refresh_starter_card_visibility = refresh_starter_card_visibility
    cls._start_waiting_run = start_waiting_run
    cls._handle_starter_card_play = handle_starter_card_play
    cls._set_window_icon = set_window_icon
    cls._quit_game = quit_game
    cls._scale_frame_set = scale_frame_set
    cls._refresh_scaled_animation_assets = refresh_scaled_animation_assets
    cls._init_audio = init_audio
    cls._load_sound = load_sound
    cls._play_turn_sfx = play_turn_sfx
    cls._play_collision_sfx = play_collision_sfx
    cls._play_eat_sfx = play_eat_sfx
    cls._stop_audio = stop_audio
    cls._apply_audio_mute_state = apply_audio_mute_state
    cls._toggle_audio_mute = toggle_audio_mute
