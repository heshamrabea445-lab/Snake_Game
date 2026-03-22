import pygame
import random
from collections import deque
import math


# ── Base design resolution ─────────────────────────────────────────────────────
BASE_W   = 650
BASE_H   = 650

WINDOW_W = 650
WINDOW_H = 650

HEADER_H_BASE  = 70
BORDER_BASE    = 19
TILE_SIZE_BASE = 34
GRID_COLS = 18
GRID_ROWS = 16
START_SNAKE_SEGMENTS = 4

TICK_RATE = 125
FPS       = 60
EARLY_TURN_STEP_MS = int(TICK_RATE * 0.70)
DEATH_CONTACT_HOLD_MS = 300
DEATH_RECOIL_MS = 500
DEATH_SCREEN_DELAY_MS = 1000
BORDER_CONTACT_INSET_TILES = 0.88
COLLISION_BACKUP_TILES = 1.0
COLLISION_EFFECT_SCALE = 1.5
COLLISION_EFFECT_FRAME_COUNT = 21
COLLISION_EFFECT_SPEED_MULT = 2.5 # >1 faster, <1 slower
COLLISION_EFFECT_ANCHOR_FWD = -1.2
COLLISION_EFFECT_EXTRA_ROT_DEG = 180
DEATH_FACE_FRAME_COUNT = 36
DEATH_FACE_SCALE = 1
DEATH_FACE_SEPARATOR_W = 1
DEATH_FACE_ANCHOR_FWD = -0.2
DEATH_FACE_TWITCH_START_FRAME = 20
DEATH_FACE_INTRO_FRAME_MS = 65
DEATH_FACE_TWITCH_FRAME_MS = 65
# ── Colours ───────────────────────────────────────────────────────────────────
HEADER_COLOUR  = ( 78, 112,  50)
PANEL_COLOUR   = ( 87, 138,  52)
TILE_LIGHT     = (154, 202,  60)
TILE_DARK      = (140, 185,  50)

# Gradient: head = royal blue (fixed). Tail starts identical (flat/invisible
# gradient at game start) and darkens toward dark navy each apple eaten.
SNAKE_HEAD_COL      = ( 78, 126, 240)   # base snake body/head blue
SNAKE_TAIL_DARK_MAX = ( 18,  38, 110)   # dark navy – maximum tail darkness
APPLE_DARKEN_STEP   = 0.040             # ~25 apples to reach full dark navy
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
EYE_SPRITE_SCALE = 1.00
EYE_CENTER_FWD = -0.45
EYE_CENTER_SIDE = 0.00
EYE_SEPARATION = 0.32
EYE_SHADOW_SCALE = 0.8
EYE_TRACK_MAX_ROT_DEG = 180.0
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
# Visual travel speed of the bulge down the snake while snake is moving.
# Internally we add snake advection (+1 segment/tick in head-space) so the
# bulge does not appear stationary on straight runs.
BULGE_TRAVEL_SEG_PER_TICK = 1
BULGE_FADE_SEGMENTS_CAP = 25 
BULGE_MIN_VISIBLE_SCALE = 1.
BULGE_SAMPLE_STEP_FACTOR = 0.40
FACE_SHADOW_ALPHA = 38
FACE_SHADOW_YOFF_FACTOR = 0.55
MOUTH_SHADOW_SCALE = 0.95
SEGMENT_SHRINK_PER_SEG = 0.25
TAIL_MIN_RADIUS_FACTOR = 0.62

EYE_WHITE    = (235, 235, 235)
EYE_PUPIL    = ( 20,  20,  20)
EYE_RING     = ( 95, 135, 235)
NOSE_CLR     = ( 18,  60, 160)
SCORE_COLOUR = (255, 255, 255)
OVERLAY_CLR  = (  0,   0,   0, 160)
LOST_CLR     = (210,  55,  55)
HINT_CLR     = (190, 190, 190)
START_CLR    = (255, 220,  50)

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
        pygame.init()
        self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.set_caption("Snake")
        pygame.display.set_icon(pygame.image.load("snake_icon.png"))
        self.clock = pygame.time.Clock()

        self.cursor_hand    = pygame.SYSTEM_CURSOR_HAND
        self.cursor_default = pygame.SYSTEM_CURSOR_ARROW
        self.high_score  = 0
        self.fullscreen  = False
        self.x_rect      = None
        self.fs_rect     = None
        self._last_fs_toggle_ms = 0

        self._last_scale    = None
        self._last_win_size = None
        self._scaled_assets = {}
        self._scaled_mouth_frames = []
        self._scaled_tongue_frames = []
        self._scaled_eye_frames = []
        self._scaled_death_face_frames = []
        self._scaled_collision_effect_frames = []

        self._load_raw_images()
        self._load_mouth_frames()
        self._load_tongue_frames()
        self._load_eye_frames()
        self._load_death_face_frames()
        self._load_collision_effect_frames()
        self._rebuild_fonts(1.0)
        self._rebuild_overlay()
        self.new_game()
        self._main_loop()

    # ── Scale helpers ─────────────────────────────────────────────────────────
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
            self._rebuild_overlay()
        if scale_changed:
            self._last_scale = scale
            def sc(img, base_w, base_h=None):
                if base_h is None: base_h = base_w
                return pygame.transform.smoothscale(
                    img, (max(1, int(base_w * scale)), max(1, int(base_h * scale))))
            self._scaled_assets = {
                'tile_light':  sc(self._raw['tile_light'],  TILE_SIZE_BASE),
                'tile_dark':   sc(self._raw['tile_dark'],   TILE_SIZE_BASE),
                'trophy':      sc(self._raw['trophy'],      44),
                'apple_icon':  sc(self._raw['apple_icon'],  44),
                'apple_board': sc(self._raw['apple_icon'],  TILE_SIZE_BASE),
                'x':           sc(self._raw['x'],           40),
                'full_screen': sc(self._raw['full_screen'], 40),
            }
            self._scaled_mouth_frames = []
            for src in self.mouth_frames:
                mw = max(1, int(src.get_width() * scale * MOUTH_SCALE))
                mh = max(1, int(src.get_height() * scale * MOUTH_SCALE))
                self._scaled_mouth_frames.append(
                    pygame.transform.smoothscale(src, (mw, mh))
                )
            self._scaled_tongue_frames = []
            for src in self.snake_tongue:
                tw = max(1, int(src.get_width() * scale * TONGUE_SCALE))
                th = max(1, int(src.get_height() * scale * TONGUE_SCALE))
                self._scaled_tongue_frames.append(
                    pygame.transform.smoothscale(src, (tw, th))
                )
            self._scaled_eye_frames = []
            for src in self.eye_frames:
                ew = max(1, int(src.get_width() * scale))
                eh = max(1, int(src.get_height() * scale))
                self._scaled_eye_frames.append(
                    pygame.transform.smoothscale(src, (ew, eh))
                )
            self._scaled_death_face_frames = []
            for src in self.death_face_frames:
                dw = max(1, int(src.get_width() * scale * DEATH_FACE_SCALE))
                dh = max(1, int(src.get_height() * scale * DEATH_FACE_SCALE))
                self._scaled_death_face_frames.append(
                    pygame.transform.smoothscale(src, (dw, dh))
                )
            self._scaled_collision_effect_frames = []
            for src in self.collision_effect_frames:
                ew = max(1, int(src.get_width() * scale * COLLISION_EFFECT_SCALE))
                eh = max(1, int(src.get_height() * scale * COLLISION_EFFECT_SCALE))
                self._scaled_collision_effect_frames.append(
                    pygame.transform.smoothscale(src, (ew, eh))
                )
            self._rebuild_fonts(scale)

    def _rebuild_fonts(self, scale):
        self.font_large  = pygame.font.SysFont("Arial", max(8, int(52 * scale)), bold=True)
        self.font_medium = pygame.font.SysFont("Arial", max(8, int(30 * scale)), bold=True)
        self.font_small  = pygame.font.SysFont("Arial", max(8, int(26 * scale)))
        self.font_score  = pygame.font.SysFont("Arial", max(8, int(34 * scale)), bold=True)

    def _rebuild_overlay(self):
        ww, wh = self.window.get_size()
        self.overlay = pygame.Surface((ww, wh), pygame.SRCALPHA)
        self.overlay.fill(OVERLAY_CLR)

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

    def _eye_track_rotation_deg(self, eye_center, apple_center):
        if apple_center is None:
            return 0.0

        vx = apple_center[0] - eye_center[0]
        vy = apple_center[1] - eye_center[1]
        if abs(vx) < 1e-6 and abs(vy) < 1e-6:
            return 0.0

        target_deg = math.degrees(math.atan2(vy, vx))
        rot_deg = -target_deg
        return max(-EYE_TRACK_MAX_ROT_DEG, min(EYE_TRACK_MAX_ROT_DEG, rot_deg))

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
            pts.append(self._offset_point(self._cell_center(*segments[i], lay), off_px))
        return pts

    def _collision_offset_tiles(self, now_ms):
        if not self.collision_recoil:
            return (0.0, 0.0)

        recoil = self.collision_recoil
        contact = recoil['contact_offset_tiles']
        target = recoil['target_offset_tiles']
        if now_ms <= recoil['hold_until_ms']:
            t = 0.0
        else:
            dur = max(1, recoil['recoil_end_ms'] - recoil['hold_until_ms'])
            t = max(0.0, min(1.0, (now_ms - recoil['hold_until_ms']) / dur))
            t = smoothstep(t)
        return (
            lerp(contact[0], target[0], t),
            lerp(contact[1], target[1], t),
        )

    def _collision_effect_frame_idx(self, now_ms):
        if not self.collision_effect or not self._scaled_collision_effect_frames:
            return None

        frame_count = len(self._scaled_collision_effect_frames)
        if frame_count <= 0:
            return None
        if frame_count == 1:
            return 0

        total_visible_ms = (
            DEATH_CONTACT_HOLD_MS +
            DEATH_RECOIL_MS +
            DEATH_SCREEN_DELAY_MS
        )
        speed_mult = max(0.01, COLLISION_EFFECT_SPEED_MULT)
        frame_ms = max(1, int(math.ceil(total_visible_ms / ((frame_count - 1) * speed_mult))))
        elapsed = max(0, now_ms - self.collision_effect['start_ms'])
        return min(frame_count - 1, int(elapsed // frame_ms))

    def _draw_collision_effect(self, now_ms):
        frame_idx = self._collision_effect_frame_idx(now_ms)
        if frame_idx is None:
            return

        sprite = self._scaled_collision_effect_frames[frame_idx]
        rot_deg = self.collision_effect.get('angle_deg', 0.0)
        if abs(rot_deg) > 0.01:
            sprite = pygame.transform.rotate(sprite, rot_deg)

        anchor_x, anchor_y = self.collision_effect['anchor_px']
        rect = sprite.get_rect(center=(int(anchor_x), int(anchor_y)))
        self.window.blit(sprite, rect.topleft)

    def _death_face_frame_idx(self, now_ms):
        if self.death_face_start_ms is None or not self._scaled_death_face_frames:
            return None

        frame_count = len(self._scaled_death_face_frames)
        if frame_count <= 0:
            return None
        if frame_count == 1:
            return 0

        intro_frames = max(1, min(DEATH_FACE_TWITCH_START_FRAME, frame_count))
        intro_frame_ms = max(1, DEATH_FACE_INTRO_FRAME_MS)
        elapsed = max(0, now_ms - self.death_face_start_ms)
        intro_end_ms = intro_frames * intro_frame_ms
        if elapsed < intro_end_ms:
            return min(intro_frames - 1, int(elapsed // intro_frame_ms))

        loop_start = intro_frames
        if loop_start >= frame_count:
            return frame_count - 1

        loop_count = frame_count - loop_start
        loop_frame_ms = max(1, DEATH_FACE_TWITCH_FRAME_MS)
        loop_elapsed = elapsed - intro_end_ms
        return loop_start + (int(loop_elapsed // loop_frame_ms) % loop_count)

    def _draw_death_face(self, head_c, head_angle, lay, now_ms):
        frame_idx = self._death_face_frame_idx(now_ms)
        if frame_idx is None:
            return

        sprite = self._scaled_death_face_frames[frame_idx]
        dx, dy = self._angle_vec(head_angle)
        ts = lay['tile_size']
        face_target = (
            head_c[0] + dx * ts * DEATH_FACE_ANCHOR_FWD,
            head_c[1] + dy * ts * DEATH_FACE_ANCHOR_FWD,
        )
        angle = -head_angle
        rot = sprite if abs(angle) < 0.01 else pygame.transform.rotate(sprite, angle)
        rect = rot.get_rect(center=(int(round(face_target[0])), int(round(face_target[1]))))
        self.window.blit(rot, rect.topleft)

    def _begin_collision_recoil(self, kind, impact_head):
        now_ms = pygame.time.get_ticks()
        dx, dy = self.direction
        contact_scalar = -BORDER_CONTACT_INSET_TILES if kind == "border" else 0.0
        target_scalar = contact_scalar - COLLISION_BACKUP_TILES
        base_segments = [impact_head] + self.snake[:-1]

        self.game_state = "colliding"
        self.high_score = max(self.high_score, self.score)
        self.input_queue.clear()
        self.next_dir = self.direction
        self.collision_recoil = {
            'kind': kind,
            'direction': self.direction,
            'base_segments': base_segments,
            'contact_offset_tiles': (dx * contact_scalar, dy * contact_scalar),
            'target_offset_tiles': (dx * target_scalar, dy * target_scalar),
            'hold_until_ms': now_ms + DEATH_CONTACT_HOLD_MS,
            'recoil_end_ms': now_ms + DEATH_CONTACT_HOLD_MS + DEATH_RECOIL_MS,
            'head_angle': self._dir_to_angle(self.direction),
        }
        lay = self._layout()
        contact_pts = self._build_pose_points(
            lay,
            base_segments,
            offset_tiles_xy=(dx * contact_scalar, dy * contact_scalar),
        )
        head_c = contact_pts[-1] if contact_pts else self._cell_center(*impact_head, lay)
        anchor_px = (
            head_c[0] + dx * lay['tile_size'] * COLLISION_EFFECT_ANCHOR_FWD,
            head_c[1] + dy * lay['tile_size'] * COLLISION_EFFECT_ANCHOR_FWD,
        )
        extra_rot_deg = COLLISION_EFFECT_EXTRA_ROT_DEG if self.direction in (UP, DOWN) else 0.0
        self.collision_effect = {
            'start_ms': now_ms,
            'angle_deg': self._dir_to_angle(self.direction) + extra_rot_deg,
            'anchor_px': anchor_px,
        }
        self.death_face_start_ms = now_ms

    def _update_collision_recoil(self):
        if self.game_state != "colliding" or not self.collision_recoil:
            return

        now_ms = pygame.time.get_ticks()
        if now_ms < self.collision_recoil['recoil_end_ms']:
            return

        self.death_pose = {
            'segments': list(self.collision_recoil['base_segments']),
            'offset_tiles': self.collision_recoil['target_offset_tiles'],
            'head_angle': self.collision_recoil['head_angle'],
        }
        self.death_overlay_delay_until_ms = now_ms + DEATH_SCREEN_DELAY_MS
        self.collision_recoil = None
        self.game_state = "dead"

    # ── Setup ─────────────────────────────────────────────────────────────────
    def _load_raw_images(self):
        self._raw = {
            'tile_light':  pygame.image.load("light_green.png").convert(),
            'tile_dark':   pygame.image.load("dark_green.png").convert(),
            'trophy':      pygame.image.load("trophy.png").convert_alpha(),
            'apple_icon':  pygame.image.load("apple_icon.png").convert_alpha(),
            'x':           pygame.image.load("x.png").convert_alpha(),
            'full_screen': pygame.image.load("full_screen.png").convert_alpha(),
        }

    def _crop_alpha_bounds(self, surf):
        w, h = surf.get_size()
        min_x, min_y = w, h
        max_x, max_y = -1, -1
        for y in range(h):
            for x in range(w):
                if surf.get_at((x, y)).a <= 0:
                    continue
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        if max_x < min_x or max_y < min_y:
            return None

        crop_w = max_x - min_x + 1
        crop_h = max_y - min_y + 1
        cropped = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA)
        cropped.blit(surf, (0, 0), pygame.Rect(min_x, min_y, crop_w, crop_h))
        return cropped

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
            strip = pygame.image.load("tongue_sprites.png").convert_alpha()
            self.snake_tongue = self._slice_tongue_strip(strip)
        except Exception:
            self.snake_tongue = []

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
            strip = pygame.image.load("mouth_sprite.png").convert_alpha()
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

    def _load_eye_frames(self):
        self.eye_frames = []
        try:
            strip = pygame.image.load("eyes_sprites.png").convert_alpha()
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

        return frames

    def _load_death_face_frames(self):
        self.death_face_frames = []
        try:
            strip = pygame.image.load("death_sprites.png").convert_alpha()
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
            strip = pygame.image.load("collision_effects_sprite.png").convert_alpha()
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

    def _draw_tongue_frame(self, head_c, head_angle, lay, frame_idx):
        if frame_idx <= 0 or frame_idx >= len(self._scaled_tongue_frames):
            return

        sprite = self._scaled_tongue_frames[frame_idx]
        rot = pygame.transform.rotate(sprite, -head_angle)
        dx, dy = self._angle_vec(head_angle)
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
        self.score         = 0
        self.game_state    = "waiting"
        self.tail_darkness = 0.0   # 0 = flat royal-blue,  1 = max dark navy

        cx, cy     = GRID_COLS // 2, GRID_ROWS // 2
        self.snake = [(cx - 3, cy), (cx - 4, cy), (cx - 5, cy), (cx - 6, cy)]
        self.apple = (cx + 3, cy)

        self.direction      = RIGHT
        self.next_dir       = RIGHT
        self.input_queue    = deque(maxlen=3)
        self.prev_head      = self.snake[0]
        self.prev_tail      = self.snake[-1]   # ← kept: needed for ghost_tip
        self.prev_direction = self.direction
        self.last_tick_ms   = pygame.time.get_ticks()
        self._apple_pulse_frozen = 1.0
        self.head_angle_deg = self._dir_to_angle(self.direction)
        self.turn_from_deg  = self.head_angle_deg
        self.turn_to_deg    = self.head_angle_deg
        self.turn_start_ms  = self.last_tick_ms
        self.turn_end_ms    = self.last_tick_ms
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
        self.collision_recoil = None
        self.death_pose = None
        self.death_face_start_ms = None
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

    def _draw_mouth_frame(self, head_c, head_angle, lay, frame_idx):
        if frame_idx <= 0 or frame_idx >= len(self._scaled_mouth_frames):
            return
        sprite = self._scaled_mouth_frames[frame_idx]
        rot = pygame.transform.rotate(sprite, -head_angle)
        dx, dy = self._angle_vec(head_angle)
        perp_x, perp_y = -dy, dx
        ts = lay['tile_size']
        mx = head_c[0] + dx * ts * MOUTH_ANCHOR_FWD + perp_x * ts * MOUTH_ANCHOR_SIDE
        my = head_c[1] + dy * ts * MOUTH_ANCHOR_FWD + perp_y * ts * MOUTH_ANCHOR_SIDE

        # Subtle face shadow under mouth sprite.
        sw = max(2, int(rot.get_width() * MOUTH_SHADOW_SCALE))
        sh = max(2, int(rot.get_height() * MOUTH_SHADOW_SCALE * 0.45))
        mouth_shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(mouth_shadow, (0, 0, 0, FACE_SHADOW_ALPHA), mouth_shadow.get_rect())
        self.window.blit(mouth_shadow, (int(mx - sw // 2), int(my - sh // 2 + ts * 0.08)))

        rect = rot.get_rect(center=(int(mx), int(my)))
        self.window.blit(rot, rect.topleft)

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._last_fs_toggle_ms = pygame.time.get_ticks()
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        self._last_scale = None
        self._rebuild_overlay()

    # ── Main loop ─────────────────────────────────────────────────────────────
    def _main_loop(self):
        while True:
            self._handle_events()
            self._tick_if_due()
            self._update_collision_recoil()
            self._ensure_assets()
            self._draw()
            mouse_pos = pygame.mouse.get_pos()
            if ((self.x_rect  and self.x_rect.collidepoint(mouse_pos)) or
                (self.fs_rect and self.fs_rect.collidepoint(mouse_pos))):
                pygame.mouse.set_cursor(self.cursor_hand)
            else:
                pygame.mouse.set_cursor(self.cursor_default)
            self.clock.tick(FPS)

    # ── Input ─────────────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.x_rect and self.x_rect.collidepoint(event.pos):
                    pygame.quit(); exit()
                if event.button == 1 and self.fs_rect and self.fs_rect.collidepoint(event.pos):
                    self._toggle_fullscreen()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); exit()
                if event.key == pygame.K_f:
                    self._toggle_fullscreen(); return
                if event.key == pygame.K_r and self.game_state == "dead":
                    self.new_game(); return
                if self.game_state == "waiting" and event.key in DIR_KEYS:
                    start_dir = DIR_KEYS[event.key]
                    if start_dir == (-self.direction[0], -self.direction[1]):
                        return
                    now = pygame.time.get_ticks()
                    self.game_state     = "playing"
                    self.last_tick_ms   = now
                    self.direction      = start_dir
                    self.next_dir       = self.direction
                    self.prev_direction = self.direction
                    self.head_angle_deg = self._dir_to_angle(self.direction)
                    self.turn_from_deg  = self.head_angle_deg
                    self.turn_to_deg    = self.head_angle_deg
                    self.turn_start_ms  = now
                    self.turn_end_ms    = now
                    self._cancel_tongue_rattle(now, reschedule=True)
                    return
                if self.game_state == "playing" and event.key in DIR_KEYS:
                    self._enqueue_direction(DIR_KEYS[event.key])

    def _enqueue_direction(self, new_dir):
        base_dir = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir == (-base_dir[0], -base_dir[1]): return False
        if new_dir == base_dir: return False
        self.input_queue.append(new_dir)
        self.next_dir = new_dir
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

        self.prev_head = self.snake[0]
        self.prev_tail = self.snake[-1]   # ← kept: record before potential pop

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
        death_overlay_visible = (
            self.game_state == "dead" and
            now >= self.death_overlay_delay_until_ms
        )

        self.window.fill(HEADER_COLOUR)
        self._draw_header(lay, a)
        pygame.draw.rect(self.window, PANEL_COLOUR,
                         pygame.Rect(0, lay['header_h'],
                                     lay['win_w'], lay['win_h'] - lay['header_h']))
        self._draw_tiles(lay, a)
        self._draw_apple(lay, a)
        self._draw_snake(lay, a, progress, now)

        if self.game_state == "waiting":
            self._draw_waiting_overlay(lay)
        elif death_overlay_visible:
            self._draw_death_overlay(lay)

        overlay_active = self.game_state == "waiting" or death_overlay_visible
        for icon, rect in ((a['full_screen'], self.fs_rect), (a['x'], self.x_rect)):
            if rect is None: continue
            if overlay_active:
                bright = icon.copy()
                bright.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_ADD)
                self.window.blit(bright, (rect.x, rect.y))
            else:
                self.window.blit(icon, (rect.x, rect.y))

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
        gap    = int(10 * lay['sc'])
        x_x  = lay['win_w'] - margin - a['x'].get_width()
        x_y  = (lay['header_h'] - a['x'].get_height()) // 2
        fs_x = x_x - gap - a['full_screen'].get_width()
        fs_y = (lay['header_h'] - a['full_screen'].get_height()) // 2
        self.x_rect  = pygame.Rect(x_x,  x_y,  a['x'].get_width(),          a['x'].get_height())
        self.fs_rect = pygame.Rect(fs_x, fs_y, a['full_screen'].get_width(), a['full_screen'].get_height())

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

    # ─────────────────────────────────────────────────────────────────────────
    # WHY this fixes both problems:
    #
    # TAIL GLITCH (original bug):
    #   The original code drew two separate capsules from snake[-1]:
    #     (a) snake[-1] → ghost_tip   (old tail direction, shrinking)
    #     (b) snake[-1] → snake[-2]   (new body direction, full)
    #   At a corner these two capsules form a visible "Y" fork.
    #
    #   Fix: build a single polyline  ghost_tip → snake[-1] → … → head_c
    #   and sample circles along it.  snake[-1] is just a WAYPOINT — circles
    #   approach it from the old direction and leave it in the new direction.
    #   There is no fork because we never draw two separate primitives from the
    #   same node.
    #
    # GRADIENT:
    #   Every circle sample gets colour = mix(tail_colour, head_colour, frac)
    #   where frac = arc_dist / total_arc_length.  tail_colour starts equal to
    #   head_colour (invisible gradient) and darkens by APPLE_DARKEN_STEP each
    #   apple, capped at SNAKE_TAIL_DARK_MAX.
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_snake(self, lay, a, progress, now):
        n = len(self.snake)
        if n < 2:
            return

        cc = lambda gx, gy: self._cell_center(gx, gy, lay)
        r  = lay["body_r"]
        special_pose = None
        if self.game_state == "colliding" and self.collision_recoil:
            special_pose = {
                'segments': self.collision_recoil['base_segments'],
                'offset_tiles': self._collision_offset_tiles(now),
                'head_angle': self.collision_recoil['head_angle'],
            }
        elif self.game_state == "dead" and self.death_pose:
            special_pose = {
                'segments': self.death_pose['segments'],
                'offset_tiles': self.death_pose['offset_tiles'],
                'head_angle': self.death_pose['head_angle'],
            }

        if special_pose is not None:
            pts = self._build_pose_points(
                lay,
                special_pose['segments'],
                offset_tiles_xy=special_pose['offset_tiles'],
            )
            body = self._draw_snake_body(lay, pts)
            if body is None:
                return
            head_c = pts[-1]
            head_angle = special_pose['head_angle']
            self._draw_collision_effect(now)
            self._draw_death_face(head_c, head_angle, lay, now)
            return

        # ghost_tip: identical to original — lerps from prev_tail to snake[-1].
        # At progress=0 it sits at prev_tail (full tail extension visible).
        # At progress=1 it collapses onto snake[-1] (tail fully retracted).
        ghost_tip  = lerp_pt(cc(*self.prev_tail), cc(*self.snake[-1]), progress)
        head_c     = lerp_pt(cc(*self.prev_head),  cc(*self.snake[0]),  progress)
        head_angle = self._current_head_angle(now)

        # Single continuous polyline: ghost_tip → snake[n-1] → … → snake[1] → head_c
        # At a corner near the tail, ghost_tip is in the OLD direction from
        # snake[n-1], and snake[n-2] is in the NEW direction.  Since we sample
        # circles along the polyline (not draw two capsules), the path naturally
        # bends at snake[n-1] with no fork artefact.
        pts = [ghost_tip]
        for i in range(n - 1, 0, -1):
            pts.append(cc(*self.snake[i]))
        pts.append(head_c)

        # Cumulative arc-lengths (needed for gradient fraction and shadow)
        cum = [0.0]
        for i in range(1, len(pts)):
            cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i-1][0],
                                             pts[i][1] - pts[i-1][1]))
        total = cum[-1]
        if total < 1.0:
            return

        # ── Shadow (fast capsules — no colour needed) ──────────────────────
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

        # ── Gradient body — arc-length circle sampling ─────────────────────
        # frac 0.0 = tail tip (ghost_tip)  →  tail_colour
        # frac 1.0 = head tip              →  head_colour (always royal blue)
        head_colour = SNAKE_HEAD_COL
        tail_colour = mix_colour(SNAKE_HEAD_COL, SNAKE_TAIL_DARK_MAX, self.tail_darkness)

        # Step = 40 % of radius → tight overlap, zero banding, corners smooth
        STEP_PX = max(1.0, r * 0.40)

        for seg in range(len(pts) - 1):
            p0      = pts[seg]
            p1      = pts[seg + 1]
            seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if seg_len < 0.1:
                continue
            seg_from_head = (len(pts) - 2) - seg
            seg_r = self._radius_for_segment_from_head(seg_from_head, r)
            steps = max(1, int(math.ceil(seg_len / STEP_PX)))
            prev_pt = p0
            for s in range(1, steps + 1):
                t_local = s / steps
                cur_pt = (p0[0] + (p1[0] - p0[0]) * t_local,
                          p0[1] + (p1[1] - p0[1]) * t_local)
                mid_t = (s - 0.5) / steps
                arc_dist = cum[seg] + seg_len * mid_t
                frac = max(0.0, min(1.0, arc_dist / total))  # 0 = tail, 1 = head
                col = mix_colour(tail_colour, head_colour, frac)
                draw_capsule(self.window, col, prev_pt, cur_pt, seg_r)
                prev_pt = cur_pt

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
            self._draw_tongue_frame(head_c, head_angle, lay, self.tongue_frame_idx)
        self._draw_mouth_frame(head_c, head_angle, lay, self.mouth_frame_idx)
        self._update_eye_blink(now)
        self._draw_eyes(head_c, lay, head_angle)


    def _draw_eyes(self, head_c, lay, head_angle):
        dx, dy         = self._angle_vec(head_angle)
        perp_x, perp_y = -dy, dx
        ts = lay['tile_size']

        sprite = None
        if self._scaled_eye_frames:
            frame_idx = max(0, min(self.eye_frame_idx, len(self._scaled_eye_frames) - 1))
            sprite = self._scaled_eye_frames[frame_idx]
        apple_center = self._apple_center_screen(lay)

        pair_fwd = ts * EYE_CENTER_FWD
        pair_side = ts * EYE_CENTER_SIDE
        side_off = ts * EYE_SEPARATION
        left_eye = (
            head_c[0] + dx * pair_fwd + perp_x * (pair_side + side_off),
            head_c[1] + dy * pair_fwd + perp_y * (pair_side + side_off),
        )
        right_eye = (
            head_c[0] + dx * pair_fwd + perp_x * (pair_side - side_off),
            head_c[1] + dy * pair_fwd + perp_y * (pair_side - side_off),
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
                # The eye sheet's open frame looks right by default, so rotate
                # from that neutral orientation toward the apple.
                rot_deg = self._eye_track_rotation_deg((ex, ey), apple_center)
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


        for sign in (+1, -1):
            ex = head_c[0] + dx * fwd_off + perp_x * sign * side_off
            ey = head_c[1] + dy * fwd_off + perp_y * sign * side_off

            yoff = int(ts * FACE_SHADOW_YOFF_FACTOR * 0.10)
            sh_r = max(1, int(eye_r * 0.95))
            sh_sz = sh_r * 2 + 2
            eye_shadow = pygame.Surface((sh_sz, sh_sz), pygame.SRCALPHA)
            pygame.draw.circle(eye_shadow, (0, 0, 0, FACE_SHADOW_ALPHA), (sh_sz // 2, sh_sz // 2), sh_r)
            self.window.blit(eye_shadow, (int(ex - sh_sz // 2), int(ey + yoff - sh_sz // 2)))

            # Thin dark outline ring
            pygame.draw.circle(self.window, (20, 40, 100), (int(ex), int(ey)), outline_r)
            # White sclera
            pygame.draw.circle(self.window, EYE_WHITE, (int(ex), int(ey)), eye_r)

            # Clamp pupil inside white
            pdx = base_px + wob_x
            pdy = base_py + wob_y
            lim = max(0.0, eye_r - pup_r - 1)
            mag = math.hypot(pdx, pdy)
            if mag > lim and mag > 0:
                pdx = pdx / mag * lim
                pdy = pdy / mag * lim

            px = ex + pdx
            py = ey + pdy
            # Large dark pupil
            pygame.draw.circle(self.window, (15, 15, 25), (int(px), int(py)), pup_r)
            # Bright white highlight — upper-left of pupil
            hl_r = max(2, int(pup_r * 0.30))
            pygame.draw.circle(self.window, (255, 255, 255),
                               (int(px - pup_r * 0.38), int(py - pup_r * 0.38)), hl_r)

        # Two nostrils on the snout.
        snout_x   = head_c[0] + dx * ts * 0.34
        snout_y   = head_c[1] + dy * ts * 0.34
        nost_side = ts * 0.23
        nost_fwd  = ts * -0.25
        nost_r    = 1
        for sign in (+1, -1):
            nx = snout_x + dx * nost_fwd + perp_x * sign * nost_side
            ny = snout_y + dy * nost_fwd + perp_y * sign * nost_side
            pygame.draw.circle(self.window, NOSE_CLR, (int(nx), int(ny)), nost_r)

    def _draw_waiting_overlay(self, lay):
        self.window.blit(self.overlay, (0, 0))
        cx = lay['win_w'] // 2
        cy = lay['board_oy'] + lay['board_h'] // 2
        t1 = self.font_large.render("Snake", True, START_CLR)
        t2 = self.font_medium.render("Press any arrow key to start", True, HINT_CLR)
        self.window.blit(t1, t1.get_rect(center=(cx, cy - int(30 * lay['sc']))))
        self.window.blit(t2, t2.get_rect(center=(cx, cy + int(28 * lay['sc']))))

    def _draw_death_overlay(self, lay):
        self.window.blit(self.overlay, (0, 0))
        cx = lay['win_w'] // 2
        cy = lay['board_oy'] + lay['board_h'] // 2
        t1 = self.font_large.render("You Lost", True, LOST_CLR)
        t2 = self.font_small.render("Press R to Restart", True, HINT_CLR)
        self.window.blit(t1, t1.get_rect(center=(cx, cy - int(28 * lay['sc']))))
        self.window.blit(t2, t2.get_rect(center=(cx, cy + int(28 * lay['sc']))))


if __name__ == "__main__":
    print ('hello world')
    SnakeGame()
