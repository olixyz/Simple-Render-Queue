import bpy

print("Overrides")

# This script is applied to all jobs in the queue
cycles = bpy.context.scene.cycles
cycles.device = "GPU"

# bpy.context.scene.render.resolution_x = 1920
# bpy.context.scene.render.resolution_y = 1080
# bpy.context.scene.render.resolution_percentage = 100

cycles.use_adaptive_sampling = True
cycles.adaptive_threshold = 0.2
cycles.samples = 10
cycles.adaptive_min_samples = 0

cycles.use_denoising = False

cycles.diffuse_bounces = 4
cycles.glossy_bounces = 4
cycles.transparent_max_bounces = 6
cycles.transmission_bounces = 8
