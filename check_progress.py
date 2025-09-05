from simple_render_queue import Simple_Queue
import re
import sys


class Check_Progress:
    def __init__(self, queue):
        self.q_file = queue
        self.queue_raw_items = []
        self.SQ = Simple_Queue(self.q_file)

    def run(self):
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

                f.close()
        except OSError:
            print("Could not open/read file:", self.q_file)
            exit()

        for index, q_item in enumerate(self.queue_raw_items):

            scenepath_regex = r"^(.*?)(?= -c)"
            # c_regex = r"(?<= -c )(.*?)(?= -f)"
            f_regex = r"(?<= -f )(.*)"

            scenepath = re.search(scenepath_regex, q_item).group(1)
            frames_as_string = re.search(f_regex, q_item).group(1)
            frames = self.SQ.frames_list_from_string(frames_as_string)
            frames_count = len(frames)

            [
                output_dir_blender_relative,
                output_dir_script_relative,
                output_file,
                image_name,
            ] = self.SQ.output_from_scenefile(scenepath)

            # Check output and find what is missing
            found = self.SQ.list_images(output_dir_script_relative, image_name)
            missing = self.SQ.find_missing_in_sequence(frames, found)
            missing_frames_count = len(missing)
            missing_normalized = float(missing_frames_count) / float(frames_count)
            done_normalized = 1.0 - missing_normalized
            done_percent = done_normalized * 100.0

            message = "{}% Done |  {} of {} frames missing | {}".format(
                "%.2f" % round(done_percent, 2),
                missing_frames_count,
                frames_count,
                scenepath,
            )
            print(message)


if __name__ == "__main__":
    queue = sys.argv[1]
    check = Check_Progress(queue)
    check.run()
