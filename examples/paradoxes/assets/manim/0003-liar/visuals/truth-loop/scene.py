from manimlib import *

import numpy as np


INK = "#F5F1E8"
MUTED = "#AAB3BA"
CYAN = "#58C4DD"
GREEN = "#83C167"
RED = "#E65A4F"
GHOST = "#303842"
CARD = "#1A2129"


def label(text, size=30, color=INK):
    return Text(text, font="Avenir Next", font_size=size, color=color)


def sentence_card(scale=1.0):
    card = RoundedRectangle(
        width=8.4 * scale,
        height=1.25 * scale,
        corner_radius=0.15,
        stroke_color=MUTED,
        stroke_width=2,
        fill_color=CARD,
        fill_opacity=1,
    )
    text = label("THIS SENTENCE IS FALSE", int(39 * scale), INK).move_to(card)
    return VGroup(card, text)


def value_node(text, color, position):
    circle = Circle(radius=0.72, stroke_color=color, stroke_width=4, fill_color=color, fill_opacity=0.08)
    circle.move_to(position)
    word = label(text, 34, color).move_to(circle)
    return VGroup(circle, word)


def truth_arrows():
    true_to_false = Arrow([-2.25, -0.3, 0], [2.25, -0.3, 0], color=RED, stroke_width=6)
    true_to_false.shift(0.28 * UP)
    false_to_true = Arrow([2.25, -1.55, 0], [-2.25, -1.55, 0], color=GREEN, stroke_width=6)
    false_to_true.shift(0.28 * DOWN)
    return true_to_false, false_to_true


class TruthLoopLesson(Scene):
    random_seed = 0

    def construct(self):
        card = sentence_card().to_edge(UP, buff=0.38)
        true_node = value_node("TRUE", GREEN, [-3.25, -0.9, 0])
        false_node = value_node("FALSE", RED, [3.25, -0.9, 0])
        top_arrow, bottom_arrow = truth_arrows()
        top_reason = label("what it says", 24, RED).next_to(top_arrow, UP, buff=0.12)
        bottom_reason = label("then its claim is correct", 24, GREEN).next_to(bottom_arrow, DOWN, buff=0.12)

        self.play(FadeIn(card, shift=0.15 * UP), run_time=0.65)
        self.play(FadeIn(true_node), FadeIn(false_node), run_time=0.65)

        assume_true = label("ASSUME TRUE", 29, GREEN).to_edge(DOWN, buff=0.38)
        self.play(FadeIn(assume_true), true_node.animate.scale(1.12), run_time=0.5)
        self.play(ShowCreation(top_arrow), FadeIn(top_reason), false_node.animate.scale(1.12), run_time=0.8)

        assume_false = label("ASSUME FALSE", 29, RED).move_to(assume_true)
        self.play(
            ReplacementTransform(assume_true, assume_false),
            true_node.animate.scale(1 / 1.12),
            run_time=0.45,
        )
        self.play(ShowCreation(bottom_arrow), FadeIn(bottom_reason), true_node.animate.scale(1.12), run_time=0.8)

        for _ in range(2):
            self.play(Indicate(false_node, color=RED), run_time=0.42)
            self.play(Indicate(true_node, color=GREEN), run_time=0.42)

        conclusion = label("NO STABLE CLASSICAL VALUE", 36, INK).move_to(assume_false)
        self.play(ReplacementTransform(assume_false, conclusion), run_time=0.6)
        self.wait(2.0)


class TruthLoopLive(Scene):
    random_seed = 0

    def build_lumanim(self):
        self.card = sentence_card(scale=0.92).to_edge(UP, buff=0.38)
        self.true_node = value_node("TRUE", GREEN, [-3.25, -0.9, 0])
        self.false_node = value_node("FALSE", RED, [3.25, -0.9, 0])
        self.top_arrow, self.bottom_arrow = truth_arrows()
        self.caption = label("ASSUME TRUE  →  THE SENTENCE FORCES FALSE", 28, INK).to_edge(DOWN, buff=0.35)
        self.add(
            self.card,
            self.true_node,
            self.false_node,
            self.top_arrow,
            self.bottom_arrow,
            self.caption,
        )
        self.set_lumanim_state({"assumption": 1})

    def set_lumanim_state(self, state):
        assumption = float(state.get("assumption", 1))
        if not np.isfinite(assumption):
            raise ValueError("assumption must be finite")
        assume_true = assumption >= 0.5

        self.true_node[0].set_fill(GREEN, opacity=0.24 if assume_true else 0.04)
        self.false_node[0].set_fill(RED, opacity=0.24 if not assume_true else 0.04)
        self.top_arrow.set_opacity(1 if assume_true else 0.16)
        self.bottom_arrow.set_opacity(0.16 if assume_true else 1)
        caption_text = (
            "ASSUME TRUE  →  WHAT IT SAYS FORCES FALSE"
            if assume_true
            else "ASSUME FALSE  →  ITS CLAIM IS CORRECT  →  TRUE"
        )
        caption_color = RED if assume_true else GREEN
        self.caption.become(label(caption_text, 28, caption_color).to_edge(DOWN, buff=0.35))
