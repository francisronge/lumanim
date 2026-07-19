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
GHOST = "#303842"


def grain_positions():
    rows = (8, 7, 5, 3, 1)
    positions = []
    for row, length in enumerate(rows):
        y = -0.95 + row * 0.38
        for column in range(length):
            x = (column - (length - 1) / 2) * 0.35
            positions.append(np.array([x, y, 0]))
    return positions


def make_pile():
    grains = VGroup()
    for position in grain_positions():
        grain = Circle(
            radius=0.125,
            stroke_color=SAND_DARK,
            stroke_width=1.5,
            fill_color=SAND,
            fill_opacity=1,
        )
        grain.move_to(position + np.array([0, 0.45, 0]))
        grains.add(grain)
    return grains


def label(text, size=30, color=INK):
    return Text(text, font="Avenir Next", font_size=size, color=color)


def make_track():
    track = VGroup()
    xs = np.linspace(-5.3, 5.3, GRAIN_COUNT)
    for x in xs:
        segment = RoundedRectangle(
            width=0.32,
            height=0.16,
            corner_radius=0.04,
            stroke_color=GHOST,
            stroke_width=1,
            fill_color=GHOST,
            fill_opacity=1,
        ).move_to([x, -2.65, 0])
        track.add(segment)
    return track


class ForcedMarchLesson(Scene):
    random_seed = 0

    def construct(self):
        title = label("NOW REPEAT THE SAME STEP", 50)
        rule = label("HEAP(n)  →  HEAP(n − 1)", 31, CYAN)
        rule.next_to(title, DOWN, buff=0.28)
        self.play(FadeIn(title, shift=0.2 * UP), FadeIn(rule, shift=0.15 * UP), run_time=0.8)
        self.wait(0.8)
        self.play(title.animate.scale(0.65).to_edge(UP, buff=0.22), rule.animate.to_edge(UP, buff=0.92), run_time=0.65)

        pile = make_pile()
        track = make_track()
        count = label("24 GRAINS", 31, MUTED).move_to([0, 2.05, 0])
        verdict = label("HEAP", 48, GREEN).move_to([0, -1.25, 0])
        track_labels = VGroup(
            label("24", 20, MUTED).move_to([-5.3, -3.08, 0]),
            label("12", 20, MUTED).move_to([0.23, -3.08, 0]),
            label("1", 20, MUTED).move_to([5.3, -3.08, 0]),
        )
        self.play(LaggedStartMap(FadeIn, pile, lag_ratio=0.02), FadeIn(count), FadeIn(verdict), FadeIn(track), FadeIn(track_labels), run_time=1.0)

        track[0].set_fill(GREEN).set_stroke(GREEN)
        for step in range(1, GRAIN_COUNT):
            next_count = GRAIN_COUNT - step
            next_label = label(f"{next_count} GRAIN" + ("" if next_count == 1 else "S"), 31, MUTED)
            next_label.move_to(count)
            self.play(
                FadeOut(pile[-step], shift=0.18 * UP),
                ReplacementTransform(count, next_label),
                track[step].animate.set_fill(GREEN).set_stroke(GREEN),
                run_time=0.10,
            )
            count = next_label

        self.wait(0.35)
        verdict_question = label("HEAP?", 58, RED).move_to(verdict)
        endpoint = label("The harmless step has marched into a contradiction.", 31, INK)
        endpoint.to_edge(DOWN, buff=0.25)
        self.play(ReplacementTransform(verdict, verdict_question), track.animate.set_fill(RED).set_stroke(RED), run_time=0.55)
        self.play(FadeIn(endpoint, shift=0.15 * UP), run_time=0.55)
        self.wait(2.0)


class ForcedMarchLive(Scene):
    random_seed = 0

    def build_lumanim(self):
        self.title = label("REPEAT THE HARMLESS STEP", 35).to_edge(UP, buff=0.25)
        self.rule = label("HEAP(n)  →  HEAP(n − 1)", 26, CYAN).to_edge(UP, buff=0.82)
        self.pile = make_pile()
        self.track = make_track()
        self.count = label("24 GRAINS", 31, MUTED).move_to([0, 2.05, 0])
        self.verdict = label("HEAP", 48, GREEN).move_to([0, -1.25, 0])
        self.endpoint = label("One grain. Still a heap?", 31, RED).to_edge(DOWN, buff=0.25).set_opacity(0)
        self.add(self.title, self.rule, self.pile, self.track, self.count, self.verdict, self.endpoint)
        self.set_lumanim_state({"march_fraction": 0})

    def set_lumanim_state(self, state):
        fraction = float(state.get("march_fraction", 0))
        if not np.isfinite(fraction):
            raise ValueError("march_fraction must be finite")
        fraction = min(1.0, max(0.0, fraction))
        progress = fraction * (GRAIN_COUNT - 1)
        removed = int(np.floor(progress))
        partial = progress - removed
        visible = GRAIN_COUNT - removed

        for index, grain in enumerate(self.pile):
            removal_order = GRAIN_COUNT - 1 - index
            if removal_order < removed:
                opacity = 0
            elif removal_order == removed and removed < GRAIN_COUNT - 1:
                opacity = 1 - partial
            else:
                opacity = 1
            grain.set_fill(SAND, opacity=opacity).set_stroke(SAND_DARK, opacity=opacity)

        for index, segment in enumerate(self.track):
            amount = min(1.0, max(0.0, progress + 1 - index))
            color = interpolate_color(Color(GHOST), Color(GREEN), amount)
            segment.set_fill(color, opacity=1).set_stroke(color, opacity=1)

        shown_count = max(1, visible - (1 if partial >= 0.5 else 0))
        count_text = f"{shown_count} GRAIN" + ("" if shown_count == 1 else "S")
        new_count = label(count_text, 31, MUTED).move_to(self.count)
        self.count.become(new_count)
        endpoint = min(1.0, max(0.0, (fraction - 0.94) / 0.06))
        self.endpoint.set_opacity(endpoint)
        self.verdict.set_color(interpolate_color(Color(GREEN), Color(RED), endpoint))
