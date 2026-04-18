import math

import pygame


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
    dx = c2[0] - c1[0]
    dy = c2[1] - c1[1]
    dist = math.hypot(dx, dy)
    if dist < 0.5:
        return
    nx = -dy / dist * radius
    ny = dx / dist * radius
    pygame.draw.polygon(
        surface,
        colour,
        [
            (c1[0] + nx, c1[1] + ny),
            (c1[0] - nx, c1[1] - ny),
            (c2[0] - nx, c2[1] - ny),
            (c2[0] + nx, c2[1] + ny),
        ],
    )
