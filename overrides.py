import bpy

"""
print("Overrides")


def stamp_set(scene):
    print("Generating stamp")
    cycles = bpy.context.scene.cycles
    note = "-------------\nCustom data\n-------------"
    note += "\nSamples: " + str(cycles.samples)
    # note += "\nLook: "            + str(view_settings.look)
    # note += "\nExposure: "        + str(round(view_settings.exposure, 2))

    scene.render.stamp_note_text = note
    bpy.context.scene.render.use_stamp_note = True


bpy.app.handlers.render_pre.append(stamp_set)

# This script is applied to all jobs in the queue
cycles = bpy.context.scene.cycles
cycles.device = "GPU"

# bpy.context.scene.render.resolution_x = 1920
# bpy.context.scene.render.resolution_y = 1080
# bpy.context.scene.render.resolution_percentage = 100

cycles.use_adaptive_sampling = True
cycles.adaptive_threshold = 0.1
cycles.samples = 150
cycles.adaptive_min_samples = 0

cycles.use_denoising = True

cycles.diffuse_bounces = 4
cycles.glossy_bounces = 4
cycles.transparent_max_bounces = 6
cycles.transmission_bounces = 8

# .jpg preview
bpy.context.scene.render.image_settings.use_preview = True

# Metadata Burn In
bpy.context.scene.render.use_stamp_hostname = True
bpy.context.scene.render.use_stamp_memory = True
bpy.context.scene.render.use_stamp = True

"""
