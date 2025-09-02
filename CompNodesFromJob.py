import re
import os
import bpy


def __output_from_scenefile(scenefile_path):
    scenefile = os.path.basename(scenefile_path)
    scenefile_no_ext = os.path.splitext(scenefile)[0]
    scenefile_dir = os.path.dirname(scenefile_path)
    output_dir = os.path.join(scenefile_dir, "render", scenefile_no_ext)
    output_file = os.path.join(output_dir, scenefile_no_ext + ".")

    return [output_dir, output_file, scenefile_no_ext]


def process_job(job_string):

    # Extract filepath (before any flags)
    filepath_match = re.match(r"^(\S+)", job_string)
    # Extract framerange behind -f flag
    f_match = re.search(r"-f\s+(\S+)", job_string)

    found_frame = None
    # takename = None
    framerange = []

    if f_match:
        range_as_string = f_match.group(1).split("-")
        framerange.append(int(range_as_string[0]))
        framerange.append(int(range_as_string[1]))

    if filepath_match:

        scenefile_path = filepath_match.group(1)
        [output_dir, output_file, scenefile_no_ext] = __output_from_scenefile(
            scenefile_path
        )

        # output_path = os.path.join(os.path.dirname(scenefile_path), "render", takename)
        found_frame = os.listdir(output_dir)[0]

        if found_frame:
            found_frame = os.path.join(output_dir, found_frame)

        if found_frame and len(framerange):
            compositing_nodes(found_frame, scenefile_no_ext, framerange)


def compositing_nodes(output, imagename, framerange):

    head_in = framerange[0]
    tail_out = framerange[1]

    # frame_padded = f"{head_in:04}"  # python >= 3.6
    # image_name = takename + "." + frame_padded + "." + extension
    # found_seq_full_path = os.path.join(output_path, image_name)
    # found_filename = os.path.basename(output)
    # found_name_only = file_seq.rsplit('/', 1)[1]

    node_group = bpy.data.node_groups.new(imagename, "CompositorNodeTree")
    node_group.use_fake_user = True
    # image = bpy.data.images.load(found_seq_full_path)
    print("Output:", output)
    image = bpy.data.images.load(output)

    image_node = node_group.nodes.new("CompositorNodeImage")

    image_node.image = image
    image.source = "SEQUENCE"
    image_node.frame_start = head_in
    image_node.frame_duration = tail_out - head_in
    image_node.label = imagename

    # need offset of -1 to line up
    image_node.frame_offset = framerange[0] - 1

    # Add One Alpha Over Node to limit the length
    aover_node_limit = node_group.nodes.new("CompositorNodeAlphaOver")

    # Add Two Alpha Over Nodes for fading with Animation and connect

    aover_nodeA = node_group.nodes.new("CompositorNodeAlphaOver")
    aover_nodeB = node_group.nodes.new("CompositorNodeAlphaOver")
    # Set Alpha Over Colors
    aover_node_limit.inputs[1].default_value = (0, 0, 0, 0)
    aover_node_limit.inputs[2].default_value = (0, 0, 0, 0)

    aover_nodeA.inputs[1].default_value = (0, 0, 0, 0)
    aover_nodeA.inputs[2].default_value = (0, 0, 0, 0)

    aover_nodeB.inputs[1].default_value = (0, 0, 0, 0)
    aover_nodeB.inputs[2].default_value = (0, 0, 0, 0)

    # Add Keyframes
    aover_node_limit.inputs[0].default_value = 1
    aover_node_limit.inputs[0].keyframe_insert("default_value", frame=head_in)
    aover_node_limit.inputs[0].keyframe_insert("default_value", frame=tail_out)
    aover_node_limit.inputs[0].default_value = 0
    aover_node_limit.inputs[0].keyframe_insert("default_value", frame=head_in - 1)
    aover_node_limit.inputs[0].keyframe_insert("default_value", frame=tail_out + 1)

    aover_nodeA.inputs[0].default_value = 0
    aover_nodeA.inputs[0].keyframe_insert("default_value", frame=head_in)
    aover_nodeA.inputs[0].keyframe_insert("default_value", frame=tail_out)
    aover_nodeA.inputs[0].default_value = 1
    aover_nodeA.inputs[0].keyframe_insert("default_value", frame=head_in + 20)
    aover_nodeA.inputs[0].keyframe_insert("default_value", frame=tail_out - 20)

    aover_nodeB.inputs[0].default_value = 1
    aover_nodeB.inputs[0].keyframe_insert("default_value", frame=head_in)
    aover_nodeB.inputs[0].keyframe_insert("default_value", frame=tail_out)
    aover_nodeB.inputs[0].default_value = 0
    aover_nodeB.inputs[0].keyframe_insert("default_value", frame=head_in + 20)
    aover_nodeB.inputs[0].keyframe_insert("default_value", frame=tail_out - 20)

    # Align Nodes
    image_node.location.x = 0
    aover_node_limit.location.x = 200
    aover_nodeA.location.x = 400
    aover_nodeB.location.x = 400
    aover_nodeB.location.y = -250

    if __name__ == "__main__":
        # Uses the q.render job description,
        # but only accepts one range after "-f" flag: e.g. "-f 1-100"
        # It does not accept list with single frames or combined ranges and single frames!

        # Specify path to directory of .blend files that were used for rendering:
        local = "/path/to/render_files"

        output_1 = "scene_1.blend -c 1 -f 1001-1200"
        output_2 = "scene_2.blend -c 1 -f 1100-1150"

        load = [output_1, output_2]

        for job in load:
            process_job(os.path.join(local, job))
