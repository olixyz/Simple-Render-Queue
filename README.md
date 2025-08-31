# Simple Render Queue

This is a script for cli-rendering with Blender on a single machine.

The queue is a simple text-file where each job is a line:

`/path/to/blenderfile.blend -c 1 -f 1-100, 150, 151`

Flags are:

- `-c` chunksize
- `-f` frames to render: ranges and single frames

The queue can be updated and changed.
After finishing a chunk, the script reads the file again and reacts to the changes.

The script looks at the [output directories](#output-directories) of each job to figure out the list of missing frames.

## Global Switches

The queue can contain a line with global switches:

`switches: -jump -mod 0,5,2,8,1,9,3,7,4,6 -c 10`

- `-jump` jump to next job after finishing a chunk
- `-mod` only render frames that end on a number. This list is a progression: when all frames ending on `0` are rendered, continue with
  frames ending on `2`
- `-c` a global chunksize override

`-jump` combined with `-mod` is extremely helpful for getting frames of many passes/takes ready for compositing fast.

The compositing file could even be added as the last job in the queue and thereby output comped frames
for frames where all required pass/take frames are present.

## Stop Rendering

Interrupt the script with `CTRL c`. A cleanup function will terminate the render subprocess.

## Re-render frames

The script checks the image sequences in the output directories to figure out the list of missing frames.
If you want frames re-rendered, just delete them from the output.

## Output Directories

The output follows my own convention using _takes_ (variations of a scenefile, e.g. passes):

`directory_of_blendfile/render/takename/takename.####.fileext`

The _takename_ is the part of the filename after a `.` (_dot_).<br>

```sh
.
└── scenename/
    ├── render/
    │   ├── take_a/
    │   │   └── take_a.####.exr
    │   ├── take_b/
    │   │   └── take_b.####.exr
    │   └── take_c/
    │       └── take_c.####.exr
    ├── scenename.take_a.blend
    ├── scenename.take_b.blend
    └── scenename.take_c.blend
```

Example:<br>
`eng-010_010-anim-v100.take_beauty_all.blend`

The render output will be (in the directory of the .blend file) in:<br>
`./render/take_beauty_all/take_beauty_all.####.exr`

**This output needs to be set in the .blend file. It is not set by this script!**

## Running the script/demo

Run the script and specify the queue file:

```sh
python simple_render_queue.py q.render
```
