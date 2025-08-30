# Simple Render Queue

This is a script for cli-rendering with Blender on a single machine.

The queue is a simple text-file where each job is a line:

`/path/to/blenderfile.blend -c 1 -f 1-100, 150, 151`

Flags are:

- `-c` chunksize
- `-f` frames to render: ranges and single frames

The queue can be updated and changed.
After finishing a chunk, the script reads the file again and reacts to the changes.

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

## Running the script/demo

Run the script and specify the queue file:

```sh
python simple_render_queue.py q.render
```
