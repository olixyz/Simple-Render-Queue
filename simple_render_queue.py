import atexit
from os import listdir
from os.path import isfile, isdir, join, basename, splitext
from posixpath import dirname
import re
import subprocess
import sys
import time


class Simple_Queue:

    def __init__(self, q_file):
        self.q_file = q_file  # name of the render queue file
        self.sub_p = None  # the subprocess
        self.switches = {}  # store render switches
        self.last_job_index = -1
        self.use_global_chunksize = False
        self.chunksize = 1
        self.queue_raw_items = []  # each line describing a job as string
        self.frames_only_ending_on_mode = False
        atexit.register(self.__cleanup)
        self.render_cmd = None
        self.missing_frames_count = 0

    def run(self):
        self.__run()

    def __reset_after_chunk(self):
        self.sub_p.terminate()
        self.switches = {}  # store render switches
        self.use_global_chunksize = False
        self.chunksize = 1
        self.queue_raw_items = []  # each line describing a job as string
        self.frames_only_ending_on_mode = False
        self.render_cmd = None
        self.missing_frames_count = 0

    def list_images(self, folder, match_string):
        # This script needs the output folder relative to this python script
        found = []
        # Early return if folder does not exist
        if not isdir(folder):
            # print("output folder not found")
            return found

        for file in listdir(folder):
            if isfile(join(folder, file)) and file.startswith(match_string):
                # extract the frame number
                match = re.search(r"(\d+)(?=\.\w+$)", file)
                if match:
                    found.append(int(match.group(1)))
                    # print("Found frame number", int(match.group(1)))
        return found

    def find_missing_in_sequence(self, frames_list, found):
        missing = list(set(frames_list) - set(found))
        # print(len(missing), "missing frames")
        return missing

    def frames_list_from_string(self, frames_string):
        frames = []
        # split by ","
        f_split = frames_string.split(",")
        # split result by "-"
        for el in f_split:
            el_split = el.split("-")

            if len(el_split) == 2:
                # print("is range")
                # Make sure, first number is smaller than second number
                range_start = int(el_split[0])
                range_end = int(el_split[1]) + 1
                if range_start < range_end:
                    frames.extend(list(range(range_start, range_end)))
                else:
                    print("WARNING::Wrong frame range order! Ignoring...")
            else:
                frames.append(int(el))
        return frames

    def output_from_scenefile(self, scenefile_path):
        scenefile = basename(scenefile_path)
        scenefile_no_ext = splitext(scenefile)[0]

        # Output relative to blender file
        output_dir_blender_relative = join("//render", scenefile_no_ext)

        # Output relative to this script:
        output_dir_script_relative = join(
            dirname(scenefile_path), "render", scenefile_no_ext
        )

        output_file = join(output_dir_blender_relative, scenefile_no_ext + ".")

        return [
            output_dir_blender_relative,
            output_dir_script_relative,
            output_file,
            scenefile_no_ext,
        ]

    def __parse_switches(self, switches_raw):
        s = switches_raw.split(":")
        flags = s.pop()  # by default pop() passes -1 as index
        matches = re.findall(r"(-\w+)(?:\s+([^-\s][^-]*))?", flags)

        for m in matches:
            self.switches[m[0]] = m[1]

    def __check_frames_ending(self, number):
        if str(number).endswith(self.switches["-mod"]):
            return True
        return False

    def __process_queue(self):
        try:
            with open(self.q_file, "r") as f:
                for line in f.readlines():
                    # Ignore comments and empty lines
                    # Save switches seperately
                    if (
                        not line.startswith("#")
                        and line.strip()
                        and not line.startswith("switches:")
                    ):
                        self.queue_raw_items.append(line.strip())
                    if line.startswith("switches:"):
                        switches_raw = line.strip()
                        # s = line.split("switches:")
                        self.__parse_switches(switches_raw)
                        self.use_global_chunksize = True
                if not self.use_global_chunksize:
                    self.switches.clear()

                f.close()
        except OSError:
            # print("Could not open/read file:", self.q_file)
            time.sleep(1.0)
            self.__run()

        for index, q_item in enumerate(self.queue_raw_items):
            # if switch is set to jump, compare last rendered index with current index.
            # Continue to next item in queue if smaller or same
            # Start from top if at the end of queue
            if "-jump" in self.switches:
                if self.last_job_index == len(self.queue_raw_items) - 1:
                    # start from top: reset value to outside the list
                    self.last_job_index = -1
                if index <= self.last_job_index:
                    continue
            if "-c" in self.switches:
                self.chunksize = int(self.switches["-c"])
            if "-mod" in self.switches:
                self.frames_only_ending_on_mode = True

            scenepath_regex = r"^(.*?)(?= -c)"
            c_regex = r"(?<= -c )(.*?)(?= -f)"
            f_regex = r"(?<= -f )(.*)"

            scenepath = re.search(scenepath_regex, q_item).group(1)
            # Set chunksize from job if not set from switches
            if not self.use_global_chunksize:
                self.chunksize = int(re.search(c_regex, q_item).group(1))
            frames_as_string = re.search(f_regex, q_item).group(1)
            frames = self.frames_list_from_string(frames_as_string)

            [
                output_dir_blender_relative,
                output_dir_script_relative,
                output_file,
                image_name,
            ] = self.output_from_scenefile(scenepath)

            # Check output and find what is missing
            found = self.list_images(output_dir_script_relative, image_name)
            missing = self.find_missing_in_sequence(frames, found)
            self.missing_frames_count = len(missing)

            # If -mod flag is given:
            # goes through list of number after -mod flag
            # checks if missing frames end on number in list,
            # then renders them
            if self.frames_only_ending_on_mode:
                progression_list = self.switches["-mod"].split(",")
                for p in progression_list:
                    # check if list of missing frames contains
                    # any frames ending on p.
                    matching_frames_in_missing = []
                    for m in missing:
                        if str(m).endswith(p):
                            matching_frames_in_missing.append(m)

                    if len(matching_frames_in_missing):
                        missing = matching_frames_in_missing
                        break

            # use chunksize to create a chunk of renderable frames
            first_chunk = missing[: self.chunksize]
            self.last_job_index = index
            if len(first_chunk):
                self.render_cmd = "blender {} --background --factory-startup --python overrides.py --render-output {} --render-frame {}".format(
                    scenepath, output_file, ",".join(str(x) for x in first_chunk)
                )
                # Found a chunk to render
                break

    def __render(self):
        print("------------\nRENDERING:")
        print("Found", str(self.missing_frames_count), "missing frames")
        print(self.switches)
        print("Global chunksize: ", self.use_global_chunksize)
        print("\n".join(self.render_cmd.split()))
        self.sub_p = subprocess.Popen(
            self.render_cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # while True:
        #     line = self.sub_p.stdout.readline()
        #     if not line:
        #         break
        #     print(line)

        output, errors = self.sub_p.communicate()
        print("\nChunk done\n")

    def __run(self):
        done = False
        while not done:
            self.__process_queue()
            if type(self.render_cmd) == str:
                self.__render()
                self.__reset_after_chunk()
            # else:
            #     print("Job done")
            #     time.sleep(0.5)
            #     print("Next...")
            #     done = True

    def __cleanup(self):
        print("Cleanup...")
        try:
            self.sub_p.kill()
        except:
            print("No subprocess running")


if __name__ == "__main__":
    queue = sys.argv[1]
    render = Simple_Queue(queue)
    render.run()
