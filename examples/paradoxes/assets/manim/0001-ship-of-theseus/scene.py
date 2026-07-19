from manimlib import *

import numpy as np


PLANK_COUNT = 12
WOOD = "#D5A253"
WOOD_DARK = "#70502D"
REPLACEMENT = "#E05545"
GHOST = "#6D7883"
INK = "#F5F1E8"
MUTED = "#AAB3BA"
WATER = "#4DA6C8"


def make_planks(y, color=WOOD, opacity=1.0):
    planks = VGroup()
    xs = np.linspace(-4.25, 4.25, PLANK_COUNT)
    for x in xs:
        height = 1.28 - 0.035 * abs(x)
        plank = RoundedRectangle(
            width=0.69,
            height=height,
            corner_radius=0.06,
            stroke_color=WOOD_DARK if opacity > 0.2 else GHOST,
            stroke_width=2.0,
            fill_color=color,
            fill_opacity=opacity,
        )
        plank.move_to([x, y + 0.045 * x * x, 0])
        planks.add(plank)
    return planks


def ship_label(text, y, color=MUTED):
    return Text(text, font="Avenir Next", font_size=28, color=color).move_to([0, y, 0])


def mix_hex(start, end, amount):
    amount = min(1.0, max(0.0, float(amount)))
    first = tuple(int(start[index:index + 2], 16) for index in (1, 3, 5))
    second = tuple(int(end[index:index + 2], 16) for index in (1, 3, 5))
    mixed = tuple(round(a + (b - a) * amount) for a, b in zip(first, second))
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


class ShipOfTheseusLesson(Scene):
    random_seed = 0

    def construct(self):
        title = Text("THE SHIP OF THESEUS", font="Avenir Next", font_size=64, color=INK)
        question = Text("When every plank changes, what stays the same?", font="Avenir Next", font_size=32, color=MUTED)
        question.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(title, shift=0.25 * UP), FadeIn(question, shift=0.2 * UP), run_time=0.8)
        self.wait(0.8)
        self.play(FadeOut(title), FadeOut(question), run_time=0.45)

        current = make_planks(1.15)
        originals = make_planks(-2.0, opacity=0.10)
        current_label = ship_label("ONE CONTINUOUS HISTORY", 2.45)
        stored_label = ship_label("ORIGINAL PLANKS, STORED", -3.25)
        water_top = Line([-4.8, 0.48, 0], [4.8, 0.48, 0], color=WATER, stroke_width=3)
        water_bottom = Line([-4.8, -2.67, 0], [4.8, -2.67, 0], color=WATER, stroke_width=3).set_opacity(0.24)
        self.play(
            LaggedStartMap(FadeIn, current, lag_ratio=0.05),
            FadeIn(current_label),
            FadeIn(stored_label),
            ShowCreation(water_top),
            FadeIn(originals),
            FadeIn(water_bottom),
            run_time=1.0,
        )

        for top_plank, lower_plank in zip(current, originals):
            self.play(
                top_plank.animate.set_fill(REPLACEMENT, opacity=1).set_stroke(REPLACEMENT, width=2),
                lower_plank.animate.set_fill(WOOD, opacity=1).set_stroke(WOOD_DARK, width=2),
                run_time=0.20,
            )

        claim_top = ship_label("same ship by history", 0.15, color=REPLACEMENT)
        claim_bottom = ship_label("same ship by material", -3.55, color=WOOD)
        self.play(
            FadeOut(current_label),
            FadeOut(stored_label),
            FadeIn(claim_top),
            FadeIn(claim_bottom),
            water_bottom.animate.set_opacity(1),
            run_time=0.65,
        )
        tension = Text("One past. Two claimants.", font="Avenir Next", font_size=38, color=INK)
        tension.to_edge(UP, buff=0.25)
        self.play(FadeIn(tension, shift=0.15 * DOWN), run_time=0.55)
        self.wait(1.8)


class ShipOfTheseusLive(Scene):
    random_seed = 0

    def build_lumanim(self):
        self.current = make_planks(1.15)
        self.originals = make_planks(-2.0, opacity=0.10)
        self.current_label = ship_label("CONTINUOUS HISTORY", 2.45)
        self.original_label = ship_label("ORIGINAL MATERIAL", -3.25)
        self.tension = ship_label("ONE PAST. TWO CLAIMANTS.", 3.25, color=INK).set_opacity(0)
        self.history_claim = ship_label("same ship by history", 0.15, color=REPLACEMENT).set_opacity(0)
        self.material_claim = ship_label("same ship by material", -3.55, color=WOOD).set_opacity(0)
        self.water_top = Line([-4.8, 0.48, 0], [4.8, 0.48, 0], color=WATER, stroke_width=3)
        self.water_bottom = Line([-4.8, -2.67, 0], [4.8, -2.67, 0], color=WATER, stroke_width=3).set_opacity(0.24)
        self.add(
            self.current,
            self.originals,
            self.water_top,
            self.water_bottom,
            self.current_label,
            self.original_label,
            self.tension,
            self.history_claim,
            self.material_claim,
        )
        self.set_lumanim_state({"replacement_fraction": 0})

    def set_lumanim_state(self, state):
        fraction = float(state.get("replacement_fraction", 0))
        if not np.isfinite(fraction):
            raise ValueError("replacement_fraction must be finite")
        fraction = min(1.0, max(0.0, fraction))
        progress = fraction * PLANK_COUNT
        for index, (top_plank, lower_plank) in enumerate(zip(self.current, self.originals)):
            amount = min(1.0, max(0.0, progress - index))
            top_plank.set_fill(mix_hex(WOOD, REPLACEMENT, amount), opacity=1)
            top_plank.set_stroke(mix_hex(WOOD_DARK, REPLACEMENT, amount), width=2)
            lower_plank.set_fill(mix_hex(GHOST, WOOD, amount), opacity=0.10 + 0.90 * amount)
            lower_plank.set_stroke(mix_hex(GHOST, WOOD_DARK, amount), width=2)
        self.water_bottom.set_opacity(0.24 + 0.76 * fraction)
        endpoint = min(1.0, max(0.0, (fraction - 0.90) / 0.10))
        endpoint = endpoint * endpoint * (3 - 2 * endpoint)
        self.current_label.set_opacity(1 - endpoint)
        self.original_label.set_opacity(1 - endpoint)
        self.tension.set_opacity(endpoint)
        self.history_claim.set_opacity(endpoint)
        self.material_claim.set_opacity(endpoint)
