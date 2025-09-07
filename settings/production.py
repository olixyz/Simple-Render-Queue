import bpy
import os

cycles = bpy.context.scene.cycles


def stamp_set(scene):
    note = os.path.basename(__file__)
    note += "\nSamples: " + str(cycles.samples)
    scene.render.stamp_note_text = note
    bpy.context.scene.render.use_stamp_note = True


# Metadata Burn In
# bpy.app.handlers.render_pre.append(stamp_set)
# bpy.context.scene.render.use_stamp_hostname = True
# bpy.context.scene.render.use_stamp_memory = True
# bpy.context.scene.render.use_stamp = True

cycles.device = "GPU"

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.resolution_percentage = 100

cycles.use_adaptive_sampling = True
cycles.adaptive_threshold = 0.01
cycles.samples = 200
cycles.adaptive_min_samples = 0

cycles.use_denoising = False

cycles.diffuse_bounces = 4
cycles.glossy_bounces = 4
cycles.transparent_max_bounces = 6
cycles.transmission_bounces = 8

# .jpg preview
# bpy.context.scene.render.image_settings.use_preview = True
