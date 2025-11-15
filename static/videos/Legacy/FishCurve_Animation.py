from manim import *
from numpy import *

# Fish curve class
class Fishcurve(VMobject):
    def __init__(self, w=6, h=3, k=10, range = TAU,**kwargs):
        super().__init__(**kwargs)
        self.w = w
        self.h = h
        self.k = k
       
        step_size = 0.01
        theta = arange(-step_size, range, step_size)

        # Parametric equation of the Fish curve
        points = [
            [
                w * cos(k * t) - h * (sin(k * t))**2,
                w * cos(k * t) * sin(k * t),
                0
            ] for t in theta
        ]
        if len(points) > 1:
            self.set_points_smoothly(points)

class NEMO_Animation(Scene):

    def construct(self):
        
        #self.play(self.camera.frame.animate.shift(DOWN * 2), run_time=1)

        # Turning Background Transparent
        #self.camera.background_opacity = 0

        # White Background if needed
        self.camera.background_color = "#fdf6f1" 

        #Parameters
        f = 1.3
        w = 3*sqrt(2)*f; h = 3*f
        p = ValueTracker(0.001)
        x = ValueTracker(0)
        s = 0;

        #Ellipse elements
        ellipse = (
            Ellipse(width=w*2, height=h*2, color=BLUE, fill_opacity=0)
            .set_stroke(width=8, opacity=1)
        )
        focus = (
            Dot([3,0,0], color=GREEN)
            .set_stroke(width=2, opacity=1)
        )
        focus_out = (
            Dot([3,0,0], color='#cbdfbb' )
            .set_stroke(width=12, opacity=1)
        )
        moving_ellipse_point = always_redraw(
                lambda: Dot(
                    [
                        w*cos(TAU * (p.get_value())),
                        h*sin(TAU * (p.get_value())),
                        0
                    ],
                    color=GREEN
                ).set_stroke(width=2, opacity=1)
                .shift(UP*s)
        )
        moving_ellipse_point_out = always_redraw(
                lambda: Dot(
                    [
                        w*cos(TAU * (p.get_value())),
                        h*sin(TAU * (p.get_value())),
                        0
                    ],
                    color='#cbdfbb'
                ).set_stroke(width=12, opacity=1)
                .shift(UP*s)
        )
        moving_line = always_redraw(
            lambda: Line(
                start = focus.get_center(),
                end = [
                        w*cos(TAU * (p.get_value())),
                        h*sin(TAU * (p.get_value())),
                        0
                    ],
                    color=BLUE,
                ).set_stroke(width=6, opacity=1)
                .shift(UP*s)
        )

        #Fish elements
        fish = always_redraw(
            lambda: Fishcurve(
                w * (1-0.125*(x.get_value()) ),
                h * (1-0.125*(x.get_value()) ),
                1,
                TAU * (p.get_value())
            ).set_stroke(color=ORANGE, width=10, opacity=1)
             .shift(UP * (s + (2) * (x.get_value())))
        )
        moving_fish_point = always_redraw(
            lambda: Dot(
                    [
                        w * cos(TAU * (p.get_value() + 0.001)) - h * (sin(TAU * (p.get_value() + 0.001)))**2,
                        w * cos(TAU * (p.get_value() + 0.001)) * sin(TAU * (p.get_value() + 0.001)),
                        0
                    ],
                    color=GREEN,
                ).set_stroke(width=2, opacity=1)
                .shift(UP*s)
        )
        moving_fish_point_out = always_redraw(
            lambda: Dot(
                    [
                        w * cos(TAU * (p.get_value() + 0.001)) - h * (sin(TAU * (p.get_value() + 0.001)))**2,
                        w * cos(TAU * (p.get_value() + 0.001)) * sin(TAU * (p.get_value() + 0.001)),
                        0
                    ],
                    color='#cbdfbb',
                ).set_stroke(width=12, opacity=1)
                .shift(UP*s)
        )

        moving_slope = always_redraw(
            lambda: Line(
                start = moving_fish_point.get_center() - (moving_fish_point.get_center() - moving_ellipse_point.get_center()) *(100/linalg.norm(moving_fish_point.get_center() - moving_ellipse_point.get_center())),
                end = moving_ellipse_point.get_center() + (moving_fish_point.get_center() - moving_ellipse_point.get_center()) *(100/linalg.norm(moving_fish_point.get_center() - moving_ellipse_point.get_center())),
                color=BLUE
            ).set_stroke(width=6, opacity=1) if fish.has_points() else VMobject()
            .shift(UP*s)
        )

        elements = VGroup(ellipse, focus, focus_out).shift(UP*s)

        #NEMO Text
        Nemo_text = (
            MathTex(r"\mathbb{NEMO}", font_size=280, color=BLACK)
            .set_stroke(color=BLACK, width=0.5, opacity=1)
            .shift(DOWN*2.9 + UP*s) 
        )

        #Animating the Ellipse
        self.play(Create(ellipse), run_time=0.5)
        self.play(FadeIn(focus, moving_line, moving_ellipse_point, moving_slope), run_time=0.25)

        #Animating the Fish
        self.add(fish, focus_out, focus, moving_line, moving_ellipse_point_out, moving_ellipse_point, moving_slope, moving_fish_point_out, moving_fish_point)
        self.play(p.animate.set_value(1), run_time=2)

        # Getting the fish to the top and Animating the Text
        self.play(FadeOut(ellipse, moving_ellipse_point_out, moving_ellipse_point_out, moving_ellipse_point, moving_line, moving_slope, moving_fish_point_out, moving_fish_point, focus_out, focus), run_time=0.25)
        self.play(x.animate.set_value(0.6), run_time=0.75, rate_func=smooth)
        self.play(Write(Nemo_text), run_time=1)

        self.wait(2)