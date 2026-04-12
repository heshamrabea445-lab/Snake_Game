import pygame
import random
from collections import deque
import math
from pathlib import Path
import sys


# ── Base design resolution ─────────────────────────────────────────────────────
BASE_W   = 650
BASE_H   = 650

WINDOW_W = 650
WINDOW_H = 650

HEADER_H_BASE  = 70
TILE_SIZE_BASE = 34
GRID_COLS = 18
GRID_ROWS = 16
START_SNAKE_SEGMENTS = 4

TICK_RATE = 125
FPS       = 60
DEATH_FACE_COLLISION_INTRO_MS = 300
DEATH_FACE_RECOIL_MS = 75
DEATH_OVERLAY_REVEAL_MS = 960
DEATH_SCREEN_DELAY_MS = max(0, DEATH_OVERLAY_REVEAL_MS - (DEATH_FACE_COLLISION_INTRO_MS + DEATH_FACE_RECOIL_MS))
BORDER_CONTACT_INSET_TILES = 0.88
COLLISION_BACKUP_TILES = 1.0
COLLISION_PATH_EXTRA_CELLS = int(math.ceil(COLLISION_BACKUP_TILES)) + 2
COLLISION_TAIL_INSET_TILES = 0.30
COLLISION_EFFECT_SCALE = 1.5
COLLISION_EFFECT_FRAME_COUNT = 21
COLLISION_EFFECT_SPEED_MULT = 2.5
COLLISION_EFFECT_ANCHOR_FWD = -1.2
COLLISION_EFFECT_EXTRA_ROT_DEG = 180
STARTER_CARD_BASE_W = 310
STARTER_CARD_BUTTON_GAP = 12
STARTER_CARD_STAT_LEFT_X = 0.29
STARTER_CARD_STAT_RIGHT_X = 0.71
STARTER_CARD_STAT_Y = 0.44
STARTER_CARD_DIM_ALPHA = 160
STARTER_CARD_Y_OFFSET = 66
WAITING_CUE_ICON_BASE_W = 92
WAITING_CUE_BOX_PAD = 14
WAITING_CUE_BOX_ALPHA = 150
WAITING_CUE_BOX_RADIUS = 16
WAITING_CUE_CENTER_Y_RATIO = 0.24
DEATH_FACE_FRAME_COUNT = 36
DEATH_FACE_SCALE = 1.0
DEATH_FACE_SEPARATOR_W = 1
DEATH_FACE_RECOIL_START_FRAME = 6
DEATH_FACE_TWITCH_START_FRAME = 17
DEATH_FACE_TWITCH_FRAME_MS = 75
DEATH_FACE_PRE_TWITCH_ANCHOR = -0.05
DEATH_FACE_TWITCH_ANCHOR = -0.27
DEATH_FACE_TWITCH_BLEND_FRAMES = 17
DEATH_FACE_FRAME_LIFT = -0.10
AUDIO_MIXER_FREQUENCY = 44100
AUDIO_MIXER_SIZE = -16
AUDIO_MIXER_CHANNELS = 2
AUDIO_MIXER_BUFFER = 512
TURN_SFX_STACK_CHANNELS = 4
COLLISION_SFX_CHANNEL_INDEX = TURN_SFX_STACK_CHANNELS
AUDIO_RESERVED_CHANNELS = TURN_SFX_STACK_CHANNELS + 1
TURN_SFX_VOLUME = 0.35
COLLISION_SFX_VOLUME = 0.75
# ── Colours ───────────────────────────────────────────────────────────────────
HEADER_COLOUR  = ( 78, 112,  50)
PANEL_COLOUR   = ( 87, 138,  52)
TILE_LIGHT     = (154, 202,  60)
TILE_DARK      = (140, 185,  50)
SNAKE_HEAD_COL      = ( 78, 126, 240)   # base snake body/head blue
SNAKE_TAIL_DARK_MAX = ( 18,  38, 110)   # dark navy – maximum tail darkness
APPLE_DARKEN_STEP   = 0.050             # ~25 apples to reach full dark navy
MOUTH_TRIGGER_RADIUS_TILES = 2
MOUTH_OPEN_CLOSE_FRAMES = 10
MOUTH_CLOSE_DELAY_SEC = 0.15
MOUTH_ANCHOR_FWD = 0.45
MOUTH_ANCHOR_SIDE = 0.00
MOUTH_SCALE = 1.20
TONGUE_RATTLE_MIN_SEC = 0
TONGUE_RATTLE_MAX_SEC = 10.0
TONGUE_RATTLE_MODE_SEC = 5.0
TONGUE_FRAME_SEC = 0.025
TONGUE_SCALE = 1.10
TONGUE_ANCHOR_FWD = 0.45
TONGUE_ANCHOR_SIDE = 0.00
TONGUE_SHADOW_SCALE = 0.88
TONGUE_SHADOW_ALPHA = 40
TONGUE_SHADOW_YOFF_FACTOR = 0.16
TONGUE_BASE_OFFSET = 0.42
EYE_CENTER_FWD = -0.45
EYE_CENTER_SIDE = 0.00
EYE_SEPARATION = 0.32
EYE_SHADOW_SCALE = 0.8
SNAKE_SHADOW_ALPHA = 40
SNAKE_SHADOW_YOFF_FACTOR = 0.42
SNAKE_SHADOW_RADIUS_FACTOR = 0.96
EYE_BLINK_MIN_SEC = max(1.0, TONGUE_RATTLE_MIN_SEC * 0.5)
EYE_BLINK_MAX_SEC = max(EYE_BLINK_MIN_SEC, TONGUE_RATTLE_MAX_SEC * 0.5)
EYE_BLINK_MODE_SEC = max(EYE_BLINK_MIN_SEC, TONGUE_RATTLE_MODE_SEC * 0.5)
EYE_BLINK_FRAME_SEC = 0.035
BULGE_START_SCALE = 1.75
BULGE_MIN_END_SCALE = 1.00
BULGE_SHADOW_ALPHA = 34
BULGE_END_HIDE_T = 0.96
BULGE_SPAWN_DELAY_FRAMES = 4
BULGE_TRAVEL_SEG_PER_TICK = 1
BULGE_FADE_SEGMENTS_CAP = 25 
BULGE_MIN_VISIBLE_SCALE = 1.
BULGE_SAMPLE_STEP_FACTOR = 0.40
FACE_SHADOW_ALPHA = 38
FACE_SHADOW_YOFF_FACTOR = 0.55
MOUTH_SHADOW_SCALE = 0.95
SEGMENT_SHRINK_PER_SEG = 0.25
TAIL_MIN_RADIUS_FACTOR = 0.62
EYE_FRAME_COUNT = 9
EYE_FRAME_W = 28
EYE_SEPARATOR_W = 1

EYE_WHITE    = (235, 235, 235)
EYE_PUPIL    = ( 20,  20,  20)
EYE_RING     = ( 95, 135, 235)
NOSE_CLR     = ( 18,  60, 160)
SCORE_COLOUR = (255, 255, 255)

RIGHT = ( 1,  0)
LEFT  = (-1,  0)
DOWN  = ( 0,  1)
UP    = ( 0, -1)

DIR_KEYS = {
    pygame.K_RIGHT: RIGHT,  pygame.K_d: RIGHT,
    pygame.K_LEFT:  LEFT,   pygame.K_a: LEFT,
    pygame.K_DOWN:  DOWN,   pygame.K_s: DOWN,
    pygame.K_UP:    UP,     pygame.K_w: UP,
}

CROPPED_UI_CANVAS_METADATA = {
    "apple_icon": {"canvas_size": (40, 40), "offset": (8, 3)},
    "full_screen": {"canvas_size": (40, 40), "offset": (11, 10)},
    "not_full_screen": {"canvas_size": (40, 36), "offset": (6, 4)},
    "start_box": {"canvas_size": (92, 84), "offset": (23, 22)},
    "trophy": {"canvas_size": (40, 40), "offset": (8, 5)},
    "x": {"canvas_size": (40, 40), "offset": (12, 12)},
}


# ── Pure helpers ──────────────────────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * t

def lerp_pt(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))

def angle_lerp_shortest(a_deg, b_deg, t):
    diff = (b_deg - a_deg + 180.0) % 360.0 - 180.0
    return a_deg + diff * t

def mix_colour(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

def ease_out_quad(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) * (1.0 - t)

def draw_capsule(surface, colour, c1, c2, radius):
    pygame.draw.circle(surface, colour, (int(c1[0]), int(c1[1])), radius)
    pygame.draw.circle(surface, colour, (int(c2[0]), int(c2[1])), radius)
    dx = c2[0] - c1[0];  dy = c2[1] - c1[1]
    dist = math.hypot(dx, dy)
    if dist < 0.5:
        return
    nx = -dy / dist * radius;  ny = dx / dist * radius
    pygame.draw.polygon(surface, colour, [
        (c1[0]+nx, c1[1]+ny), (c1[0]-nx, c1[1]-ny),
        (c2[0]-nx, c2[1]-ny), (c2[0]+nx, c2[1]+ny),
    ])


# ── Game ──────────────────────────────────────────────────────────────────────
class SnakeGame:

    def __init__(self):
        pygame.mixer.pre_init(
            AUDIO_MIXER_FREQUENCY,
            AUDIO_MIXER_SIZE,
            AUDIO_MIXER_CHANNELS,
            AUDIO_MIXER_BUFFER,
        )
        pygame.init()
        self.base_dir = self._resolve_asset_root()
        self._configure_window()
        self._init_runtime_state()
        self._init_deferred_loading()
        self._bootstrap_launch_screen()
        self._main_loop()

    # ── Startup ───────────────────────────────────────────────────────────────
    def _configure_window(self):
        self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.set_caption("Snake")
        self.clock = pygame.time.Clock()

    def _init_runtime_state(self):
        self.cursor_hand = pygame.SYSTEM_CURSOR_HAND
        self.cursor_default = pygame.SYSTEM_CURSOR_ARROW
        self.high_score = 0
        self.fullscreen = False
        self.x_rect = None
        self.fs_rect = None
        self.vol_rect = None
        self.play_button_rect = None
        self._last_fs_toggle_ms = 0

        self._last_scale = None
        self._last_win_size = None
        self._scaled_assets = {}
        self._scaled_mouth_frames = []
        self._scaled_tongue_frames = []
        self._scaled_eye_frames = []
        self._scaled_death_face_frames = []
        self._scaled_collision_effect_frames = []

        self._raw = {}
        self.mouth_frames = []
        self.mouth_frame_open_amounts = []
        self.mouth_peak_frame_idx = 0
        self.snake_tongue = []
        self.eye_frames = []
        self.death_face_frames = []
        self.collision_effect_frames = []

        self.turn_sound = None
        self.collision_sound = None
        self.turn_channels = []
        self.next_turn_channel_idx = 0
        self.collision_channel = None
        self._audio_initialized = False
        self.audio_muted = False

        self.starter_card_visible = False
        self.starter_card_context = None
        self.starter_card_reveal_ms = None
        self.starter_card_run_score = 0
        self.show_waiting_start_cue = False
        self._deferred_tasks_started = False

    def _init_deferred_loading(self):
        self._startup_raw_keys = (
            "tile_light",
            "tile_dark",
            "trophy",
            "apple_icon",
            "snake_card",
            "play_button",
            "x",
            "full_screen",
            "volume",
        )
        self._deferred_startup_tasks = deque([
            lambda: self._load_raw_images(("start_box",)),
            lambda: self._load_raw_images(("not_full_screen",)),
            lambda: self._load_raw_images(("volume_muted",)),
            self._set_window_icon,
            self._init_audio,
        ])
        self._lazy_animation_loaders = {
            "mouth": self._load_mouth_frames,
            "eyes": self._load_eye_frames,
            "tongue": self._load_tongue_frames,
            "death_face": self._load_death_face_frames,
            "collision_effect": self._load_collision_effect_frames,
        }
        self._lazy_animation_queue = deque(self._lazy_animation_loaders)
        self._lazy_animation_pending = set(self._lazy_animation_loaders)

    def _bootstrap_launch_screen(self):
        self._load_raw_images(self._startup_raw_keys)
        self.new_game()
        self._show_starter_card("launch", run_score=0)
        self._ensure_assets()
        self._draw()

    # ── Assets ────────────────────────────────────────────────────────────────
    def _resolve_asset_root(self):
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parent

    def _asset_path(self, *parts):
        return str(self.base_dir.joinpath(*parts))

    def _restore_ui_canvas(self, name, surf):
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

    def _show_starter_card(self, context, run_score=0, reveal_ms=None):
        self.starter_card_context = context
        self.starter_card_run_score = max(0, int(run_score))
        self.starter_card_reveal_ms = reveal_ms
        self.starter_card_visible = reveal_ms is None
        self.play_button_rect = None

    def _hide_starter_card(self):
        self.starter_card_visible = False
        self.starter_card_context = None
        self.starter_card_reveal_ms = None
        self.play_button_rect = None

    def _refresh_starter_card_visibility(self):
        if self.starter_card_visible or self.starter_card_reveal_ms is None:
            return
        if pygame.time.get_ticks() < self.starter_card_reveal_ms:
            return
        self.starter_card_visible = True
        self.starter_card_reveal_ms = None

    def _start_waiting_run(self, start_dir):
        if start_dir == (-self.direction[0], -self.direction[1]):
            return False

        now = pygame.time.get_ticks()
        self._ensure_lazy_animations("mouth", "eyes", "tongue")
        self.show_waiting_start_cue = False
        self.game_state = "playing"
        self.last_tick_ms = now
        self.direction = start_dir
        self.next_dir = self.direction
        self.start_move_locked = True
        self.prev_direction = self.direction
        self.head_angle_deg = self._dir_to_angle(self.direction)
        self.turn_from_deg = self.head_angle_deg
        self.turn_to_deg = self.head_angle_deg
        self.turn_start_ms = now
        self.turn_end_ms = now
        self._cancel_tongue_rattle(now, reschedule=True)
        return True

    def _handle_starter_card_play(self):
        context = self.starter_card_context
        if context == "death":
            self.new_game()
            return
        self._ensure_raw_images("start_box")
        self.show_waiting_start_cue = True
        self._hide_starter_card()

    def _set_window_icon(self):
        try:
            pygame.display.set_icon(
                pygame.image.load(self._asset_path("images", "snake_icon.png"))
            )
        except Exception:
            pass

    def _run_next_deferred_startup_task(self):
        if not self._deferred_startup_tasks:
            return False
        task = self._deferred_startup_tasks.popleft()
        task()
        return True

    def _ensure_audio_ready(self):
        if not self._audio_initialized:
            self._init_audio()

    def _scale_frame_set(self, frames, scale, extra_scale=1.0):
        scaled_frames = []
        for src in frames:
            width = max(1, int(src.get_width() * scale * extra_scale))
            height = max(1, int(src.get_height() * scale * extra_scale))
            if (width, height) == src.get_size():
                scaled_frames.append(src)
            else:
                scaled_frames.append(pygame.transform.smoothscale(src, (width, height)))
        return scaled_frames

    def _refresh_scaled_animation_assets(self, scale, names=None):
        targets = set(self._lazy_animation_loaders if names is None else names)
        if "mouth" in targets:
            self._scaled_mouth_frames = self._scale_frame_set(self.mouth_frames, scale, MOUTH_SCALE)
        if "tongue" in targets:
            self._scaled_tongue_frames = self._scale_frame_set(self.snake_tongue, scale, TONGUE_SCALE)
        if "eyes" in targets:
            self._scaled_eye_frames = self._scale_frame_set(self.eye_frames, scale)
        if "death_face" in targets:
            self._scaled_death_face_frames = self._scale_frame_set(
                self.death_face_frames,
                scale,
                DEATH_FACE_SCALE,
            )
        if "collision_effect" in targets:
            self._scaled_collision_effect_frames = self._scale_frame_set(
                self.collision_effect_frames,
                scale,
                COLLISION_EFFECT_SCALE,
            )

    def _load_lazy_animation(self, name):
        if name not in self._lazy_animation_pending:
            return False
        loader = self._lazy_animation_loaders.get(name)
        if loader is None:
            self._lazy_animation_pending.discard(name)
            return False
        loader()
        self._lazy_animation_pending.discard(name)
        if self._last_scale is not None:
            self._refresh_scaled_animation_assets(self._last_scale, (name,))
        return True

    def _load_next_lazy_animation(self):
        while self._lazy_animation_queue:
            name = self._lazy_animation_queue.popleft()
            if self._load_lazy_animation(name):
                return True
        return False

    def _ensure_lazy_animations(self, *names):
        for name in names:
            self._load_lazy_animation(name)

    def _ensure_raw_images(self, *keys):
        missing = tuple(key for key in keys if key not in self._raw)
        if not missing:
            return
        self._load_raw_images(missing)
        self._last_scale = None

    def _init_audio(self):
        if self._audio_initialized:
            return
        self._audio_initialized = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels(), AUDIO_RESERVED_CHANNELS))
            pygame.mixer.set_reserved(AUDIO_RESERVED_CHANNELS)
            self.turn_channels = [
                pygame.mixer.Channel(i) for i in range(TURN_SFX_STACK_CHANNELS)
            ]
            self.collision_channel = pygame.mixer.Channel(COLLISION_SFX_CHANNEL_INDEX)
        except Exception:
            self.turn_channels = []
            self.collision_channel = None
            return

        self.turn_sound = self._load_sound("audio", "turn_sfx.mp3", volume=TURN_SFX_VOLUME)
        self.collision_sound = self._load_sound(
            "audio",
            "end_audio DEATH.mp3",
            volume=COLLISION_SFX_VOLUME,
        )
        self._apply_audio_mute_state()

    def _load_sound(self, *parts, volume):
        try:
            sound = pygame.mixer.Sound(self._asset_path(*parts))
        except Exception:
            return None
        sound.set_volume(volume)
        return sound

    def _play_turn_sfx(self):
        self._ensure_audio_ready()
        if self.turn_sound is None or not self.turn_channels:
            return
        for channel in self.turn_channels:
            if not channel.get_busy():
                channel.play(self.turn_sound)
                return
        self.turn_channels[self.next_turn_channel_idx].play(self.turn_sound)
        self.next_turn_channel_idx = (self.next_turn_channel_idx + 1) % len(self.turn_channels)

    def _play_collision_sfx(self):
        self._ensure_audio_ready()
        for channel in self.turn_channels:
            channel.stop()
        if self.collision_sound is None or self.collision_channel is None:
            return
        self.collision_channel.play(self.collision_sound)

    def _stop_audio(self):
        for channel in self.turn_channels:
            channel.stop()
        if self.collision_channel is not None:
            self.collision_channel.stop()

    def _apply_audio_mute_state(self):
        turn_volume = 0.0 if self.audio_muted else TURN_SFX_VOLUME
        collision_volume = 0.0 if self.audio_muted else COLLISION_SFX_VOLUME
        if self.turn_sound is not None:
            self.turn_sound.set_volume(turn_volume)
        if self.collision_sound is not None:
            self.collision_sound.set_volume(collision_volume)

    def _toggle_audio_mute(self):
        self.audio_muted = not self.audio_muted
        if self.audio_muted:
            self._ensure_raw_images("volume_muted")
        if self._audio_initialized:
            self._apply_audio_mute_state()
        if self.audio_muted and self._audio_initialized:
            self._stop_audio()

    def _get_scale(self):
        ww, wh = self.window.get_size()
        return min(ww / BASE_W, wh / BASE_H)

    def _ensure_assets(self):
        scale  = self._get_scale()
        ww, wh = self.window.get_size()
        size_changed  = (ww, wh) != self._last_win_size
        scale_changed = scale != self._last_scale
        if not scale_changed and not size_changed:
            return
        if size_changed:
            self._last_win_size = (ww, wh)
        if scale_changed:
            self._last_scale = scale
            full_screen_raw = self._raw['full_screen']
            not_full_screen_raw = self._raw.get('not_full_screen', full_screen_raw)
            volume_raw = self._raw['volume']
            volume_muted_raw = self._raw.get('volume_muted', volume_raw)
            full_screen_icon_bounds = self._crop_alpha_bounds(full_screen_raw)
            volume_icon_max_w = 40
            volume_icon_max_h = 21
            if full_screen_icon_bounds is not None:
                volume_icon_max_h = full_screen_icon_bounds.get_height() + 2
            def sc(img, base_w, base_h=None):
                if base_h is None: base_h = base_w
                size = (max(1, int(base_w * scale)), max(1, int(base_h * scale)))
                if size == img.get_size():
                    return img
                return pygame.transform.smoothscale(img, size)
            def sc_fit_width(img, base_w):
                target_w = max(1, int(base_w * scale))
                target_h = max(1, int(img.get_height() * target_w / img.get_width()))
                size = (target_w, target_h)
                if size == img.get_size():
                    return img
                return pygame.transform.smoothscale(img, size)
            def sc_fit(img, max_w, max_h=None):
                if max_h is None:
                    max_h = max_w
                iw, ih = img.get_size()
                fit_scale = min(max_w * scale / iw, max_h * scale / ih)
                size = (max(1, int(iw * fit_scale)), max(1, int(ih * fit_scale)))
                if size == img.get_size():
                    return img
                return pygame.transform.smoothscale(img, size)
            self._scaled_assets = {
                'tile_light':  sc(self._raw['tile_light'],  TILE_SIZE_BASE),
                'tile_dark':   sc(self._raw['tile_dark'],   TILE_SIZE_BASE),
                'trophy':      sc(self._raw['trophy'],      44),
                'apple_icon':  sc(self._raw['apple_icon'],  44),
                'apple_board': sc(self._raw['apple_icon'],  TILE_SIZE_BASE),
                'snake_card':  sc_fit_width(self._raw['snake_card'], STARTER_CARD_BASE_W),
                'play_button': sc_fit_width(self._raw['play_button'], STARTER_CARD_BASE_W),
                'x':           sc_fit(self._raw['x'],           40, 40),
                'full_screen': sc_fit(full_screen_raw, 40, 40),
                'not_full_screen': sc_fit(not_full_screen_raw, 40, 40),
                'volume':      sc_fit(volume_raw, volume_icon_max_w, volume_icon_max_h),
                'volume_muted': sc_fit(volume_muted_raw, volume_icon_max_w, volume_icon_max_h),
            }
            start_box_raw = self._raw.get('start_box')
            if start_box_raw is not None:
                self._scaled_assets['start_box'] = sc_fit_width(start_box_raw, WAITING_CUE_ICON_BASE_W)
            self._refresh_scaled_animation_assets(scale)
            self._rebuild_fonts(scale)

    def _rebuild_fonts(self, scale):
        self.font_large  = pygame.font.SysFont("Arial", max(8, int(52 * scale)), bold=True)
        self.font_medium = pygame.font.SysFont("Arial", max(8, int(30 * scale)), bold=True)
        self.font_small  = pygame.font.SysFont("Arial", max(8, int(26 * scale)))
        self.font_score  = pygame.font.SysFont("Arial", max(8, int(34 * scale)), bold=True)

    def _layout(self):
        sc        = self._get_scale()
        header_h  = int(HEADER_H_BASE * sc)
        tile_size = int(TILE_SIZE_BASE * sc)
        board_w   = tile_size * GRID_COLS
        board_h   = tile_size * GRID_ROWS
        ww, wh    = self.window.get_size()
        play_h    = wh - header_h
        board_ox  = (ww - board_w) // 2
        board_oy  = header_h + (play_h - board_h) // 2
        return {
            'sc': sc, 'header_h': header_h,
            'tile_size': tile_size, 'board_w': board_w, 'board_h': board_h,
            'board_ox': board_ox, 'board_oy': board_oy,
            'win_w': ww, 'win_h': wh,
            'body_r': max(1, (tile_size - 2 * int(4 * sc)) // 2),
        }

    def _grid_to_pixel(self, gx, gy, lay):
        return (lay['board_ox'] + gx * lay['tile_size'],
                lay['board_oy'] + gy * lay['tile_size'])

    def _cell_center(self, gx, gy, lay):
        px, py = self._grid_to_pixel(gx, gy, lay)
        return (px + lay['tile_size'] / 2, py + lay['tile_size'] / 2)

    def _apple_center_screen(self, lay):
        if self.apple is None:
            return None
        ax, ay = self.apple
        return self._cell_center(ax, ay, lay)

    def _dir_to_angle(self, d):
        if d == RIGHT: return 0.0
        if d == DOWN:  return 90.0
        if d == LEFT:  return 180.0
        return -90.0

    def _sample_polyline_at_distance(self, pts, cum, d):
        if not pts:
            return (0.0, 0.0)
        total = cum[-1]
        if total <= 0.0:
            return pts[-1]
        d = max(0.0, min(total, d))
        for i in range(len(cum) - 1):
            c0 = cum[i]
            c1 = cum[i + 1]
            if d <= c1:
                seg_len = c1 - c0
                if seg_len <= 1e-6:
                    return pts[i + 1]
                t = (d - c0) / seg_len
                p0 = pts[i]
                p1 = pts[i + 1]
                return lerp_pt(p0, p1, t)
        return pts[-1]

    def _segment_index_at_arc_distance(self, cum, arc_dist):
        if len(cum) < 2:
            return 0
        d = max(0.0, min(cum[-1], arc_dist))
        for i in range(len(cum) - 1):
            if d <= cum[i + 1]:
                return i
        return len(cum) - 2

    def _bulge_decay_segments_for_length(self):
        return float(max(4, min(BULGE_FADE_SEGMENTS_CAP, len(self.snake))))

    def _spawn_bulge(self):
        decay_segments = self._bulge_decay_segments_for_length()
        self.bulges.append({
            'dist_px': 0.0,
            'start_scale': BULGE_START_SCALE,
            'end_scale': BULGE_MIN_END_SCALE,
            'decay_segments': decay_segments,
            'delay_frames': BULGE_SPAWN_DELAY_FRAMES,
            'released': False,
            'hold_head_until_tick': False,
        })

    def _bulge_headspace_speed_px(self, tile_size):
        return (1.0 + BULGE_TRAVEL_SEG_PER_TICK) * tile_size

    def _radius_for_segment_from_head(self, seg_from_head, base_r):
        # Keep the spawn-length body uniform; only extra grown length tapers.
        min_r = max(1, int(base_r * TAIL_MIN_RADIUS_FACTOR))
        taper_seg_from_head = max(0.0, float(seg_from_head) - float(START_SNAKE_SEGMENTS - 1))
        rr = float(base_r) - taper_seg_from_head * SEGMENT_SHRINK_PER_SEG
        return max(min_r, int(rr))

    def _angle_vec(self, angle_deg):
        rad = math.radians(angle_deg)
        return (math.cos(rad), math.sin(rad))

    def _head_body_angle(self, head_c, neck_c, fallback_angle):
        if head_c is None or neck_c is None:
            return fallback_angle

        vx = head_c[0] - neck_c[0]
        vy = head_c[1] - neck_c[1]
        if math.hypot(vx, vy) <= 1e-6:
            return fallback_angle

        return math.degrees(math.atan2(vy, vx))

    def _segment_after_head_angle(self, segments, fallback_angle):
        if len(segments) >= 3:
            return self._head_body_angle(segments[1], segments[2], fallback_angle)
        if len(segments) >= 2:
            return self._head_body_angle(segments[0], segments[1], fallback_angle)
        return fallback_angle

    def _face_angle_from_head_path(self, pts, lay, fallback_angle):
        if len(pts) < 2:
            return fallback_angle

        head_x, head_y = pts[-1]
        for i in range(len(pts) - 2, -1, -1):
            prev_x, prev_y = pts[i]
            vx = head_x - prev_x
            vy = head_y - prev_y
            if math.hypot(vx, vy) <= 1e-6:
                continue

            # Snap the face to the dominant axis of the nearest visible head
            # segment so this feature keeps clean 90-degree rotations.
            if abs(vx) >= abs(vy):
                return self._dir_to_angle(RIGHT if vx >= 0.0 else LEFT)
            return self._dir_to_angle(DOWN if vy >= 0.0 else UP)

        return fallback_angle

    def _face_pair_center(self, head_c, face_angle, lay):
        dx, dy = self._angle_vec(face_angle)
        perp_x, perp_y = -dy, dx
        ts = lay['tile_size']
        pair_fwd = ts * EYE_CENTER_FWD
        pair_side = ts * EYE_CENTER_SIDE
        return (
            head_c[0] + dx * pair_fwd + perp_x * pair_side,
            head_c[1] + dy * pair_fwd + perp_y * pair_side,
        )

    def _current_head_angle(self, now_ms):
        if now_ms >= self.turn_end_ms:
            self.head_angle_deg = self.turn_to_deg
            return self.head_angle_deg
        if now_ms <= self.turn_start_ms:
            return self.turn_from_deg
        dur = max(1, self.turn_end_ms - self.turn_start_ms)
        t = max(0.0, min(1.0, (now_ms - self.turn_start_ms) / dur))
        self.head_angle_deg = angle_lerp_shortest(self.turn_from_deg, self.turn_to_deg, t)
        return self.head_angle_deg

    def _start_head_turn(self, new_dir, now_ms):
        self.turn_from_deg = self._current_head_angle(now_ms)
        self.turn_to_deg   = self._dir_to_angle(new_dir)
        self.turn_start_ms = now_ms
        boundary_ms = self.last_tick_ms + TICK_RATE
        self.turn_end_ms = boundary_ms if now_ms < boundary_ms else now_ms + TICK_RATE

    def _offset_point(self, pt, offset_xy):
        return (pt[0] + offset_xy[0], pt[1] + offset_xy[1])

    def _build_pose_points(self, lay, segments, *, offset_tiles_xy=(0.0, 0.0)):
        if len(segments) < 2:
            return []
        off_px = (
            offset_tiles_xy[0] * lay['tile_size'],
            offset_tiles_xy[1] * lay['tile_size'],
        )
        pts = []
        for i in range(len(segments) - 1, -1, -1):
            gx, gy = segments[i]
            pts.append(self._offset_point(self._cell_center(gx, gy, lay), off_px))
        return pts

    def _build_transition_points(self, lay, segments, *, prev_head, prev_tail, progress):
        if len(segments) < 2:
            return [], None

        progress = max(0.0, min(1.0, progress))
        cc = lambda gx, gy: self._cell_center(gx, gy, lay)
        ghost_tip = lerp_pt(cc(prev_tail[0], prev_tail[1]), cc(segments[-1][0], segments[-1][1]), progress)
        head_c = lerp_pt(cc(prev_head[0], prev_head[1]), cc(segments[0][0], segments[0][1]), progress)

        pts = [ghost_tip]
        for i in range(len(segments) - 1, 0, -1):
            gx, gy = segments[i]
            pts.append(cc(gx, gy))
        pts.append(head_c)
        return pts, head_c

    def _timed_animation_frame_idx(self, now_ms, *, start_ms, play_ms, frame_count, freeze_final):
        if start_ms is None or frame_count <= 0:
            return None
        if frame_count == 1:
            if not freeze_final and now_ms >= start_ms + max(0, play_ms):
                return None
            return 0
        if play_ms <= 0:
            return frame_count - 1 if freeze_final else None

        elapsed = max(0, now_ms - start_ms)
        if elapsed >= play_ms:
            return frame_count - 1 if freeze_final else None

        frame_ms = play_ms / frame_count
        return min(frame_count - 1, int(elapsed / frame_ms))

    def _build_collision_effect_state(self, now_ms, direction, anchor_px):
        extra_rot_deg = COLLISION_EFFECT_EXTRA_ROT_DEG if direction in (UP, DOWN) else 0.0
        return {
            'start_ms': now_ms,
            'direction': direction,
            'angle_deg': self._dir_to_angle(direction) + extra_rot_deg,
            'anchor_px': anchor_px,
        }

    def _collision_effect_anchor_px(self, effect, head_c, lay):
        if 'anchor_px' in effect:
            return effect['anchor_px']
        if head_c is None:
            return (None, None)
        dx, dy = effect['direction']
        return (
            head_c[0] + dx * lay['tile_size'] * COLLISION_EFFECT_ANCHOR_FWD,
            head_c[1] + dy * lay['tile_size'] * COLLISION_EFFECT_ANCHOR_FWD,
        )

    def _collision_impact_head(self, kind, attempted_head):
        if kind != "border":
            return attempted_head

        dx, dy = self.direction
        return (
            attempted_head[0] - dx * BORDER_CONTACT_INSET_TILES,
            attempted_head[1] - dy * BORDER_CONTACT_INSET_TILES,
        )

    def _reset_recoil_path_history(self):
        self.recoil_path_history = deque(reversed(self.snake))
        self._trim_recoil_path_history()

    def _trim_recoil_path_history(self):
        keep_cells = max(2, len(self.snake) + COLLISION_PATH_EXTRA_CELLS)
        while len(self.recoil_path_history) > keep_cells:
            self.recoil_path_history.popleft()

    def _snapshot_recoil_path(self):
        retrace_path = list(self.snake)
        history_path = list(reversed(self.recoil_path_history))
        retrace_path.extend(history_path[len(self.snake):])
        return retrace_path

    def _record_recoil_path_head(self, new_head):
        self.recoil_path_history.append(new_head)
        self._trim_recoil_path_history()

    def _build_recoil_points(
        self,
        lay,
        impact_head_grid,
        retrace_path_grid,
        visible_length,
        progress,
        *,
        tail_trim_px=0.0,
    ):
        progress = max(0.0, min(1.0, progress))
        if not retrace_path_grid:
            return [], None, self._dir_to_angle(self.direction)
        visible_length = max(1, min(visible_length, len(retrace_path_grid)))

        impact_head_px = self._cell_center(impact_head_grid[0], impact_head_grid[1], lay)
        live_head_px = self._cell_center(retrace_path_grid[0][0], retrace_path_grid[0][1], lay)
        contact_dist_px = math.hypot(
            live_head_px[0] - impact_head_px[0],
            live_head_px[1] - impact_head_px[1],
        )
        tail_extension_tiles = COLLISION_BACKUP_TILES + (contact_dist_px / lay['tile_size'])

        path_grid = [impact_head_grid] + list(retrace_path_grid)
        if len(retrace_path_grid) >= 2:
            tail_x, tail_y = retrace_path_grid[-1]
            prev_x, prev_y = retrace_path_grid[-2]
            tail_step = (tail_x - prev_x, tail_y - prev_y)
            tail_extension = (
                tail_x + tail_step[0] * tail_extension_tiles,
                tail_y + tail_step[1] * tail_extension_tiles,
            )
        else:
            tail_extension = retrace_path_grid[-1]
        path_grid.append(tail_extension)
        path_px = [self._cell_center(gx, gy, lay) for gx, gy in path_grid]

        cum = [0.0]
        for i in range(1, len(path_px)):
            cum.append(cum[-1] + math.hypot(
                path_px[i][0] - path_px[i - 1][0],
                path_px[i][1] - path_px[i - 1][1],
            ))

        # The recoil can retrace farther than the currently visible body, but
        # the rendered snake length should still match the live snake length.
        visible_tail_idx = min(len(cum) - 2, visible_length)
        max_tail_trim_px = max(0.0, cum[visible_tail_idx] - 1.0)
        body_len = max(
            0.0,
            cum[visible_tail_idx] - min(max_tail_trim_px, max(0.0, tail_trim_px)),
        )
        max_head_dist = contact_dist_px + (lay['tile_size'] * COLLISION_BACKUP_TILES)
        head_dist = (1.0 - progress) * max_head_dist
        tail_dist = min(cum[-1], head_dist + body_len)

        head_c = self._sample_polyline_at_distance(path_px, cum, head_dist)
        ghost_tip = self._sample_polyline_at_distance(path_px, cum, tail_dist)

        pts = [ghost_tip]
        for i in range(len(path_px) - 1, -1, -1):
            if head_dist < cum[i] < tail_dist:
                pts.append(path_px[i])
        pts.append(head_c)

        seg_idx = self._segment_index_at_arc_distance(cum, head_dist)
        p0 = path_px[seg_idx]
        p1 = path_px[seg_idx + 1]
        head_angle = math.degrees(math.atan2(p0[1] - p1[1], p0[0] - p1[0]))
        return pts, head_c, head_angle

    def _build_frozen_collision_pose(self):
        recoil = self.collision_recoil
        if not recoil:
            return None

        return {
            'impact_head': recoil['impact_head'],
            'face_angle': recoil['face_angle'],
            'recoil_face_from_angle': recoil.get('recoil_face_from_angle'),
            'recoil_face_to_angle': recoil.get('recoil_face_to_angle'),
            'impact_face_angle': recoil['impact_face_angle'],
            'twitch_face_angle': recoil['twitch_face_angle'],
            'retrace_path_grid': list(recoil['retrace_path_grid']),
            'visible_length': recoil['visible_length'],
            'progress': 0.0,
        }

    def _build_death_pose_points(self, lay):
        pose = self.death_pose
        if not pose:
            return [], None

        if {'segments', 'prev_head', 'prev_tail', 'progress'} <= pose.keys():
            return self._build_transition_points(
                lay,
                pose['segments'],
                prev_head=pose['prev_head'],
                prev_tail=pose['prev_tail'],
                progress=pose['progress'],
            )

        pts = self._build_pose_points(
            lay,
            pose['segments'],
            offset_tiles_xy=pose.get('offset_tiles', (0.0, 0.0)),
        )
        head_c = pts[-1] if pts else None
        return pts, head_c

    def _collision_retrace_progress(self, now_ms):
        if not self.collision_recoil:
            return 0.0

        recoil = self.collision_recoil
        if now_ms <= recoil['hold_until_ms']:
            return 1.0

        dur = max(1, recoil['retrace_end_ms'] - recoil['hold_until_ms'])
        t = max(0.0, min(1.0, (now_ms - recoil['hold_until_ms']) / dur))
        return 1.0 - ease_out_quad(t)

    def _collision_tail_trim_px(self, now_ms, lay):
        recoil = self.collision_recoil
        if not recoil:
            return 0.0

        max_trim_px = lay['tile_size'] * COLLISION_TAIL_INSET_TILES
        if now_ms <= recoil['hold_until_ms']:
            intro_dur = max(1, recoil['hold_until_ms'] - recoil['start_ms'])
            t = max(0.0, min(1.0, (now_ms - recoil['start_ms']) / intro_dur))
            return max_trim_px * smoothstep(t)

        if now_ms >= recoil['retrace_end_ms']:
            return 0.0

        recoil_dur = max(1, recoil['retrace_end_ms'] - recoil['hold_until_ms'])
        t = max(0.0, min(1.0, (now_ms - recoil['hold_until_ms']) / recoil_dur))
        return max_trim_px * (1.0 - smoothstep(t))

    def _collision_effect_frame_idx(self, now_ms):
        effect = self.collision_effect
        if not effect or not self._scaled_collision_effect_frames:
            return None

        total_visible_ms = (
            DEATH_FACE_COLLISION_INTRO_MS +
            DEATH_FACE_RECOIL_MS +
            DEATH_SCREEN_DELAY_MS
        )
        elapsed = max(0, now_ms - effect['start_ms'])
        if elapsed >= total_visible_ms:
            return None

        frame_count = len(self._scaled_collision_effect_frames)
        if frame_count <= 0:
            return None

        speed_mult = max(0.01, COLLISION_EFFECT_SPEED_MULT)
        play_ms = max(1, int(round(total_visible_ms / speed_mult)))
        return self._timed_animation_frame_idx(
            now_ms,
            start_ms=effect['start_ms'],
            play_ms=play_ms,
            frame_count=frame_count,
            freeze_final=False,
        )

    def _draw_collision_effect(self, now_ms, head_c, lay):
        frame_idx = self._collision_effect_frame_idx(now_ms)
        if frame_idx is None:
            return

        effect = self.collision_effect
        if effect is None:
            return
        assert effect is not None

        sprite = self._scaled_collision_effect_frames[frame_idx]
        rot_deg = effect['angle_deg'] if 'angle_deg' in effect else 0.0
        if abs(rot_deg) > 0.01:
            sprite = pygame.transform.rotate(sprite, rot_deg)

        anchor_x, anchor_y = self._collision_effect_anchor_px(effect, head_c, lay)
        if anchor_x is None or anchor_y is None:
            return
        rect = sprite.get_rect(center=(int(anchor_x), int(anchor_y)))
        self.window.blit(sprite, rect.topleft)

    def _death_face_frame_idx(self, now_ms):
        effect = self.death_face_anim
        if not effect or not self._scaled_death_face_frames:
            return None

        frame_count = len(self._scaled_death_face_frames)
        if frame_count <= 0:
            return None
        if frame_count == 1:
            return 0

        recoil_start = max(1, min(DEATH_FACE_RECOIL_START_FRAME, frame_count - 1))
        twitch_start = max(recoil_start + 1, min(DEATH_FACE_TWITCH_START_FRAME, frame_count - 1))
        hold_end_ms = effect.get('hold_end_ms', effect['start_ms'])
        retrace_end_ms = effect.get('retrace_end_ms', hold_end_ms)

        if now_ms < hold_end_ms:
            return self._phase_frame_idx(
                0,
                recoil_start,
                now_ms - effect['start_ms'],
                hold_end_ms - effect['start_ms'],
            )

        if now_ms < retrace_end_ms:
            return self._phase_frame_idx(
                recoil_start,
                twitch_start,
                now_ms - hold_end_ms,
                retrace_end_ms - hold_end_ms,
            )

        loop_count = frame_count - twitch_start
        if loop_count <= 0:
            return frame_count - 1

        loop_frame_ms = max(1, DEATH_FACE_TWITCH_FRAME_MS)
        loop_elapsed = max(0, now_ms - retrace_end_ms)
        return twitch_start + (int(loop_elapsed // loop_frame_ms) % loop_count)

    def _phase_frame_idx(self, start_frame, end_frame, elapsed_ms, duration_ms):
        if end_frame <= start_frame:
            return start_frame

        span = end_frame - start_frame
        if duration_ms <= 0:
            return end_frame - 1

        t = max(0.0, min(0.999999, elapsed_ms / duration_ms))
        return start_frame + min(span - 1, int(t * span))

    def _death_face_angle_for_frame(
        self,
        frame_idx,
        progress,
        face_angle,
        recoil_face_from_angle,
        recoil_face_to_angle,
        impact_face_angle,
        twitch_face_angle,
    ):
        if face_angle is not None:
            return face_angle
        if recoil_face_from_angle is not None and recoil_face_to_angle is not None:
            return angle_lerp_shortest(recoil_face_from_angle, recoil_face_to_angle, progress)
        if twitch_face_angle is not None:
            return twitch_face_angle
        if impact_face_angle is not None:
            return impact_face_angle
        return 0.0

    def _draw_death_face(
        self,
        head_c,
        progress,
        face_angle,
        recoil_face_from_angle,
        recoil_face_to_angle,
        impact_face_angle,
        twitch_face_angle,
        lay,
        now_ms,
    ):
        frame_idx = self._death_face_frame_idx(now_ms)
        if frame_idx is None:
            return

        head_angle = self._death_face_angle_for_frame(
            frame_idx,
            progress,
            face_angle,
            recoil_face_from_angle,
            recoil_face_to_angle,
            impact_face_angle,
            twitch_face_angle,
        )
        sprite = self._scaled_death_face_frames[frame_idx]
        dx, dy = self._angle_vec(head_angle)
        ts = lay['tile_size']
        blend_frames = max(1, DEATH_FACE_TWITCH_BLEND_FRAMES)
        blend_start = max(0, DEATH_FACE_TWITCH_START_FRAME - blend_frames)
        if frame_idx <= blend_start:
            blend_t = 0.0
        elif frame_idx >= DEATH_FACE_TWITCH_START_FRAME:
            blend_t = 1.0
        else:
            blend_t = (frame_idx - blend_start) / max(1, DEATH_FACE_TWITCH_START_FRAME - blend_start)
        blend_t = blend_t * blend_t * (3.0 - 2.0 * blend_t)
        anchor_fwd = (
            DEATH_FACE_PRE_TWITCH_ANCHOR
            + (DEATH_FACE_TWITCH_ANCHOR - DEATH_FACE_PRE_TWITCH_ANCHOR) * blend_t
        )
        growth_span = max(1, DEATH_FACE_TWITCH_START_FRAME - DEATH_FACE_RECOIL_START_FRAME)
        growth_t = (frame_idx - DEATH_FACE_RECOIL_START_FRAME) / growth_span
        growth_t = max(0.0, min(1.0, growth_t))
        growth_t = growth_t * growth_t * (3.0 - 2.0 * growth_t)
        vertical_lift = (
            ts * DEATH_FACE_FRAME_LIFT * growth_t
            if abs(dy) > abs(dx) and dy < 0.0
            else 0.0
        )
        face_target = (
            head_c[0] + dx * ts * anchor_fwd,
            head_c[1] + dy * ts * anchor_fwd + vertical_lift,
        )
        angle = -head_angle
        rot = sprite if abs(angle) < 0.01 else pygame.transform.rotate(sprite, angle)
        rect = rot.get_rect(center=(int(round(face_target[0])), int(round(face_target[1]))))
        self.window.blit(rot, rect.topleft)

    def _begin_collision_recoil(self, kind, impact_head):
        now_ms = pygame.time.get_ticks()
        impact_head = self._collision_impact_head(kind, impact_head)
        face_angle = self._current_head_angle(now_ms)
        hold_until_ms = now_ms + DEATH_FACE_COLLISION_INTRO_MS
        retrace_end_ms = hold_until_ms + DEATH_FACE_RECOIL_MS
        self._ensure_lazy_animations("death_face", "collision_effect")

        self._play_collision_sfx()
        self.game_state = "colliding"
        self.high_score = max(self.high_score, self.score)
        self.input_queue.clear()
        self.next_dir = self.direction
        retrace_path = self._snapshot_recoil_path()
        self.collision_recoil = {
            'kind': kind,
            'start_ms': now_ms,
            'direction': self.direction,
            'impact_head': impact_head,
            'face_angle': face_angle,
            'recoil_face_from_angle': self.turn_from_deg,
            'recoil_face_to_angle': face_angle,
            'impact_face_angle': self._dir_to_angle(self.direction),
            'twitch_face_angle': self._segment_after_head_angle(
                self.snake,
                self._dir_to_angle(self.direction),
            ),
            'retrace_path_grid': retrace_path,
            'visible_length': len(self.snake),
            'hold_until_ms': hold_until_ms,
            'retrace_end_ms': retrace_end_ms,
            'overlay_reveal_ms': now_ms + DEATH_OVERLAY_REVEAL_MS,
        }
        lay = self._layout()
        dx, dy = self.direction
        impact_head_c = self._cell_center(impact_head[0], impact_head[1], lay)
        impact_anchor_px = (
            impact_head_c[0] + dx * lay['tile_size'] * COLLISION_EFFECT_ANCHOR_FWD,
            impact_head_c[1] + dy * lay['tile_size'] * COLLISION_EFFECT_ANCHOR_FWD,
        )
        self.collision_effect = self._build_collision_effect_state(now_ms, self.direction, impact_anchor_px)
        self.death_face_anim = {
            'start_ms': now_ms,
            'hold_end_ms': hold_until_ms,
            'retrace_end_ms': retrace_end_ms,
        }

    def _update_collision_recoil(self):
        if self.game_state != "colliding" or not self.collision_recoil:
            return

        now_ms = pygame.time.get_ticks()
        recoil = self.collision_recoil
        if now_ms < recoil['retrace_end_ms']:
            return

        self.death_pose = self._build_frozen_collision_pose()
        self.death_overlay_delay_until_ms = recoil['overlay_reveal_ms']
        self.collision_recoil = None
        self.game_state = "dead"
        self.show_waiting_start_cue = False
        self._show_starter_card("death", run_score=self.score, reveal_ms=self.death_overlay_delay_until_ms)

    # ── Setup ─────────────────────────────────────────────────────────────────
    def _load_raw_image(self, key):
        if key == "tile_light":
            return pygame.image.load(self._asset_path("images", "light_green.png")).convert()
        if key == "tile_dark":
            return pygame.image.load(self._asset_path("images", "dark_green.png")).convert()
        if key == "snake_card":
            return pygame.image.load(self._asset_path("images", "Snake_card.png")).convert_alpha()
        if key == "play_button":
            return pygame.image.load(self._asset_path("images", "play_button.png")).convert_alpha()
        if key == "trophy":
            return self._restore_ui_canvas(
                "trophy",
                pygame.image.load(self._asset_path("images", "trophy.png")).convert_alpha(),
            )
        if key == "apple_icon":
            return self._restore_ui_canvas(
                "apple_icon",
                pygame.image.load(self._asset_path("images", "apple_icon.png")).convert_alpha(),
            )
        if key == "x":
            return self._restore_ui_canvas(
                "x",
                pygame.image.load(self._asset_path("images", "x.png")).convert_alpha(),
            )
        if key == "full_screen":
            return self._restore_ui_canvas(
                "full_screen",
                pygame.image.load(self._asset_path("images", "full_screen.png")).convert_alpha(),
            )
        if key == "not_full_screen":
            return self._restore_ui_canvas(
                "not_full_screen",
                pygame.image.load(self._asset_path("images", "not_full_screen.png")).convert_alpha(),
            )
        if key == "start_box":
            start_box_image = self._restore_ui_canvas(
                "start_box",
                pygame.image.load(self._asset_path("images", "start_box.png")).convert_alpha(),
            )
            start_box = self._crop_alpha_bounds(start_box_image)
            return start_box if start_box is not None else start_box_image
        if key == "volume":
            volume_icon = pygame.image.load(self._asset_path("images", "volume.png")).convert_alpha()
            cropped_volume_icon = self._crop_alpha_bounds(volume_icon)
            return cropped_volume_icon if cropped_volume_icon is not None else volume_icon
        if key == "volume_muted":
            muted_icon = pygame.image.load(self._asset_path("images", "muted.png")).convert_alpha()
            cropped_muted_icon = self._crop_alpha_bounds(muted_icon)
            return cropped_muted_icon if cropped_muted_icon is not None else muted_icon
        raise KeyError(key)

    def _load_raw_images(self, keys=None):
        if keys is None:
            keys = (
                "tile_light",
                "tile_dark",
                "trophy",
                "apple_icon",
                "snake_card",
                "play_button",
                "start_box",
                "x",
                "full_screen",
                "not_full_screen",
                "volume",
                "volume_muted",
            )
        for key in keys:
            if key in self._raw:
                continue
            self._raw[key] = self._load_raw_image(key)

    def _crop_alpha_bounds(self, surf):
        bounds = surf.get_bounding_rect(min_alpha=1)
        if bounds.width <= 0 or bounds.height <= 0:
            return None
        return surf.subsurface(bounds).copy()

    def _death_face_mouth_anchor(self, surf):
        w, h = surf.get_size()
        y_start = max(0, min(h - 1, int(h * 0.45)))
        min_x, min_y = w, h
        max_x, max_y = -1, -1

        for y in range(y_start, h):
            for x in range(w):
                if surf.get_at((x, y)).a <= 0:
                    continue
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        if max_x < min_x or max_y < min_y:
            return (w / 2.0, h / 2.0)

        return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)

    def _slice_tongue_strip(self, strip):
        frame_w = 49
        frame_h = strip.get_height()
        frame_count = math.ceil(strip.get_width() / frame_w)
        frames = []

        for i in range(frame_count):
            x0 = i * frame_w
            fw = min(frame_w, strip.get_width() - x0)
            if fw <= 0:
                continue
            frame = pygame.Surface((fw, frame_h), pygame.SRCALPHA)
            frame.blit(strip, (0, 0), pygame.Rect(x0, 0, fw, frame_h))
            cropped = self._crop_alpha_bounds(frame)
            if cropped is not None:
                frames.append(cropped)
        return frames

    def _load_tongue_frames(self):
        self.snake_tongue = []
        try:
            strip = pygame.image.load(self._asset_path("sprites", "tongue_sprites.png")).convert_alpha()
            self.snake_tongue = self._slice_tongue_strip(strip)
        except Exception:
            self.snake_tongue = []

    def _slice_fixed_strip(self, strip, frame_count, frame_w, separator_w=0, *, crop=True):
        w, h = strip.get_size()
        frames = []
        expected_w = frame_count * frame_w + separator_w * (frame_count - 1)

        if frame_count <= 0 or frame_w <= 0:
            return frames

        if expected_w != w:
            for i in range(frame_count):
                x0 = int(round(i * w / frame_count))
                x1 = int(round((i + 1) * w / frame_count))
                fw = max(1, x1 - x0)
                frame = pygame.Surface((fw, h), pygame.SRCALPHA)
                frame.blit(strip, (0, 0), pygame.Rect(x0, 0, fw, h))
                if crop:
                    cropped = self._crop_alpha_bounds(frame)
                    if cropped is not None:
                        frames.append(cropped)
                else:
                    frames.append(frame)
            return frames

        for i in range(frame_count):
            x0 = i * (frame_w + separator_w)
            frame = pygame.Surface((frame_w, h), pygame.SRCALPHA)
            frame.blit(strip, (0, 0), pygame.Rect(x0, 0, frame_w, h))
            if crop:
                cropped = self._crop_alpha_bounds(frame)
                if cropped is not None:
                    frames.append(cropped)
            else:
                frames.append(frame)
        return frames

    def _slice_mouth_strip(self, strip):
        frames = []
        w, h = strip.get_size()
        run_start = None
        for x in range(w):
            has_alpha = False
            for y in range(h):
                if strip.get_at((x, y)).a > 0:
                    has_alpha = True
                    break
            if has_alpha and run_start is None:
                run_start = x
            elif not has_alpha and run_start is not None:
                frame = pygame.Surface((x - run_start, h), pygame.SRCALPHA)
                frame.blit(strip, (0, 0), pygame.Rect(run_start, 0, x - run_start, h))
                cropped = self._crop_alpha_bounds(frame)
                if cropped is not None:
                    frames.append(cropped)
                run_start = None
        if run_start is not None:
            frame = pygame.Surface((w - run_start, h), pygame.SRCALPHA)
            frame.blit(strip, (0, 0), pygame.Rect(run_start, 0, w - run_start, h))
            cropped = self._crop_alpha_bounds(frame)
            if cropped is not None:
                frames.append(cropped)
        return frames

    def _compute_frame_open_amounts(self, frames):
        if not frames:
            return []

        alpha_counts = []
        for frame in frames:
            w, h = frame.get_size()
            alpha_count = 0
            for y in range(h):
                for x in range(w):
                    if frame.get_at((x, y)).a > 0:
                        alpha_count += 1
            alpha_counts.append(alpha_count)

        max_alpha = max(alpha_counts, default=0)
        if max_alpha <= 0:
            return [0.0 for _ in alpha_counts]
        return [count / max_alpha for count in alpha_counts]

    def _load_mouth_frames(self):
        self.mouth_frames = []
        self.mouth_frame_open_amounts = []
        self.mouth_peak_frame_idx = 0
        try:
            strip = pygame.image.load(self._asset_path("sprites", "mouth_sprite.png")).convert_alpha()
            self.mouth_frames = self._slice_mouth_strip(strip)
            self.mouth_frame_open_amounts = self._compute_frame_open_amounts(self.mouth_frames)
            if self.mouth_frame_open_amounts:
                self.mouth_peak_frame_idx = max(
                    range(len(self.mouth_frame_open_amounts)),
                    key=lambda i: self.mouth_frame_open_amounts[i],
                )
        except Exception:
            self.mouth_frames = []
            self.mouth_frame_open_amounts = []
            self.mouth_peak_frame_idx = 0

    def _slice_eye_strip(self, strip):
        return self._slice_fixed_strip(
            strip,
            EYE_FRAME_COUNT,
            EYE_FRAME_W,
            EYE_SEPARATOR_W,
            crop=False,
        )

    def _load_eye_frames(self):
        self.eye_frames = []
        try:
            strip = pygame.image.load(self._asset_path("sprites", "eye_sprite.png")).convert_alpha()
            self.eye_frames = self._slice_eye_strip(strip)
        except Exception:
            self.eye_frames = []

    def _slice_death_face_strip(self, strip):
        w, h = strip.get_size()
        frames = []
        frame_count = max(1, DEATH_FACE_FRAME_COUNT)
        separator_w = max(0, DEATH_FACE_SEPARATOR_W)
        frame_w = (w - separator_w * (frame_count - 1)) // frame_count
        expected_w = frame_w * frame_count + separator_w * (frame_count - 1)

        if frame_w <= 0 or expected_w != w:
            for i in range(frame_count):
                x0 = int(round(i * w / frame_count))
                x1 = int(round((i + 1) * w / frame_count))
                fw = max(1, x1 - x0)
                frame = pygame.Surface((fw, h), pygame.SRCALPHA)
                frame.blit(strip, (0, 0), pygame.Rect(x0, 0, fw, h))
                frames.append(frame)
        else:
            for i in range(frame_count):
                x0 = i * (frame_w + separator_w)
                frame = pygame.Surface((frame_w, h), pygame.SRCALPHA)
                frame.blit(strip, (0, 0), pygame.Rect(x0, 0, frame_w, h))
                frames.append(frame)

        anchor_start = min(max(0, DEATH_FACE_TWITCH_START_FRAME), len(frames) - 1) if frames else 0
        anchor_frames = frames[anchor_start:] if frames else []
        if not anchor_frames:
            anchor_frames = frames
        if anchor_frames:
            anchors = [self._death_face_mouth_anchor(frame) for frame in anchor_frames]
            reference_anchor = (
                sum(ax for ax, _ay in anchors) / len(anchors),
                sum(ay for _ax, ay in anchors) / len(anchors),
            )
        else:
            reference_anchor = (31.5, 38.5)

        normalized_frames = []
        for frame in frames:
            anchor_x, anchor_y = self._death_face_mouth_anchor(frame)
            dx = int(round(reference_anchor[0] - anchor_x))
            dy = int(round(reference_anchor[1] - anchor_y))
            normalized = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            normalized.blit(frame, (dx, dy))
            normalized_frames.append(normalized)

        return normalized_frames

    def _load_death_face_frames(self):
        self.death_face_frames = []
        try:
            strip = pygame.image.load(self._asset_path("sprites", "death_sprites.png")).convert_alpha()
            self.death_face_frames = self._slice_death_face_strip(strip)
        except Exception:
            self.death_face_frames = []

    def _slice_collision_effect_strip(self, strip):
        frame_count = max(1, COLLISION_EFFECT_FRAME_COUNT)
        frame_h = strip.get_height()
        frames = []

        for i in range(frame_count):
            x0 = int(round(i * strip.get_width() / frame_count))
            x1 = int(round((i + 1) * strip.get_width() / frame_count))
            fw = max(1, x1 - x0)
            frame = pygame.Surface((fw, frame_h), pygame.SRCALPHA)
            frame.blit(strip, (0, 0), pygame.Rect(x0, 0, fw, frame_h))
            frames.append(frame)
        return frames

    def _load_collision_effect_frames(self):
        self.collision_effect_frames = []
        try:
            strip = pygame.image.load(self._asset_path("sprites", "collision_effects_sprite.png")).convert_alpha()
            self.collision_effect_frames = self._slice_collision_effect_strip(strip)
        except Exception:
            self.collision_effect_frames = []

    def _schedule_next_tongue_rattle(self, now_ms):
        delay_sec = random.triangular(
            TONGUE_RATTLE_MIN_SEC,
            TONGUE_RATTLE_MAX_SEC,
            TONGUE_RATTLE_MODE_SEC,
        )
        self.tongue_next_rattle_ms = now_ms + int(delay_sec * 1000)

    def _cancel_tongue_rattle(self, now_ms, *, reschedule):
        self.tongue_anim_active = False
        self.tongue_anim_phase = 0.0
        self.tongue_anim_dir = 1
        self.tongue_frame_idx = 0
        self.tongue_last_update_ms = now_ms
        if reschedule:
            self._schedule_next_tongue_rattle(now_ms)

    def _schedule_next_eye_blink(self, now_ms):
        delay_sec = random.triangular(
            EYE_BLINK_MIN_SEC,
            EYE_BLINK_MAX_SEC,
            EYE_BLINK_MODE_SEC,
        )
        self.eye_next_blink_ms = now_ms + int(delay_sec * 1000)

    def _cancel_eye_blink(self, now_ms, *, reschedule):
        self.eye_blink_active = False
        self.eye_frame_idx = 0
        self.eye_last_update_ms = now_ms
        if reschedule:
            self._schedule_next_eye_blink(now_ms)

    def _update_eye_blink(self, now_ms):
        if len(self._scaled_eye_frames) <= 1:
            self._cancel_eye_blink(now_ms, reschedule=(self.game_state != "dead"))
            return

        if self.game_state == "dead":
            self._cancel_eye_blink(now_ms, reschedule=False)
            return

        if not self.eye_blink_active:
            if now_ms < self.eye_next_blink_ms:
                return
            self.eye_blink_active = True
            self.eye_frame_idx = 1
            self.eye_last_update_ms = now_ms
            return

        frame_ms = max(1, int(EYE_BLINK_FRAME_SEC * 1000))
        elapsed = now_ms - self.eye_last_update_ms
        if elapsed < frame_ms:
            return

        steps = elapsed // frame_ms
        self.eye_last_update_ms += steps * frame_ms
        last_idx = len(self._scaled_eye_frames) - 1
        next_idx = self.eye_frame_idx + int(steps)
        if next_idx > last_idx:
            self._cancel_eye_blink(now_ms, reschedule=True)
            return
        self.eye_frame_idx = next_idx

    def _tongue_is_allowed(self):
        return (
            self.game_state == "playing"
            and self.mouth_phase <= 0.0
            and not self.mouth_target_open
            and bool(self.snake_tongue)
            and bool(self._scaled_tongue_frames)
        )

    def _update_tongue_anim(self, now_ms):
        if len(self._scaled_tongue_frames) <= 1:
            self._cancel_tongue_rattle(now_ms, reschedule=(self.game_state == "playing"))
            return

        if not self._tongue_is_allowed():
            self._cancel_tongue_rattle(now_ms, reschedule=(self.game_state == "playing"))
            return

        if not self.tongue_anim_active:
            if now_ms < self.tongue_next_rattle_ms:
                return
            self.tongue_anim_active = True
            self.tongue_anim_phase = 0.0
            self.tongue_anim_dir = 1
            self.tongue_frame_idx = 1
            self.tongue_last_update_ms = now_ms
            return

        frame_ms = max(1, int(TONGUE_FRAME_SEC * 1000))
        elapsed = now_ms - self.tongue_last_update_ms
        if elapsed < frame_ms:
            return

        steps = elapsed // frame_ms
        self.tongue_last_update_ms += steps * frame_ms
        last_idx = len(self._scaled_tongue_frames) - 1

        for _ in range(int(steps)):
            self.tongue_anim_phase += self.tongue_anim_dir
            next_idx = self.tongue_frame_idx + self.tongue_anim_dir
            if next_idx >= last_idx:
                self.tongue_frame_idx = last_idx
                self.tongue_anim_dir = -1
            elif next_idx <= 0:
                self._cancel_tongue_rattle(now_ms, reschedule=True)
                break
            else:
                self.tongue_frame_idx = next_idx

    def _draw_tongue_frame(self, head_c, face_angle, lay, frame_idx):
        if frame_idx <= 0 or frame_idx >= len(self._scaled_tongue_frames):
            return

        sprite = self._scaled_tongue_frames[frame_idx]
        rot = pygame.transform.rotate(sprite, -face_angle)
        dx, dy = self._angle_vec(face_angle)
        perp_x, perp_y = -dy, dx
        ts = lay['tile_size']
        base_x = head_c[0] + dx * ts * TONGUE_ANCHOR_FWD + perp_x * ts * TONGUE_ANCHOR_SIDE
        base_y = head_c[1] + dy * ts * TONGUE_ANCHOR_FWD + perp_y * ts * TONGUE_ANCHOR_SIDE
        tongue_extent = max(rot.get_width(), rot.get_height())
        tx = base_x + dx * tongue_extent * TONGUE_BASE_OFFSET
        ty = base_y + dy * tongue_extent * TONGUE_BASE_OFFSET

        shadow_yoff = int(ts * TONGUE_SHADOW_YOFF_FACTOR)
        shadow_len = max(2.0, sprite.get_width() * TONGUE_SHADOW_SCALE)
        shadow_r = max(1, int(sprite.get_height() * 0.18))
        sh_start = (
            base_x + dx * shadow_len * 0.08,
            base_y + shadow_yoff + dy * shadow_len * 0.08,
        )
        sh_end = (
            base_x + dx * shadow_len * 0.92,
            base_y + shadow_yoff + dy * shadow_len * 0.92,
        )
        min_x = int(min(sh_start[0], sh_end[0]) - shadow_r - 2)
        min_y = int(min(sh_start[1], sh_end[1]) - shadow_r - 2)
        max_x = int(max(sh_start[0], sh_end[0]) + shadow_r + 2)
        max_y = int(max(sh_start[1], sh_end[1]) + shadow_r + 2)
        shadow_surf = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)
        draw_capsule(
            shadow_surf,
            (0, 0, 0, TONGUE_SHADOW_ALPHA),
            (sh_start[0] - min_x, sh_start[1] - min_y),
            (sh_end[0] - min_x, sh_end[1] - min_y),
            shadow_r,
        )
        self.window.blit(shadow_surf, (min_x, min_y))

        rect = rot.get_rect(center=(int(tx), int(ty)))
        self.window.blit(rot, rect.topleft)

    def new_game(self):
        self._stop_audio()
        self.score = 0
        self.game_state = "waiting"
        self.tail_darkness = 0.0   # 0 = flat royal-blue,  1 = max dark navy
        self.play_button_rect = None
        self.starter_card_visible = False
        self.starter_card_context = None
        self.starter_card_reveal_ms = None
        self.starter_card_run_score = 0
        self.show_waiting_start_cue = False

        cx, cy = GRID_COLS // 2, GRID_ROWS // 2
        head_x = cx - (START_SNAKE_SEGMENTS + 1)
        self.snake = [(head_x - offset, cy) for offset in range(START_SNAKE_SEGMENTS)]
        self.apple = (cx + 3, cy)

        self.direction = RIGHT
        self.next_dir = RIGHT
        self.input_queue = deque(maxlen=3)
        self.start_move_locked = False
        self.prev_head = self.snake[0]
        self.prev_tail = self.snake[-1]
        self.prev_direction = self.direction
        self.last_tick_ms = pygame.time.get_ticks()
        self._apple_pulse_frozen = 1.0
        self.head_angle_deg = self._dir_to_angle(self.direction)
        self.turn_from_deg = self.head_angle_deg
        self.turn_to_deg = self.head_angle_deg
        self.turn_start_ms = self.last_tick_ms
        self.turn_end_ms = self.last_tick_ms
        self.mouth_phase = 0.0
        self.mouth_target_open = False
        self.mouth_last_update_ms = self.last_tick_ms
        self.mouth_frame_idx = 0
        self.mouth_close_delay_until_ms = 0
        self.tongue_anim_active = False
        self.tongue_anim_phase = 0.0
        self.tongue_anim_dir = 1
        self.tongue_last_update_ms = self.last_tick_ms
        self.tongue_frame_idx = 0
        self.tongue_next_rattle_ms = self.last_tick_ms
        self._schedule_next_tongue_rattle(self.last_tick_ms)
        self.eye_blink_active = False
        self.eye_frame_idx = 0
        self.eye_last_update_ms = self.last_tick_ms
        self.eye_next_blink_ms = self.last_tick_ms
        self._schedule_next_eye_blink(self.last_tick_ms)
        self.bulges = []
        self._reset_recoil_path_history()
        self.collision_recoil = None
        self.death_pose = None
        self.death_face_anim = None
        self.collision_effect = None
        self.death_overlay_delay_until_ms = 0

    def _spawn_apple(self):
        all_cells = {(c, r) for c in range(GRID_COLS) for r in range(GRID_ROWS)}
        free = list(all_cells - set(self.snake))
        self.apple = random.choice(free) if free else None

    def _is_head_near_apple_tiles(self):
        if self.apple is None or not self.snake:
            return False
        hx, hy = self.snake[0]
        ax, ay = self.apple
        dist = max(abs(hx - ax), abs(hy - ay))
        return 0 < dist <= MOUTH_TRIGGER_RADIUS_TILES

    def _update_mouth_anim(self, now_ms, near_apple):
        if self.game_state != "playing":
            self.mouth_target_open = False
            self.mouth_close_delay_until_ms = 0
        else:
            if near_apple:
                self.mouth_target_open = True
                self.mouth_close_delay_until_ms = 0
            else:
                # Delay start of closing animation by configured amount.
                if self.mouth_phase > 0.0:
                    if self.mouth_close_delay_until_ms == 0:
                        self.mouth_close_delay_until_ms = now_ms + int(MOUTH_CLOSE_DELAY_SEC * 1000)
                    if now_ms >= self.mouth_close_delay_until_ms:
                        self.mouth_target_open = False
                else:
                    self.mouth_target_open = False
                    self.mouth_close_delay_until_ms = 0

        prev_phase = self.mouth_phase
        duration_sec = max(1e-6, MOUTH_OPEN_CLOSE_FRAMES / FPS)
        dt = max(0.0, (now_ms - self.mouth_last_update_ms) / 1000.0)
        self.mouth_last_update_ms = now_ms
        step = dt / duration_sec
        target = 1.0 if self.mouth_target_open else 0.0
        if self.mouth_phase < target:
            self.mouth_phase = min(target, self.mouth_phase + step)
        elif self.mouth_phase > target:
            self.mouth_phase = max(target, self.mouth_phase - step)
        opening = self.mouth_target_open or self.mouth_phase >= prev_phase
        self.mouth_frame_idx = self._mouth_frame_from_phase(self.mouth_phase, opening)

    def _mouth_frame_from_phase(self, phase, opening):
        p = max(0.0, min(1.0, phase))
        if p <= 0.0 or not self.mouth_frames or not self.mouth_frame_open_amounts:
            return 0

        peak_idx = max(0, min(self.mouth_peak_frame_idx, len(self.mouth_frame_open_amounts) - 1))
        if opening:
            if peak_idx <= 0:
                candidates = list(range(1, len(self.mouth_frame_open_amounts)))
            else:
                candidates = list(range(1, peak_idx + 1))
            tie_break = lambda i: i
        else:
            candidates = list(range(peak_idx, len(self.mouth_frame_open_amounts)))
            if 0 not in candidates:
                candidates.append(0)
            tie_break = lambda i: -i

        if not candidates:
            return 0

        return min(
            candidates,
            key=lambda i: (abs(self.mouth_frame_open_amounts[i] - p), tie_break(i)),
        )

    def _draw_mouth_frame(self, head_c, face_angle, lay, frame_idx):
        if frame_idx <= 0 or frame_idx >= len(self._scaled_mouth_frames):
            return
        sprite = self._scaled_mouth_frames[frame_idx]
        rot = pygame.transform.rotate(sprite, -face_angle)
        dx, dy = self._angle_vec(face_angle)
        perp_x, perp_y = -dy, dx
        ts = lay['tile_size']
        mx = head_c[0] + dx * ts * MOUTH_ANCHOR_FWD + perp_x * ts * MOUTH_ANCHOR_SIDE
        my = head_c[1] + dy * ts * MOUTH_ANCHOR_FWD + perp_y * ts * MOUTH_ANCHOR_SIDE

        sw = max(2, int(rot.get_width() * MOUTH_SHADOW_SCALE))
        sh = max(2, int(rot.get_height() * MOUTH_SHADOW_SCALE * 0.45))
        mouth_shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(mouth_shadow, (0, 0, 0, FACE_SHADOW_ALPHA), mouth_shadow.get_rect())
        self.window.blit(mouth_shadow, (int(mx - sw // 2), int(my - sh // 2 + ts * 0.08)))
        rect = rot.get_rect(center=(int(mx), int(my)))
        self.window.blit(rot, rect.topleft)

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self._ensure_raw_images("not_full_screen")
        self._last_fs_toggle_ms = pygame.time.get_ticks()
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        self._last_scale = None

    # ── Main loop ─────────────────────────────────────────────────────────────
    def _main_loop(self):
        while True:
            self._refresh_starter_card_visibility()
            self._handle_events()
            self._tick_if_due()
            self._update_collision_recoil()
            self._refresh_starter_card_visibility()
            self._ensure_assets()
            self._draw()
            mouse_pos = pygame.mouse.get_pos()
            if ((self.x_rect  and self.x_rect.collidepoint(mouse_pos)) or
                (self.fs_rect and self.fs_rect.collidepoint(mouse_pos)) or
                (self.vol_rect and self.vol_rect.collidepoint(mouse_pos)) or
                (self.play_button_rect and self.play_button_rect.collidepoint(mouse_pos))):
                pygame.mouse.set_cursor(self.cursor_hand)
            else:
                pygame.mouse.set_cursor(self.cursor_default)
            if self._deferred_tasks_started:
                if not self._run_next_deferred_startup_task():
                    self._load_next_lazy_animation()
            else:
                self._deferred_tasks_started = True
            self.clock.tick(FPS)

    # ── Input ─────────────────────────────────────────────────────────────────
    def _handle_events(self):
        self._refresh_starter_card_visibility()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.x_rect and self.x_rect.collidepoint(event.pos):
                    pygame.quit(); exit()
                if event.button == 1 and self.fs_rect and self.fs_rect.collidepoint(event.pos):
                    self._toggle_fullscreen()
                if event.button == 1 and self.vol_rect and self.vol_rect.collidepoint(event.pos):
                    self._toggle_audio_mute()
                if (
                    event.button == 1 and
                    self.starter_card_visible and
                    self.play_button_rect and
                    self.play_button_rect.collidepoint(event.pos)
                ):
                    self._handle_starter_card_play()
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); exit()
                if event.key == pygame.K_f:
                    self._toggle_fullscreen(); return
                if (
                    event.key == pygame.K_r and
                    self.game_state == "waiting" and
                    self.starter_card_visible and
                    self.starter_card_context == "launch"
                ):
                    self._ensure_raw_images("start_box")
                    self.show_waiting_start_cue = True
                    self._hide_starter_card()
                    return
                if event.key == pygame.K_r and self.game_state == "dead":
                    self.new_game()
                    return
                if self.starter_card_visible:
                    continue
                if self.game_state == "waiting" and event.key in DIR_KEYS:
                    if self._start_waiting_run(DIR_KEYS[event.key]):
                        return
                if self.game_state == "playing" and event.key in DIR_KEYS:
                    self._enqueue_direction(DIR_KEYS[event.key])

    def _enqueue_direction(self, new_dir):
        if self.start_move_locked:
            return False
        base_dir = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir == (-base_dir[0], -base_dir[1]): return False
        if new_dir == base_dir: return False
        self.input_queue.append(new_dir)
        self.next_dir = new_dir
        if len(self.input_queue) == 1:
            self._start_head_turn(new_dir, pygame.time.get_ticks())
        return True

    def _tick_if_due(self):
        if self.game_state != "playing":
            return
        now = pygame.time.get_ticks()
        while now - self.last_tick_ms >= TICK_RATE:
            self._update()
            if self.game_state != "playing":
                break
            bulge_step_px = self._bulge_headspace_speed_px(self._layout()['tile_size'])
            for bulge in self.bulges:
                if bulge.get('delay_frames', 0) > 0:
                    continue
                if not bulge.get('released', False):
                    continue
                if bulge.get('hold_head_until_tick', False):
                    bulge['hold_head_until_tick'] = False
                    continue
                bulge['dist_px'] += bulge_step_px
            self.last_tick_ms += TICK_RATE

    def _update(self):
        self.prev_direction = self.direction
        if self.input_queue:
            self.direction = self.input_queue.popleft()
        else:
            self.direction = self.next_dir
        if self.direction != self.prev_direction:
            self._play_turn_sfx()

        if self.input_queue:
            self._start_head_turn(self.input_queue[0], self.last_tick_ms)

        self.prev_head = self.snake[0]
        self.prev_tail = self.snake[-1]

        hx, hy   = self.snake[0]
        dx, dy   = self.direction
        new_head = (hx + dx, hy + dy)

        if not (0 <= new_head[0] < GRID_COLS and 0 <= new_head[1] < GRID_ROWS):
            self._begin_collision_recoil("border", new_head)
            return
        if new_head in self.snake[:-1]:
            self._begin_collision_recoil("self", new_head)
            return

        self.snake.insert(0, new_head)
        self.start_move_locked = False
        self._record_recoil_path_head(new_head)
        if new_head == self.apple:
            self.score      += 1
            self.high_score  = max(self.high_score, self.score)
            self.tail_darkness = min(1.0, self.tail_darkness + APPLE_DARKEN_STEP)
            self._spawn_bulge()
            self._spawn_apple()
        else:
            self.snake.pop()

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        lay      = self._layout()
        a        = self._scaled_assets
        now      = pygame.time.get_ticks()
        progress = min((now - self.last_tick_ms) / TICK_RATE, 1.0)
        starter_card_visible = self.starter_card_visible
        self.play_button_rect = None

        self.window.fill(HEADER_COLOUR)
        self._draw_header(lay, a)
        pygame.draw.rect(self.window, PANEL_COLOUR,
                         pygame.Rect(0, lay['header_h'],
                                     lay['win_w'], lay['win_h'] - lay['header_h']))
        self._draw_tiles(lay, a)
        self._draw_apple(lay, a)
        self._draw_snake(lay, progress, now)

        if starter_card_visible:
            self._draw_starter_card_overlay(lay, a)
        elif self.game_state == "waiting" and self.show_waiting_start_cue:
            self._draw_waiting_start_cue(lay, a)

        fullscreen_icon = a['not_full_screen'] if self.fullscreen else a['full_screen']
        volume_icon = a['volume_muted'] if self.audio_muted else a['volume']
        for icon, rect in (
            (fullscreen_icon, self.fs_rect),
            (volume_icon, self.vol_rect),
            (a['x'], self.x_rect),
        ):
            if rect is None: continue
            draw_rect = icon.get_rect(center=rect.center)
            self.window.blit(icon, draw_rect.topleft)

        pygame.display.flip()

    def _draw_header(self, lay, a):
        icon_x = int(12 * lay['sc'])
        icon_y = (lay['header_h'] - a['apple_icon'].get_height()) // 2
        self.window.blit(a['apple_icon'], (icon_x, icon_y))
        score_surf = self.font_score.render(str(self.score), True, SCORE_COLOUR)
        self.window.blit(score_surf, (
            icon_x + a['apple_icon'].get_width() + int(8 * lay['sc']),
            (lay['header_h'] - score_surf.get_height()) // 2))
        trophy_x = icon_x * 10
        self.window.blit(a['trophy'], (trophy_x, icon_y))
        hs_surf = self.font_score.render(str(self.high_score), True, SCORE_COLOUR)
        self.window.blit(hs_surf, (
            trophy_x + a['trophy'].get_width() + int(8 * lay['sc']),
            (lay['header_h'] - a['trophy'].get_height()) // 2))
        margin = int(17 * lay['sc'])
        gap    = int(16 * lay['sc'])
        x_x  = lay['win_w'] - margin - a['x'].get_width()
        x_y  = (lay['header_h'] - a['x'].get_height()) // 2
        vol_w = max(a['volume'].get_width(), a['volume_muted'].get_width())
        vol_h = max(a['volume'].get_height(), a['volume_muted'].get_height())
        vol_x = x_x - gap - vol_w
        vol_y = (lay['header_h'] - vol_h) // 2
        fs_w = max(a['full_screen'].get_width(), a['not_full_screen'].get_width())
        fs_h = max(a['full_screen'].get_height(), a['not_full_screen'].get_height())
        fs_x = vol_x - gap - fs_w
        fs_y = (lay['header_h'] - fs_h) // 2
        self.x_rect  = pygame.Rect(x_x,  x_y,  a['x'].get_width(),          a['x'].get_height())
        self.vol_rect = pygame.Rect(vol_x, vol_y, vol_w, vol_h)
        self.fs_rect = pygame.Rect(fs_x, fs_y, fs_w, fs_h)

    def _draw_tiles(self, lay, a):
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                tile = a['tile_light'] if (row + col) % 2 == 0 else a['tile_dark']
                px, py = self._grid_to_pixel(col, row, lay)
                self.window.blit(tile, (px, py))

    def _draw_apple(self, lay, a):
        if self.apple is None:
            return
        ax, ay = self.apple
        px, py = self._grid_to_pixel(ax, ay, lay)
        ab     = a['apple_board']
        if self.game_state == "dead":
            pulse = self._apple_pulse_frozen
        else:
            t     = pygame.time.get_ticks() / 1000.0
            pulse = 1.0 + 0.20 * (0.5 + 0.5 * pygame.math.Vector2(1, 0).rotate(t * 360).x)
            self._apple_pulse_frozen = pulse
        new_sz  = max(4, int(ab.get_width() * pulse))
        scaled  = pygame.transform.smoothscale(self._raw['apple_icon'], (new_sz, new_sz))
        tile_cx = px + lay['tile_size'] // 2
        tile_cy = py + lay['tile_size'] // 2
        r       = new_sz // 2
        sh_w = int(r * 0.85 * pulse)
        sh_h = max(2, int(r * 0.18 * pulse))
        yoff = int(r * 0.92)
        tmp  = pygame.Surface((max(1, sh_w * 2), max(2, sh_h * 2)), pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, (0, 0, 0, 50), tmp.get_rect())
        self.window.blit(tmp, (tile_cx - sh_w, tile_cy + yoff - sh_h))
        self.window.blit(scaled, (tile_cx - r, tile_cy - r))

    def _draw_snake_body(self, lay, pts):
        if len(pts) < 2:
            return None

        r = lay["body_r"]
        cum = [0.0]
        for i in range(1, len(pts)):
            cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i-1][0],
                                             pts[i][1] - pts[i-1][1]))
        total = cum[-1]
        if total < 1.0:
            return None

        sh_yoff = int(r * SNAKE_SHADOW_YOFF_FACTOR)
        sh_r    = max(1, int(r * SNAKE_SHADOW_RADIUS_FACTOR))
        ox, oy  = lay["board_ox"], lay["board_oy"]
        shadow_surf = pygame.Surface(
            (lay["board_w"], lay["board_h"] + sh_yoff + r + 4), pygame.SRCALPHA)
        for i in range(len(pts) - 1):
            c1, c2 = pts[i], pts[i + 1]
            draw_capsule(shadow_surf, (0, 0, 0, SNAKE_SHADOW_ALPHA),
                         (c1[0] - ox, c1[1] - oy + sh_yoff),
                         (c2[0] - ox, c2[1] - oy + sh_yoff), sh_r)
        self.window.blit(shadow_surf, (ox, oy))

        head_colour = SNAKE_HEAD_COL
        tail_colour = mix_colour(SNAKE_HEAD_COL, SNAKE_TAIL_DARK_MAX, self.tail_darkness)
        step_px = max(1.0, r * 0.40)

        for seg in range(len(pts) - 1):
            p0 = pts[seg]
            p1 = pts[seg + 1]
            seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if seg_len < 0.1:
                continue
            seg_from_head = (len(pts) - 2) - seg
            seg_r = self._radius_for_segment_from_head(seg_from_head, r)
            steps = max(1, int(math.ceil(seg_len / step_px)))
            prev_pt = p0
            for s in range(1, steps + 1):
                t_local = s / steps
                cur_pt = (p0[0] + (p1[0] - p0[0]) * t_local,
                          p0[1] + (p1[1] - p0[1]) * t_local)
                mid_t = (s - 0.5) / steps
                arc_dist = cum[seg] + seg_len * mid_t
                frac = max(0.0, min(1.0, arc_dist / total))
                col = mix_colour(tail_colour, head_colour, frac)
                draw_capsule(self.window, col, prev_pt, cur_pt, seg_r)
                prev_pt = cur_pt

        return cum, total

    def _draw_snake(self, lay, progress, now):
        n = len(self.snake)
        if n < 2:
            return

        if self.game_state == "colliding" and self.collision_recoil:
            recoil_progress = self._collision_retrace_progress(now)
            tail_trim_px = self._collision_tail_trim_px(now, lay)
            pts, head_c, head_angle = self._build_recoil_points(
                lay,
                self.collision_recoil['impact_head'],
                self.collision_recoil['retrace_path_grid'],
                self.collision_recoil['visible_length'],
                recoil_progress,
                tail_trim_px=tail_trim_px,
            )
            body = self._draw_snake_body(lay, pts)
            if body is None or head_c is None:
                return
            face_angle = self._face_angle_from_head_path(pts, lay, head_angle)
            self._draw_collision_effect(now, head_c, lay)
            self._draw_death_face(
                head_c,
                recoil_progress,
                face_angle,
                self.collision_recoil.get('recoil_face_from_angle'),
                self.collision_recoil.get('recoil_face_to_angle'),
                self.collision_recoil['impact_face_angle'],
                self.collision_recoil['twitch_face_angle'],
                lay,
                now,
            )
            return

        if self.game_state == "dead" and self.death_pose:
            pts, head_c, head_angle = self._build_recoil_points(
                lay,
                self.death_pose['impact_head'],
                self.death_pose['retrace_path_grid'],
                self.death_pose['visible_length'],
                self.death_pose['progress'],
            )
            body = self._draw_snake_body(lay, pts)
            if body is None or head_c is None:
                return
            face_angle = self._face_angle_from_head_path(pts, lay, head_angle)
            self._draw_collision_effect(now, head_c, lay)
            self._draw_death_face(
                head_c,
                self.death_pose['progress'],
                face_angle,
                self.death_pose.get('recoil_face_from_angle'),
                self.death_pose.get('recoil_face_to_angle'),
                self.death_pose['impact_face_angle'],
                self.death_pose['twitch_face_angle'],
                lay,
                now,
            )
            return

        r  = lay["body_r"]
        pts, head_c = self._build_transition_points(
            lay,
            self.snake,
            prev_head=self.prev_head,
            prev_tail=self.prev_tail,
            progress=progress,
        )
        if head_c is None:
            return
        head_angle = self._current_head_angle(now)
        body = self._draw_snake_body(lay, pts)
        if body is None:
            return
        face_angle = self._face_angle_from_head_path(pts, lay, head_angle)
        cum, total = body
        head_colour = SNAKE_HEAD_COL
        tail_colour = mix_colour(SNAKE_HEAD_COL, SNAKE_TAIL_DARK_MAX, self.tail_darkness)

        if self.bulges:
            draw_bulges = []
            bulge_speed_px = self._bulge_headspace_speed_px(lay['tile_size'])
            for bulge in self.bulges:
                if bulge.get('delay_frames', 0) > 0:
                    bulge['delay_frames'] -= 1
                    draw_bulges.append(bulge)
                    continue

                if not bulge.get('released', False):
                    bulge['released'] = True
                    bulge['hold_head_until_tick'] = True
                    d = 0.0
                elif bulge.get('hold_head_until_tick', False):
                    d = 0.0
                else:
                    d = bulge['dist_px'] + progress * bulge_speed_px
                arc_from_tail = total - d
                center = self._sample_polyline_at_distance(pts, cum, arc_from_tail)
                seg_idx = self._segment_index_at_arc_distance(cum, arc_from_tail)
                seg_from_head = (len(pts) - 2) - seg_idx
                local_r = self._radius_for_segment_from_head(seg_from_head, r)
                decay_px = max(1.0, bulge['decay_segments'] * lay['tile_size'])
                t = max(0.0, min(1.0, d / decay_px))
                s = lerp(bulge['start_scale'], bulge['end_scale'], smoothstep(t))
                br = max(1, int(local_r * s))
                bulge_frac = max(0.0, min(1.0, arc_from_tail / total))
                bulge_col = mix_colour(tail_colour, head_colour, bulge_frac)
                pygame.draw.circle(self.window, bulge_col, (int(center[0]), int(center[1])), br)

                if d < (total + r) and t < BULGE_END_HIDE_T:
                    draw_bulges.append(bulge)
            self.bulges = draw_bulges

        near_apple = self._is_head_near_apple_tiles()
        self._update_mouth_anim(now, near_apple)
        self._update_tongue_anim(now)
        if self.tongue_anim_active:
            self._draw_tongue_frame(head_c, face_angle, lay, self.tongue_frame_idx)
        self._draw_mouth_frame(head_c, face_angle, lay, self.mouth_frame_idx)
        self._update_eye_blink(now)
        self._draw_eyes(head_c, lay, face_angle)


    def _draw_eyes(self, head_c, lay, face_angle):
        dx, dy         = self._angle_vec(face_angle)
        perp_x, perp_y = -dy, dx
        ts = lay['tile_size']

        sprite = None
        if self._scaled_eye_frames:
            frame_idx = max(0, min(self.eye_frame_idx, len(self._scaled_eye_frames) - 1))
            sprite = self._scaled_eye_frames[frame_idx]

        pair_c = self._face_pair_center(head_c, face_angle, lay)
        side_off = ts * EYE_SEPARATION
        left_eye = (
            pair_c[0] + perp_x * side_off,
            pair_c[1] + perp_y * side_off,
        )
        right_eye = (
            pair_c[0] - perp_x * side_off,
            pair_c[1] - perp_y * side_off,
        )

        if sprite is not None:
            sh_yoff = int(lay["body_r"] * 0.6 * EYE_SHADOW_SCALE)
            sh_r = max(1, int(lay["body_r"] * 0.80 * EYE_SHADOW_SCALE))
            surf_w = int(ts * 2.6)
            surf_h = int(ts * 2.5)
            ox = int(head_c[0] - surf_w / 2)
            oy = int(head_c[1] - surf_h / 2)
            shadow_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            draw_capsule(
                shadow_surf,
                (0, 0, 0, 40),
                (left_eye[0] - ox, left_eye[1] - oy + sh_yoff),
                (right_eye[0] - ox, right_eye[1] - oy + sh_yoff),
                sh_r,
            )
            erase = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            neck_c = (
                head_c[0] - dx * lay["body_r"] * 1.4,
                head_c[1] - dy * lay["body_r"] * 1.4,
            )
            # Remove any part that sits under the blue body itself.
            draw_capsule(
                erase,
                (0, 0, 0, 255),
                (head_c[0] - ox, head_c[1] - oy),
                (neck_c[0] - ox, neck_c[1] - oy),
                lay["body_r"] + 3,
            )
            # Remove overlap with the existing head/body shadow to avoid stacking darker.
            draw_capsule(
                erase,
                (0, 0, 0, 255),
                (head_c[0] - ox, head_c[1] - oy + sh_yoff),
                (neck_c[0] - ox, neck_c[1] - oy + sh_yoff),
                max(1, int(lay["body_r"] * 0.80)),
            )
            shadow_surf.blit(erase, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            self.window.blit(shadow_surf, (ox, oy))

        for ex, ey in (left_eye, right_eye):
            if sprite is not None:
                rot_deg = -face_angle
                eye_sprite = sprite if abs(rot_deg) < 0.01 else pygame.transform.rotate(sprite, rot_deg)
                rect = eye_sprite.get_rect(center=(int(ex), int(ey)))
                self.window.blit(eye_sprite, rect.topleft)

        snout_x = head_c[0] + dx * ts * 0.34
        snout_y = head_c[1] + dy * ts * 0.34
        nost_side = ts * 0.23
        nost_fwd = ts * -0.25
        nost_r = 1
        for sign in (+1, -1):
            nx = snout_x + dx * nost_fwd + perp_x * sign * nost_side
            ny = snout_y + dy * nost_fwd + perp_y * sign * nost_side
            pygame.draw.circle(self.window, NOSE_CLR, (int(nx), int(ny)), nost_r)
        return

    def _draw_starter_card_overlay(self, lay, a):
        card = a.get('snake_card')
        button = a.get('play_button')
        if card is None or button is None:
            return

        shade = pygame.Surface((lay['win_w'], lay['win_h']), pygame.SRCALPHA)
        shade.fill((0, 0, 0, STARTER_CARD_DIM_ALPHA))
        self.window.blit(shade, (0, 0))

        gap = max(8, int(STARTER_CARD_BUTTON_GAP * lay['sc']))
        block_h = card.get_height() + gap + button.get_height()
        center_top = lay['board_oy'] + max(0, (lay['board_h'] - block_h) // 2)
        block_top = max(lay['board_oy'], center_top - int(STARTER_CARD_Y_OFFSET * lay['sc']))
        card_rect = card.get_rect(midtop=(lay['win_w'] // 2, block_top))
        button_rect = button.get_rect(midtop=(lay['win_w'] // 2, card_rect.bottom + gap))

        self.window.blit(card, card_rect.topleft)
        self.window.blit(button, button_rect.topleft)
        self.play_button_rect = button_rect

        if self.starter_card_context != "death":
            return

        stat_font = pygame.font.SysFont("Arial", max(8, int(card.get_height() * 0.10)))
        run_score_surf = stat_font.render(str(self.starter_card_run_score), True, SCORE_COLOUR)
        best_score_surf = stat_font.render(str(self.high_score), True, SCORE_COLOUR)
        stat_y = card_rect.y + int(card.get_height() * STARTER_CARD_STAT_Y)
        left_x = card_rect.x + int(card.get_width() * STARTER_CARD_STAT_LEFT_X)
        right_x = card_rect.x + int(card.get_width() * STARTER_CARD_STAT_RIGHT_X)
        self.window.blit(run_score_surf, run_score_surf.get_rect(center=(left_x, stat_y)))
        self.window.blit(best_score_surf, best_score_surf.get_rect(center=(right_x, stat_y)))

    def _draw_waiting_start_cue(self, lay, a):
        icon = a.get('start_box')
        if icon is None:
            return
        pad = max(8, int(WAITING_CUE_BOX_PAD * lay['sc']))
        box_w = icon.get_width() + pad * 2
        box_h = icon.get_height() + pad * 2
        box_x = lay['board_ox'] + (lay['board_w'] - box_w) // 2
        box_y = lay['board_oy'] + int(lay['board_h'] * WAITING_CUE_CENTER_Y_RATIO) - box_h // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        cue_box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(
            cue_box,
            (0, 0, 0, WAITING_CUE_BOX_ALPHA),
            cue_box.get_rect(),
            border_radius=max(1, int(WAITING_CUE_BOX_RADIUS * lay['sc'])),
        )
        self.window.blit(cue_box, box_rect.topleft)
        icon_rect = icon.get_rect(center=box_rect.center)
        self.window.blit(icon, icon_rect.topleft)


if __name__ == "__main__":
    SnakeGame()
