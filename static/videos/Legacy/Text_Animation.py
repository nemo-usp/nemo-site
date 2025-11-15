from manim import *
import math

class Text_Animation(Scene):

    def construct(self):
        # Set background to be transparent for the final output
        #self.camera.background_opacity = 0

        # White Background if needed
        #self.camera.background_color = "#fdf6f1"
        
        # Add a small buffer around the text to avoid cutting it off
        padding = 10  # pixels

        # Define your text object
        text_object = (
            MathTex(r"\text{FAQ}", font_size=120, color=BLACK)
            .set_stroke(color=BLACK, width=1, opacity=1)
        )

        text_object.move_to(ORIGIN)
        
        # --- Crop calculation logic ---
        # Get camera and text dimensions
        pix_height = self.camera.pixel_height
        pix_width = self.camera.pixel_width
        
        # Convert Manim units to pixels
        # Note: A Mobject's origin is its center
        w_pixels = text_object.width * self.camera.pixel_width / self.camera.frame_width
        h_pixels = text_object.height * self.camera.pixel_height / self.camera.frame_height

        # Calculate crop parameters for ffmpeg (w:h:x:y)
        w = math.ceil(w_pixels) + padding * 2
        h = math.ceil(h_pixels) + padding * 2
        # x and y are the top-left corner of the crop area
        x = math.floor((pix_width - w) / 2)
        y = math.floor((pix_height - h) / 2)

        # Print the crop info for the shell script to capture
        # The format is w:h:x:y
        print(f"CROP_INFO:{w}:{h}:{x}:{y}")
        # --- End of calculation logic ---

        self.play(Write(text_object), run_time=1)
        self.wait(1)