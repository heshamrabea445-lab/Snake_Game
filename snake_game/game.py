import math
import os
import random
from collections import deque

import pygame

from .bootstrap import attach_bootstrap_methods
from .constants import *
from .helpers import (
    angle_lerp_shortest,
    draw_capsule,
    ease_out_quad,
    lerp,
    lerp_pt,
    mix_colour,
    smoothstep,
)


class SnakeGame:

    def __init__(self):
        # Bring up just enough pygame state to paint the first frame quickly.
        # Audio comes up immediately after that first visible frame.
        pygame.display.init()
        pygame.font.init()
        self.base_dir = self._resolve_asset_root()
        self._configure_window()
        self._init_runtime_state()
        self._bootstrap_game()
        self._main_loop()

    # ── Startup ───────────────────────────────────────────────────────────────
    def _get_scale(self):
        ww, wh = self.window.get_size()
        return min(ww / BASE_W, wh / BASE_H)

    def _scale_surface(self, surf, scale, base_w, base_h=None):
        if base_h is None:
            base_h = base_w
        size = (max(1, int(base_w * scale)), max(1, int(base_h * scale)))
        if size == surf.get_size():
            return surf
        return pygame.transform.smoothscale(surf, size)

    def _scale_surface_fit_width(self, surf, scale, base_w):
        target_w = max(1, int(base_w * scale))
        target_h = max(1, int(surf.get_height() * target_w / surf.get_width()))
        size = (target_w, target_h)
        if size == surf.get_size():
            return surf
        return pygame.transform.smoothscale(surf, size)

    def _scale_surface_fit_box(self, surf, scale, max_w, max_h=None):
        if max_h is None:
            max_h = max_w
        iw, ih = surf.get_size()
        fit_scale = min(max_w * scale / iw, max_h * scale / ih)
        size = (max(1, int(iw * fit_scale)), max(1, int(ih * fit_scale)))
        if size == surf.get_size():
            return surf
        return pygame.transform.smoothscale(surf, size)

    def _build_scaled_assets(self, scale):
        full_screen_raw = self._raw["full_screen"]
        full_screen_icon_bounds = self._crop_alpha_bounds(full_screen_raw)
        volume_icon_max_h = 21
        if full_screen_icon_bounds is not None:
            volume_icon_max_h = full_screen_icon_bounds.get_height() + 2

        return {
            "tile_light": self._scale_surface(self._raw["tile_light"], scale, TILE_SIZE_BASE),
            "tile_dark": self._scale_surface(self._raw["tile_dark"], scale, TILE_SIZE_BASE),
            "trophy": self._scale_surface(self._raw["trophy"], scale, 44),
            "apple_icon": self._scale_surface(self._raw["apple_icon"], scale, 44),
            "apple_board": self._scale_surface(self._raw["apple_icon"], scale, TILE_SIZE_BASE),
            "snake_card": self._scale_surface_fit_width(self._raw["snake_card"], scale, STARTER_CARD_BASE_W),
            "play_button": self._scale_surface_fit_width(self._raw["play_button"], scale, STARTER_CARD_BASE_W),
            "start_box": self._scale_surface_fit_width(self._raw["start_box"], scale, WAITING_CUE_ICON_BASE_W),
            "x": self._scale_surface_fit_box(self._raw["x"], scale, 40, 40),
            "full_screen": self._scale_surface_fit_box(full_screen_raw, scale, 40, 40),
            "not_full_screen": self._scale_surface_fit_box(self._raw["not_full_screen"], scale, 40, 40),
            "volume": self._scale_surface_fit_box(self._raw["volume"], scale, 40, volume_icon_max_h),
            "volume_muted": self._scale_surface_fit_box(self._raw["volume_muted"], scale, 40, volume_icon_max_h),
        }

    def _ensure_assets(self):
        scale = self._get_scale()
        ww, wh = self.window.get_size()
        size_changed = (ww, wh) != self._last_win_size
        scale_changed = scale != self._last_scale
        if not scale_changed and not size_changed:
            return
        if size_changed:
            self._last_win_size = (ww, wh)
        if scale_changed:
            self._last_scale = scale
            self._scaled_assets = self._build_scaled_assets(scale)
            self._refresh_scaled_animation_assets(scale)
            self._rebuild_fonts(scale)

    def _rebuild_fonts(self, scale):
        """Build fonts at the given scale.

        Using a direct file path is much faster than SysFont, which must
        scan the entire system font registry on every call.  Falls back
        to SysFont on non-Windows machines or if the files are missing.
        """
        font_path      = "C:/Windows/Fonts/arial.ttf"
        font_bold_path = "C:/Windows/Fonts/arialbd.ttf"
        try:
            if not os.path.exists(font_path) or not os.path.exists(font_bold_path):
                raise FileNotFoundError
            self.font_large  = pygame.font.Font(font_bold_path, max(8, int(52 * scale)))
            self.font_medium = pygame.font.Font(font_bold_path, max(8, int(30 * scale)))
            self.font_small  = pygame.font.Font(font_path,      max(8, int(26 * scale)))
            self.font_score  = pygame.font.Font(font_bold_path, max(8, int(34 * scale)))
        except Exception:
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

    def _head_motion_progress(self):
        """Return 0..1 progress from last crossed cell to the next."""
        if self.game_state != "playing":
            return 0.0
        if not hasattr(self, "head_float") or not hasattr(self, "last_head_cell"):
            return 0.0

        dx, dy = self.direction
        if dx > 0:
            p = self.head_float[0] - self.last_head_cell[0]
        elif dx < 0:
            p = self.last_head_cell[0] - self.head_float[0]
        elif dy > 0:
            p = self.head_float[1] - self.last_head_cell[1]
        else:
            p = self.last_head_cell[1] - self.head_float[1]
        return max(0.0, min(1.0, float(p)))

    def _collision_shake_offset_px(self, now_ms, lay):
        if now_ms >= self.collision_shake_end_ms:
            return (0.0, 0.0)
        dur = max(1, self.collision_shake_end_ms - self.collision_shake_start_ms)
        t = max(0.0, min(1.0, (now_ms - self.collision_shake_start_ms) / dur))
        decay = (1.0 - t) * (1.0 - t)
        amp = lay['tile_size'] * COLLISION_SHAKE_AMPLITUDE_TILES * decay
        phase = math.tau * t
        sx = math.sin(phase * COLLISION_SHAKE_X_CYCLES + 0.35) * amp
        sy = math.sin(phase * COLLISION_SHAKE_Y_CYCLES + 1.10) * amp * 0.80
        return (sx, sy)

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

    def _advance_growth_reveal(self, moved_tiles):
        moved = max(0.0, float(moved_tiles))
        if moved <= 0.0 or self.growth_hidden_tiles <= 0.0:
            return
        reveal = moved * GROWTH_REVEAL_TILES_PER_TILE
        self.growth_hidden_tiles = max(0.0, self.growth_hidden_tiles - reveal)

    def _radius_for_segment_from_head(self, seg_from_head, base_r):
        # Keep the spawn-length body uniform; only extra grown length tapers.
        min_r = max(1, int(base_r * TAIL_MIN_RADIUS_FACTOR))
        taper_seg_from_head = max(0.0, float(seg_from_head) - float(START_SNAKE_SEGMENTS - 1))
        rr = float(base_r) - taper_seg_from_head * SEGMENT_SHRINK_PER_SEG
        return max(min_r, int(rr))

    def _radius_for_arc_from_head_px(self, arc_from_head_px, tile_size, base_r):
        ts = max(1.0, float(tile_size))
        seg_from_head = max(0.0, float(arc_from_head_px) / ts)
        return self._radius_for_segment_from_head(seg_from_head, base_r)

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
        t = t * t * (3.0 - 2.0 * t)   # smoothstep easing
        self.head_angle_deg = angle_lerp_shortest(self.turn_from_deg, self.turn_to_deg, t)
        return self.head_angle_deg

    def _start_head_turn(self, new_dir, now_ms):
        self.turn_from_deg = self._current_head_angle(now_ms)
        self.turn_to_deg   = self._dir_to_angle(new_dir)
        self.turn_start_ms = now_ms
        # Duration matches the Bézier arc traversal so the head face
        # sweeps at the same rate the body curves.
        arc_tiles = 0.45 * 2.0          # pre + post corner radius
        turn_ms = int(arc_tiles * 1000.0 / self.move_speed)
        self.turn_end_ms = now_ms + max(50, turn_ms)

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
        dx, dy = self.direction
        if kind == "border":
            return (
                attempted_head[0] - dx * BORDER_CONTACT_INSET_TILES,
                attempted_head[1] - dy * BORDER_CONTACT_INSET_TILES,
            )
        elif kind == "self":
            return (
                attempted_head[0] - dx * 0.6,
                attempted_head[1] - dy * 0.6,
            )
        return attempted_head

    def _reset_recoil_path_history(self):
        self.recoil_path_history = deque(reversed(self.snake))
        self._trim_recoil_path_history()

    def _trim_recoil_path_history(self):
        keep_cells = max(2, len(self.snake) + COLLISION_PATH_EXTRA_CELLS)
        while len(self.recoil_path_history) > keep_cells:
            self.recoil_path_history.popleft()

    def _snapshot_recoil_path_tiles(self):
        # Build a tile-space retrace path from the current movement trail so
        # collision recoil follows the live track instead of snapping to cells.
        retrace_path = []
        for i in range(len(self.body_path) - 1, -1, -1):
            bx, by = self.body_path[i]
            retrace_path.append((float(bx), float(by)))

        # Extend with older grid history so one-tile recoil still works even on
        # very short snakes or after rapid recent turns.
        history_path = list(reversed(self.recoil_path_history))
        tail_ref = retrace_path[-1] if retrace_path else None
        start_idx = 0
        if tail_ref is not None:
            for i, (hx, hy) in enumerate(history_path):
                if abs(float(hx) - tail_ref[0]) <= 1e-6 and abs(float(hy) - tail_ref[1]) <= 1e-6:
                    start_idx = i + 1
                    break
        retrace_path.extend((float(hx), float(hy)) for hx, hy in history_path[start_idx:])

        if not retrace_path:
            retrace_path = [(float(self.snake[0][0]), float(self.snake[0][1]))]

        compact = [retrace_path[0]]
        for pt in retrace_path[1:]:
            if math.hypot(pt[0] - compact[-1][0], pt[1] - compact[-1][1]) > 1e-6:
                compact.append(pt)
        return compact

    def _record_recoil_path_head(self, new_head):
        self.recoil_path_history.append(new_head)
        self._trim_recoil_path_history()

    def _build_recoil_points(
        self,
        lay,
        impact_head_tile,
        retrace_path_tiles,
        visible_length,
        progress,
        *,
        tail_trim_px=0.0,
    ):
        progress = max(0.0, min(1.0, progress))
        if not retrace_path_tiles:
            return [], None, self._dir_to_angle(self.direction)
        visible_length = max(1, min(visible_length, len(retrace_path_tiles)))

        impact_head_px = self._cell_center(impact_head_tile[0], impact_head_tile[1], lay)
        live_head_px = self._cell_center(retrace_path_tiles[0][0], retrace_path_tiles[0][1], lay)
        contact_dist_px = math.hypot(
            live_head_px[0] - impact_head_px[0],
            live_head_px[1] - impact_head_px[1],
        )
        tail_extension_tiles = COLLISION_BACKUP_TILES

        path_tiles = [impact_head_tile] + list(retrace_path_tiles)
        if len(retrace_path_tiles) >= 2:
            tail_x, tail_y = retrace_path_tiles[-1]
            prev_x, prev_y = retrace_path_tiles[-2]
            tail_step = (tail_x - prev_x, tail_y - prev_y)
            tail_extension = (
                tail_x + tail_step[0] * tail_extension_tiles,
                tail_y + tail_step[1] * tail_extension_tiles,
            )
        else:
            tail_extension = retrace_path_tiles[-1]
        path_tiles.append(tail_extension)
        path_px = [self._cell_center(gx, gy, lay) for gx, gy in path_tiles]

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
        # Recoil to tile-center spacing: first back to the current live head
        # center, then one additional full tile along the retrace.
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
        if len(pts) >= 3:
            pts = self._smooth_path_corners(pts, lay['tile_size'] * 0.45)
            head_c = pts[-1]

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
            'retrace_path_tiles': list(recoil['retrace_path_tiles']),
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
            + DEATH_FACE_ANCHOR_BACK_SHIFT
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
        up_collision_y_nudge = ts * DEATH_FACE_UP_COLLISION_Y_NUDGE_TILES if dy < 0.0 else 0.0
        face_target = (
            head_c[0] + dx * ts * anchor_fwd,
            head_c[1] + dy * ts * anchor_fwd + vertical_lift + up_collision_y_nudge,
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

        self._play_collision_sfx()
        self.game_state = "colliding"
        self.high_score = max(self.high_score, self.score)
        self.input_queue.clear()
        self.next_dir = self.direction
        retrace_path = self._snapshot_recoil_path_tiles()
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
            'retrace_path_tiles': retrace_path,
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
        self.collision_shake_start_ms = now_ms
        self.collision_shake_end_ms = now_ms + COLLISION_SHAKE_DURATION_MS
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
        """Return the centre of the mouth region in the lower half of *surf*.

        Uses the C-level get_bounding_rect() instead of per-pixel Python
        iteration for a large speed-up during sprite sheet processing.
        """
        w, h = surf.get_size()
        y_start = max(0, min(h - 1, int(h * 0.45)))

        sub  = surf.subsurface((0, y_start, w, h - y_start))
        rect = sub.get_bounding_rect(min_alpha=1)

        if rect.width <= 0 or rect.height <= 0:
            return (w / 2.0, h / 2.0)

        # Translate the sub-surface rect back to full-surface coordinates.
        min_x = rect.left
        max_x = rect.right - 1
        min_y = rect.top + y_start
        max_y = rect.bottom - 1 + y_start

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
        """Split a horizontal mouth sprite strip into individual frames.

        Frames are separated by fully transparent columns.  Each column
        is tested with a 1-pixel-wide subsurface + get_bounding_rect()
        instead of iterating pixels in Python.
        """
        frames = []
        w, h = strip.get_size()
        run_start = None

        for x in range(w):
            column = strip.subsurface((x, 0, 1, h))
            has_alpha = column.get_bounding_rect(min_alpha=1).height > 0

            if has_alpha and run_start is None:
                run_start = x
            elif not has_alpha and run_start is not None:
                frame = pygame.Surface((x - run_start, h), pygame.SRCALPHA)
                frame.blit(strip, (0, 0), pygame.Rect(run_start, 0, x - run_start, h))
                cropped = self._crop_alpha_bounds(frame)
                if cropped is not None:
                    frames.append(cropped)
                run_start = None

        # Capture the last frame if the strip doesn't end with a gap.
        if run_start is not None:
            frame = pygame.Surface((w - run_start, h), pygame.SRCALPHA)
            frame.blit(strip, (0, 0), pygame.Rect(run_start, 0, w - run_start, h))
            cropped = self._crop_alpha_bounds(frame)
            if cropped is not None:
                frames.append(cropped)

        return frames

    def _compute_frame_open_amounts(self, frames):
        """Return a 0..1 openness ratio for each mouth frame.

        Uses pygame.mask.from_surface() to count opaque pixels in C
        rather than looping with get_at() in Python.
        """
        if not frames:
            return []

        alpha_counts = [pygame.mask.from_surface(frame, 0).count()
                        for frame in frames]

        max_alpha = max(alpha_counts, default=0)
        if max_alpha <= 0:
            return [0.0] * len(alpha_counts)
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
        self.pending_growth = 0
        self._reset_overlay_state()
        self.snake, self.apple = self._build_starting_positions()
        now_ms = pygame.time.get_ticks()
        self._reset_movement_state(now_ms)
        self._reset_animation_state(now_ms)

    def _build_starting_positions(self):
        cx, cy = GRID_COLS // 2, GRID_ROWS // 2
        head_x = cx - (START_SNAKE_SEGMENTS + 1)
        snake = [(head_x - offset, cy) for offset in range(START_SNAKE_SEGMENTS)]
        apple = (cx + 3, cy)
        return snake, apple

    def _reset_movement_state(self, now_ms):
        self.direction = RIGHT
        self.next_dir = RIGHT
        self.input_queue = deque(maxlen=4)
        self.start_move_locked = False
        self.prev_head = self.snake[0]
        self.prev_tail = self.snake[-1]
        self.prev_direction = self.direction
        self.last_frame_ms = now_ms
        self.head_angle_deg = self._dir_to_angle(self.direction)
        self.turn_from_deg = self.head_angle_deg
        self.turn_to_deg = self.head_angle_deg
        self.turn_start_ms = now_ms
        self.turn_end_ms = now_ms
        # ── Continuous movement state ──
        self.head_float = [float(self.snake[0][0]), float(self.snake[0][1])]
        self.move_speed = 1000.0 / TICK_RATE   # tiles per second
        self.body_path = deque()
        self._rebuild_body_path()
        self.last_head_cell = self.snake[0]
        self._last_turn_cell = None

    def _reset_animation_state(self, now_ms):
        self._apple_pulse_frozen = 1.0
        self.mouth_phase = 0.0
        self.mouth_target_open = False
        self.mouth_last_update_ms = now_ms
        self.mouth_frame_idx = 0
        self.mouth_close_delay_until_ms = 0
        self.tongue_anim_active = False
        self.tongue_anim_phase = 0.0
        self.tongue_anim_dir = 1
        self.tongue_last_update_ms = now_ms
        self.tongue_frame_idx = 0
        self.tongue_next_rattle_ms = now_ms
        self._schedule_next_tongue_rattle(now_ms)
        self.eye_blink_active = False
        self.eye_frame_idx = 0
        self.eye_last_update_ms = now_ms
        self.eye_next_blink_ms = now_ms
        self._schedule_next_eye_blink(now_ms)
        self.bulges = []
        self.growth_hidden_tiles = 0.0
        self.collision_shake_start_ms = 0
        self.collision_shake_end_ms = 0
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
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        self._set_window_icon()
        self._last_scale = None

    # ── Main loop ─────────────────────────────────────────────────────────────
    def _run_frame(self):
        self._refresh_starter_card_visibility()
        self._handle_events()
        self._tick_if_due()
        self._update_collision_recoil()
        self._ensure_assets()
        self._draw()
        self._update_cursor()

    def _update_cursor(self):
        mouse_pos = pygame.mouse.get_pos()
        interactive_rects = (
            self.x_rect,
            self.fs_rect,
            self.vol_rect,
            self.play_button_rect,
        )
        if any(rect and rect.collidepoint(mouse_pos) for rect in interactive_rects):
            pygame.mouse.set_cursor(self.cursor_hand)
        else:
            pygame.mouse.set_cursor(self.cursor_default)

    def _main_loop(self):
        while True:
            self._run_frame()
            self.clock.tick(FPS)

    # ── Input ─────────────────────────────────────────────────────────────────
    def _handle_mouse_button_down(self, event):
        if event.button != 1:
            return False
        if self.x_rect and self.x_rect.collidepoint(event.pos):
            self._quit_game()
        if self.fs_rect and self.fs_rect.collidepoint(event.pos):
            self._toggle_fullscreen()
            return True
        if self.vol_rect and self.vol_rect.collidepoint(event.pos):
            self._toggle_audio_mute()
            return True
        if (
            self.starter_card_visible and
            self.play_button_rect and
            self.play_button_rect.collidepoint(event.pos)
        ):
            self._handle_starter_card_play()
            return True
        return False

    def _handle_key_down(self, event):
        if event.key == pygame.K_ESCAPE:
            self._quit_game()
        if event.key == pygame.K_f:
            self._toggle_fullscreen()
            return True
        if (
            event.key == pygame.K_r and
            self.game_state == "waiting" and
            self.starter_card_visible and
            self.starter_card_context == "launch"
        ):
            self._show_waiting_start_cue()
            return True
        if event.key == pygame.K_r and self.game_state == "dead":
            self.trophy_unlocked_after_restart = (
                self.trophy_unlocked_after_restart
                or self.score > 0
            )
            self.new_game()
            return True
        if self.starter_card_visible:
            return False
        if self.game_state == "waiting" and event.key in DIR_KEYS:
            return self._start_waiting_run(DIR_KEYS[event.key])
        if self.game_state == "playing" and event.key in DIR_KEYS:
            self._enqueue_direction(DIR_KEYS[event.key])
            return True
        return False

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit_game()
            if event.type == pygame.MOUSEBUTTONDOWN and self._handle_mouse_button_down(event):
                return
            if event.type == pygame.KEYDOWN and self._handle_key_down(event):
                return

    def _enqueue_direction(self, new_dir):
        """Queue a direction change.  Multiple rapid inputs are buffered
        so back-to-back turns (e.g. UP then LEFT) execute in sequence
        at successive cell centres."""
        if self.start_move_locked:
            return False

        # The effective direction is whatever the snake will be heading
        # AFTER all already-queued turns have fired.
        if self.input_queue:
            effective_dir = self.input_queue[-1]
        else:
            effective_dir = self.direction

        if new_dir == (-effective_dir[0], -effective_dir[1]):
            return False
        if new_dir == effective_dir:
            return False

        if len(self.input_queue) >= self.input_queue.maxlen:
            return False

        # Add to the queue. The turn will strictly execute at the required
        # future cell crossing. This matches standard grid-locked snake
        # (like Google Snake) and prevents ANY visual glitching, snapping,
        # or shifting.
        self.input_queue.append(new_dir)
        return True

    # ── Continuous movement helpers ──────────────────────────────────────────

    def _rebuild_body_path(self):
        """Rebuild body_path from the current snake cell list (tail→head)."""
        self.body_path = deque()
        for i in range(len(self.snake) - 1, -1, -1):
            self.body_path.append((float(self.snake[i][0]), float(self.snake[i][1])))

    def _tick_if_due(self):
        """Advance the snake continuously each frame instead of per-tick."""
        if self.game_state != "playing":
            return
        now = pygame.time.get_ticks()
        dt_ms = now - self.last_frame_ms
        self.last_frame_ms = now
        dt_ms = max(0, min(dt_ms, 50))          # cap to prevent huge jumps
        if dt_ms <= 0:
            return
        dist = self.move_speed * (dt_ms / 1000.0)
        self._advance_head(dist)

    def _advance_head(self, dist):
        """Move the head forward by *dist* grid-units, executing any
        queued turn exactly at the cell centre it crosses so the
        visual path never jumps."""
        if dist <= 0 or self.game_state != "playing":
            return

        start_remaining = dist
        remaining = dist
        while remaining > 1e-9 and self.game_state == "playing":
            dx, dy = self.direction
            # Next cell centre along the current direction.
            ncx = self.last_head_cell[0] + dx
            ncy = self.last_head_cell[1] + dy

            # Signed distance to that centre.
            if dx > 0:
                d2c = ncx - self.head_float[0]
            elif dx < 0:
                d2c = self.head_float[0] - ncx
            elif dy > 0:
                d2c = ncy - self.head_float[1]
            else:
                d2c = self.head_float[1] - ncy
            d2c = max(0.0, d2c)

            # ── Early Registration for Collisions ──
            COLLISION_TRIGGER_BORDER_D2C = BORDER_CONTACT_INSET_TILES
            COLLISION_TRIGGER_SELF_D2C = 0.6
            is_collision = False
            col_kind = None
            trigger_d2c = 0.0

            if not (0 <= ncx < GRID_COLS and 0 <= ncy < GRID_ROWS):
                is_collision = True
                col_kind = "border"
                trigger_d2c = COLLISION_TRIGGER_BORDER_D2C
            elif (ncx, ncy) in self.snake[:-1]:
                is_collision = True
                col_kind = "self"
                trigger_d2c = COLLISION_TRIGGER_SELF_D2C

            if is_collision:
                dist_to_col = max(0.0, d2c - trigger_d2c)
                if remaining >= dist_to_col:
                    self.head_float[0] += dx * dist_to_col
                    self.head_float[1] += dy * dist_to_col
                    self._begin_collision_recoil(col_kind, (ncx, ncy))
                    break

            # ── Early Registration for Apples ──
            APPLE_TRIGGER_D2C = 0.7
            is_apple_next = (self.apple is not None and (ncx, ncy) == self.apple)
            if is_apple_next:
                dist_to_apple = max(0.0, d2c - APPLE_TRIGGER_D2C)
                if remaining >= dist_to_apple:
                    self.score      += 1
                    self.high_score  = max(self.high_score, self.score)
                    self.tail_darkness = min(1.0, self.tail_darkness + APPLE_DARKEN_STEP)
                    self._play_eat_sfx()
                    self._spawn_bulge()
                    self._spawn_apple()
                    self.pending_growth = getattr(self, 'pending_growth', 0) + 1

            if remaining < d2c:
                # Won't reach the next cell centre this step.
                self.head_float[0] += dx * remaining
                self.head_float[1] += dy * remaining
                remaining = 0.0
                break

            # ── Head reached the next cell centre ─────────────────
            # Place head exactly at the centre.
            self.head_float[0] = float(ncx)
            self.head_float[1] = float(ncy)
            remaining -= d2c

            # Snap perpendicular axis to prevent floating-point drift.
            if dx != 0:
                self.head_float[1] = float(round(self.head_float[1]))
            else:
                self.head_float[0] = float(round(self.head_float[0]))

            cp = (float(ncx), float(ncy))
            self.body_path.append(cp)
            self.last_head_cell = (ncx, ncy)
            self._on_enter_new_cell((ncx, ncy))

            if self.game_state != "playing":
                break

            # Apply the next queued turn at this cell centre.
            if self.input_queue:
                queued = self.input_queue.popleft()
                # Guard against stale queue entries that became reverses.
                if queued != (-self.direction[0], -self.direction[1]):
                    now_ms = pygame.time.get_ticks()
                    self.prev_direction = self.direction
                    self.direction = queued
                    self.next_dir = queued
                    self.start_move_locked = False
                    self._last_turn_cell = (ncx, ncy)
                    self._start_head_turn(self.direction, now_ms)
                    self._play_turn_sfx()

        moved_tiles = max(0.0, start_remaining - remaining)
        self._advance_growth_reveal(moved_tiles)

    def _on_enter_new_cell(self, new_cell):
        """Game logic when the head enters a new grid cell."""
        # ── Collision ──
        if not (0 <= new_cell[0] < GRID_COLS and 0 <= new_cell[1] < GRID_ROWS):
            self._begin_collision_recoil("border", new_cell)
            return
        if new_cell in self.snake[:-1]:
            self._begin_collision_recoil("self", new_cell)
            return

        self.prev_head = self.snake[0]
        self.prev_tail = self.snake[-1]
        self.snake.insert(0, new_cell)
        self.start_move_locked = False
        self._record_recoil_path_head(new_cell)

        if getattr(self, 'pending_growth', 0) > 0:
            self.pending_growth -= 1
            # Keep game-state growth immediate but reveal it smoothly in render.
            self.growth_hidden_tiles += 1.0
        elif new_cell == self.apple:
            self.score      += 1
            self.high_score  = max(self.high_score, self.score)
            self.tail_darkness = min(1.0, self.tail_darkness + APPLE_DARKEN_STEP)
            self._play_eat_sfx()
            self._spawn_bulge()
            self._spawn_apple()
        else:
            self.snake.pop()

        # Advance bulges on cell entry (replaces per-tick bulge stepping).
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

        # Trim body_path memory.
        max_pts = len(self.snake) * 3 + 20
        while len(self.body_path) > max_pts:
            self.body_path.popleft()

    def _smooth_path_corners(self, pts, radius):
        """Replace right-angle corners with smooth quadratic Bézier arcs."""
        if len(pts) < 3:
            return pts
        smoothed = [pts[0]]
        for i in range(1, len(pts) - 1):
            A = pts[i - 1]
            B = pts[i]
            C = pts[i + 1]
            ab = math.hypot(B[0] - A[0], B[1] - A[1])
            bc = math.hypot(C[0] - B[0], C[1] - B[1])
            if ab < 0.1 or bc < 0.1:
                smoothed.append(B)
                continue
            din = ((B[0] - A[0]) / ab, (B[1] - A[1]) / ab)
            dout = ((C[0] - B[0]) / bc, (C[1] - B[1]) / bc)
            dot = din[0] * dout[0] + din[1] * dout[1]
            if abs(dot) > 0.95:
                smoothed.append(B)
                continue
            off = min(radius, ab * 0.48, bc * 0.48)
            if off < 1.0:
                smoothed.append(B)
                continue
            p0 = (B[0] - din[0] * off, B[1] - din[1] * off)
            p2 = (B[0] + dout[0] * off, B[1] + dout[1] * off)
            ARC_STEPS = 8
            for j in range(ARC_STEPS + 1):
                t = j / ARC_STEPS
                mt = 1.0 - t
                smoothed.append((
                    mt * mt * p0[0] + 2 * mt * t * B[0] + t * t * p2[0],
                    mt * mt * p0[1] + 2 * mt * t * B[1] + t * t * p2[1],
                ))
        smoothed.append(pts[-1])
        return smoothed

    def _build_continuous_body_path(self, lay):
        """Build the tail→head polyline from the continuous body path."""
        n = len(self.snake)
        if n < 2:
            return [], None
        ts = lay['tile_size']
        hf = self.head_float
        head_px = (
            lay['board_ox'] + hf[0] * ts + ts / 2.0,
            lay['board_oy'] + hf[1] * ts + ts / 2.0,
        )
        # Backward path: head → body_path (newest→oldest)
        back = [head_px]
        for i in range(len(self.body_path) - 1, -1, -1):
            bx, by = self.body_path[i]
            back.append((
                lay['board_ox'] + bx * ts + ts / 2.0,
                lay['board_oy'] + by * ts + ts / 2.0,
            ))
        # Extension past the tail so the polyline is long enough.
        if len(back) >= 2:
            lx, ly = back[-1]
            px, py = back[-2]
            back.append((lx + (lx - px), ly + (ly - py)))

        # Cumulative arc-length.
        cum = [0.0]
        for i in range(1, len(back)):
            cum.append(cum[-1] + math.hypot(
                back[i][0] - back[i - 1][0],
                back[i][1] - back[i - 1][1]))
        total_path = cum[-1]
        visible_len_tiles = max(0.0, (n - 1) - self.growth_hidden_tiles)
        body_len = min(visible_len_tiles * ts, total_path)
        if body_len <= 0:
            return [head_px], head_px

        tail_px = self._sample_polyline_at_distance(back, cum, body_len)

        # Forward path: tail → interior → head.
        interior = [i for i in range(1, len(back) - 1)
                    if 0 < cum[i] < body_len]
        pts = [tail_px]
        for i in reversed(interior):
            pts.append(back[i])
        pts.append(head_px)

        # Deduplicate very close points.
        filtered = [pts[0]]
        for i in range(1, len(pts)):
            if math.hypot(pts[i][0] - filtered[-1][0],
                          pts[i][1] - filtered[-1][1]) > 0.5:
                filtered.append(pts[i])
        if filtered[-1] != pts[-1]:
            filtered.append(pts[-1])
        # Smooth every right-angle corner into a curved arc.
        corner_radius = ts * 0.45
        filtered = self._smooth_path_corners(filtered, corner_radius)
        return filtered, head_px

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        lay = self._layout()
        assets = self._scaled_assets
        now = pygame.time.get_ticks()
        progress = self._head_motion_progress()
        self.play_button_rect = None

        self.window.fill(HEADER_COLOUR)
        self._draw_header(lay, assets)
        pygame.draw.rect(self.window, PANEL_COLOUR,
                         pygame.Rect(0, lay['header_h'],
                                     lay['win_w'], lay['win_h'] - lay['header_h']))
        self._draw_tiles(lay, assets)
        self._draw_apple(lay, assets)
        self._draw_snake(lay, progress, now)

        shake_x, shake_y = self._collision_shake_offset_px(now, lay)
        board_rect = pygame.Rect(lay['board_ox'], lay['board_oy'], lay['board_w'], lay['board_h'])
        if abs(shake_x) > 0.01 or abs(shake_y) > 0.01:
            gameplay_lay = dict(lay)
            gameplay_lay['board_ox'] = lay['board_ox'] + int(round(shake_x))
            gameplay_lay['board_oy'] = lay['board_oy'] + int(round(shake_y))
            if board_rect.width > 0 and board_rect.height > 0:
                prev_clip = self.window.get_clip()
                self.window.set_clip(board_rect)
                self._draw_tiles(gameplay_lay, assets)
                self._draw_apple(gameplay_lay, assets)
                self._draw_snake(gameplay_lay, progress, now)
                self.window.set_clip(prev_clip)
            border_w = max(1, int(round(BOARD_BORDER_STROKE_BASE * lay['sc'])))
            border_rect = board_rect.inflate(border_w * 2, border_w * 2)
            pygame.draw.rect(self.window, PANEL_COLOUR, border_rect, border_w)
        self._draw_overlay(lay, assets)
        self._draw_window_controls(assets)
        pygame.display.flip()

    def _draw_overlay(self, lay, assets):
        if self.starter_card_visible:
            self._draw_starter_card_overlay(lay, assets)
            return
        if self.game_state == "waiting" and self.show_waiting_start_cue:
            self._draw_waiting_start_cue(lay, assets)

    def _draw_window_controls(self, assets):
        fullscreen_icon = assets['not_full_screen'] if self.fullscreen else assets['full_screen']
        volume_icon = assets['volume_muted'] if self.audio_muted else assets['volume']
        for icon, rect in (
            (fullscreen_icon, self.fs_rect),
            (volume_icon, self.vol_rect),
            (assets['x'], self.x_rect),
        ):
            if rect is None:
                continue
            draw_rect = icon.get_rect(center=rect.center)
            self.window.blit(icon, draw_rect.topleft)

    def _draw_header(self, lay, a):
        icon_x = int(12 * lay['sc'])
        icon_y = (lay['header_h'] - a['apple_icon'].get_height()) // 2
        self.window.blit(a['apple_icon'], (icon_x, icon_y))
        score_surf = self.font_score.render(str(self.score), True, SCORE_COLOUR)
        self.window.blit(score_surf, (
            icon_x + a['apple_icon'].get_width() + int(8 * lay['sc']),
            (lay['header_h'] - score_surf.get_height()) // 2))
        show_trophy = (
            self.trophy_unlocked_after_restart
            and
            self.high_score > 0
            and not (self.starter_card_visible and self.starter_card_context == "launch")
        )
        if show_trophy:
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
            steps = max(1, int(math.ceil(seg_len / step_px)))
            prev_pt = p0
            for s in range(1, steps + 1):
                t_local = s / steps
                cur_pt = (p0[0] + (p1[0] - p0[0]) * t_local,
                          p0[1] + (p1[1] - p0[1]) * t_local)
                mid_t = (s - 0.5) / steps
                arc_dist = cum[seg] + seg_len * mid_t
                arc_from_head = total - arc_dist
                seg_r = self._radius_for_arc_from_head_px(arc_from_head, lay['tile_size'], r)
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
                self.collision_recoil['retrace_path_tiles'],
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
                self.death_pose['retrace_path_tiles'],
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
        pts, head_c = self._build_continuous_body_path(lay)
        if not pts or head_c is None:
            return
        head_angle = self._current_head_angle(now)
        body = self._draw_snake_body(lay, pts)
        if body is None:
            return
        face_angle = head_angle   # smooth time-based lerp for live play
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
                    d = bulge['dist_px'] + smoothstep(progress) * bulge_speed_px
                arc_from_tail = total - d
                center = self._sample_polyline_at_distance(pts, cum, arc_from_tail)
                arc_from_head = max(0.0, min(total, total - arc_from_tail))
                local_r = self._radius_for_arc_from_head_px(arc_from_head, lay['tile_size'], r)
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
        apple_c = self._apple_center_screen(lay)

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
                if apple_c is not None:
                    look_vx = apple_c[0] - ex
                    look_vy = apple_c[1] - ey
                    if math.hypot(look_vx, look_vy) > 1e-6:
                        rot_deg = -math.degrees(math.atan2(look_vy, look_vx))
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




attach_bootstrap_methods(SnakeGame)

if __name__ == "__main__":
    SnakeGame()
