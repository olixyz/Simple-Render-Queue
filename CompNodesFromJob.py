import re
import os
import bpy


def process_job(job_string):

    # Extract filepath (before any flags)
    filepath_match = re.match(r"^(\S+)", job_string)
    # Extract framerange behind -f flag
    f_match = re.search(r"-f\s+(\S+)", job_string)

    found_frame = None
    takename = None
    framerange = []

    if f_match:
        range_as_string = f_match.group(1).split("-")
        framerange.append(int(range_as_string[0]))
        framerange.append(int(range_as_string[1]))

    if filepath_match:
        scenefile_path = filepath_match.group(1)
        # extract filename from path.
        scenefile = os.path.basename(scenefile_path)
        scenefile_no_ext = os.path.splitext(scenefile)[0]

        # By my convention, the take name is a suffix
        # appended to the filename after a dot:
        takename = scenefile_no_ext.split(".")[-1]

        # By my convention, the output is next to the scenefile_path
        # in a folder called "render" and inside is a folder per take
        output_path = os.path.join(os.path.dirname(scenefile_path), "render", takename)
        found_frame = os.listdir(output_path)[0]
        if found_frame:
            found_frame = os.path.join(output_path, found_frame)

    if found_frame and takename and len(framerange):
        compositing_nodes(found_frame, takename, framerange)


def compositing_nodes(output, takename, framerange):

    head_in = framerange[0]
    tail_out = framerange[1]

    # frame_padded = f"{head_in:04}"  # python >= 3.6
    # image_name = takename + "." + frame_padded + "." + extension
    # found_seq_full_path = os.path.join(output_path, image_name)
    # found_filename = os.path.basename(output)
    # found_name_only = file_seq.rsplit('/', 1)[1]

    node_group = bpy.data.node_groups.new(takename, "CompositorNodeTree")
    node_group.use_fake_user = True
    # image = bpy.data.images.load(found_seq_full_path)
    print("Output:", output)
    image = bpy.data.images.load(output)

    image_node = node_group.nodes.new("CompositorNodeImage")

    image_node.image = image
    image.source = "SEQUENCE"
    image_node.frame_start = head_in
    image_node.frame_duration = tail_out - head_in
    image_node.label = takename

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
    # This does not accept list with single frames or combined ranges and single frames!
    # Use the line given by takes.log, e.g.:
    # "/home/oliver/dev/bl_takes_dev/output/objects/objects.take_cone.blend -c 1 -f 1-100"
    #
    job = "/home/oliver/dev/bl_takes_dev/output/objects/objects.take_cone.blend -c 1 -f 1-100"
    process_job(job)
