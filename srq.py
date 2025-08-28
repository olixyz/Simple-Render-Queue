import atexit
from os import listdir
from os.path import isfile, isdir, join, basename, splitext
from posixpath import dirname
import re
import subprocess
import sys


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
        self.__process_queue()

    def __reset_after_chunk(self):
        self.sub_p.terminate()
        self.switches = {}  # store render switches
        self.use_global_chunksize = False
        self.chunksize = 1
        self.queue_raw_items = []  # each line describing a job as string
        self.frames_only_ending_on_mode = False

    def __list_images(self, folder, match_string):
        found = []
        # Early return if folder does not exist
        if not isdir(folder):
            return found

        for file in listdir(folder):
            if isfile(join(folder, file)) and file.startswith(match_string):
                # extract the frame number
                match = re.search(r"(\d+)(?=\.\w+$)", file)
                if match:
                    found.append(int(match.group(1)))
        return found

    def __find_missing_in_sequence(self, frames_list, found):
        missing = list(set(frames_list) - set(found))
        # print(len(missing), "missing frames")
        return missing

    def __frames_list_from_string(self, frames_string):
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

    def __output_from_scenefile(self, scenefile_path):
        # extract filename from path.
        scenefile = basename(scenefile_path)
        scenefile_no_ext = splitext(scenefile)[0]

        # By my convention, the take name is a suffix
        # appended to the filename after a dot:
        takename = scenefile_no_ext.split(".")[-1]

        # print(scenefile)
        # print(scenefile_no_ext)
        # print(takename)

        # By my convention, the output is next to the scenefile_path
        # in a folder called "render" and inside is a folder per take
        output_path = join(dirname(scenefile_path), "render", takename)

        # The finale image name is just the takename
        return [output_path, takename]

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
            frames = self.__frames_list_from_string(frames_as_string)

            # print("chunksize", chunksize)
            # print("frames\n", frames)

            [output_path, image_name] = self.__output_from_scenefile(scenepath)
            # print(output_path)
            # print(image_name)

            # Check output and find what is missing
            found = self.__list_images(output_path, image_name)
            missing = self.__find_missing_in_sequence(frames, found)

            # If -mod flag is given
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
            if len(first_chunk):
                # blender -b engine.96.take_text_main.blend -a 1001,1002,
                render_command = "blender {} --background --factory-startup --render-frame {}".format(
                    scenepath, ",".join(str(x) for x in first_chunk)
                )
                # print(render_command)
                # print("\n\n-------------------")

                self.last_job_index = index
                self.__render(render_command)

    def __render(self, cmd):
        print("------------\nRENDERING:")
        print(self.switches)
        print("Global chunksize: ", self.use_global_chunksize)
        print("\n".join(cmd.split()))
        self.sub_p = subprocess.Popen(
            cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # while True:
        #     line = sub_p.stdout.readline()
        #     if not line:
        #         break
        #     print(line)

        output, errors = self.sub_p.communicate()
        print("\nChunk done\n")

        self.__reset_after_chunk()
        self.__process_queue()

    def __cleanup(self):
        print("Cleanup...")
        try:
            self.sub_p.kill()
        except:
            print("No subprocess running")


if __name__ == "__main__":
    queue = sys.argv[1]
    render = Simple_Queue(queue)
