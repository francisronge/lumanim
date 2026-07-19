from manimlib import *

import numpy as np


GRAIN_COUNT = 24
SAND = "#F0C36A"
SAND_DARK = "#9A6B2F"
INK = "#F5F1E8"
MUTED = "#AAB3BA"
CYAN = "#58C4DD"
GREEN = "#83C167"
RED = "#E65A4F"


def grain_positions():
    rows = (8, 7, 5, 3, 1)
    positions = []
    for row, length in enumerate(rows):
        y = -1.25 + row * 0.39
        for column in range(length):
            x = (column - (length - 1) / 2) * 0.35
            positions.append(np.array([x, y, 0]))
    return positions


def make_pile(count, center):
    grains = VGroup()
    for position in grain_positions()[:count]:
        grain = Circle(
            radius=0.125,
            stroke_color=SAND_DARK,
            stroke_width=1.5,
            fill_color=SAND,
            fill_opacity=1,
        )
        grain.move_to(position + center)
        grains.add(grain)
    return grains


def label(text, size=30, color=INK):
    return Text(text, font="Avenir Next", font_size=size, color=color)


class HarmlessStepLesson(Scene):
    random_seed = 0

    def construct(self):
        title = label("THE HARMLESS STEP", 58)
        subtitle = label("Can one grain change the word?", 30, MUTED)
        subtitle.next_to(title, DOWN, buff=0.28)
        self.play(FadeIn(title, shift=0.2 * UP), FadeIn(subtitle, shift=0.15 * UP), run_time=0.8)
        self.wait(0.8)
        self.play(FadeOut(title), FadeOut(subtitle), run_time=0.45)

        left_center = np.array([-3.25, 0.5, 0])
        right_center = np.array([3.25, 0.5, 0])
        left = make_pile(GRAIN_COUNT, left_center)
        right = make_pile(GRAIN_COUNT - 1, right_center)
        left_count = label("24 GRAINS", 27, MUTED).move_to([-3.25, 2.55, 0])
        right_count = label("23 GRAINS", 27, MUTED).move_to([3.25, 2.55, 0])
        left_verdict = label("HEAP", 42, GREEN).move_to([-3.25, -1.55, 0])
        right_verdict = label("HEAP", 42, GREEN).move_to([3.25, -1.55, 0])

        self.play(LaggedStartMap(FadeIn, left, lag_ratio=0.025), FadeIn(left_count), run_time=0.9)
        self.play(FadeIn(left_verdict, shift=0.15 * UP), run_time=0.45)

        arrow = Arrow([-1.25, 0.5, 0], [1.25, 0.5, 0], color=CYAN, stroke_width=5)
        minus_one = label("− 1", 34, CYAN).next_to(arrow, UP, buff=0.18)
        removed = left[-1].copy()
        self.play(ShowCreation(arrow), FadeIn(minus_one), run_time=0.55)
        self.play(
            TransformFromCopy(left[:-1], right),
            removed.animate.move_to([0, 1.55, 0]).set_fill(RED).set_stroke(RED),
            FadeIn(right_count),
            run_time=1.0,
        )
        self.play(FadeOut(removed, shift=0.25 * UP), FadeIn(right_verdict, shift=0.15 * UP), run_time=0.55)

        rule = label("If n grains are a heap, n − 1 grains are a heap.", 31, INK)
        rule.to_edge(DOWN, buff=0.45)
        brace = Line([-5.2, -2.45, 0], [5.2, -2.45, 0], color=CYAN, stroke_width=3)
        self.play(ShowCreation(brace), FadeIn(rule, shift=0.15 * UP), run_time=0.7)
        self.wait(2.0)
