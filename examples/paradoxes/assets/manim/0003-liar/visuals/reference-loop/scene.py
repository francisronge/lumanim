from manimlib import *


INK = "#F5F1E8"
MUTED = "#AAB3BA"
CYAN = "#58C4DD"
RED = "#E65A4F"
CARD = "#1A2129"


def label(text, size=30, color=INK):
    return Text(text, font="Avenir Next", font_size=size, color=color)


def sentence_card():
    card = RoundedRectangle(
        width=9.6,
        height=1.8,
        corner_radius=0.18,
        stroke_color=MUTED,
        stroke_width=2,
        fill_color=CARD,
        fill_opacity=1,
    )
    subject = label("THIS SENTENCE", 46, CYAN)
    predicate = label("IS FALSE", 46, RED)
    words = VGroup(subject, predicate).arrange(RIGHT, buff=0.34).move_to(card)
    return VGroup(card, words), subject, predicate


class ReferenceLoopLesson(Scene):
    random_seed = 0

    def construct(self):
        title = label("WHAT DOES ‘THIS’ POINT TO?", 52)
        subtitle = label("First expose the reference.", 29, MUTED)
        subtitle.next_to(title, DOWN, buff=0.26)
        self.play(FadeIn(title, shift=0.2 * UP), FadeIn(subtitle, shift=0.15 * UP), run_time=0.8)
        self.wait(0.75)
        self.play(FadeOut(title), FadeOut(subtitle), run_time=0.45)

        card, subject, predicate = sentence_card()
        card.move_to([0, 0.8, 0])
        self.play(FadeIn(card[0]), FadeIn(subject), FadeIn(predicate), run_time=0.8)

        target = label("THE WHOLE SENTENCE", 34, CYAN).move_to([0, -1.8, 0])
        down = Arrow(subject.get_bottom() + 0.05 * DOWN, target.get_top() + 0.1 * UP, color=CYAN, stroke_width=5)
        back = Arrow(target.get_right() + 0.15 * RIGHT, card[0].get_bottom() + 2.2 * RIGHT, color=CYAN, stroke_width=5)
        self.play(subject.animate.scale(1.06), FadeIn(target, shift=0.1 * UP), ShowCreation(down), run_time=0.7)
        self.play(ShowCreation(back), card[0].animate.set_stroke(CYAN, width=4), run_time=0.7)

        caption = label("The subject loops back to the sentence containing it.", 31)
        caption.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(caption, shift=0.15 * UP), run_time=0.6)
        self.wait(2.0)
