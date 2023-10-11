import os
import tempfile
import time

from PyQt6.QtCore import QObject, pyqtSignal

from utils import decode_data
from nodefs import FSNode, parse_dirlist_line
from consts import DEFAULT_MAX_ITEMS


class DirlistWorker(QObject):
    # Signals
    finished = pyqtSignal()
    progress = pyqtSignal(FSNode)
    report_error = pyqtSignal(str)

    def __init__(self, nodes_stats, root_node, provider, max_items=DEFAULT_MAX_ITEMS, pre_generated_dirlist_path=None):
        super().__init__()
        # Stop and responsiveness
        self.should_stop = False
        self.counter_items_before_sleep = 1000 # for GUI to be more responsive
        self.seconds_sleep = 1 # for GUI to be more responsive
        # Data
        self.nodes_stats = nodes_stats
        self.root_node = root_node
        self.provider = provider
        self.pre_generated_dirlist_path = pre_generated_dirlist_path
        self.max_items = max_items
        self.current_items = 0
        # Working modes
        self.is_offline = False # Should get dirlist
        self.has_errors = False
        self.set_working_mode()
        # Working dirs
        self.working_dir = None
        self.dirlist_path = None
        self.create_temp_dir()

    def set_working_mode(self):
        # Offline mode
        if self.pre_generated_dirlist_path:
            self.is_offline = True
        else:
            # Online mode
            self.is_offline = False
            if not self.provider:
                raise Exception("Provider is not configured")

    def create_temp_dir(self):
        if not self.is_offline:
            # Create temp dir
            dirlist_name = self.provider.hostname() + ".dirlist.txt"
            self.working_dir = tempfile.mkdtemp()
            self.dirlist_path = os.path.join(self.working_dir, dirlist_name)
        else:
            self.dirlist_path = self.pre_generated_dirlist_path
            self.working_dir = os.path.dirname(os.path.abspath(self.dirlist_path))

    def stop(self):
        self.should_stop = True

    # Read from a an offline dirlist file
    def offline_mode_read_data(self):
        dirlist_lines = []
        try:
            with open(self.pre_generated_dirlist_path, "rb") as f:
                dirlist_data = decode_data(f.read())
                if not dirlist_data:
                    raise Exception("Could not decode dirlist. Are you sure your data is valid?")
                dirlist_lines = dirlist_data.splitlines()
        except Exception as e:
            self.has_errors = True
            self.report_error.emit(str(e))
        return dirlist_lines

    # Get dirlist
    def run(self):
        self.current_items = 1 # to avoid sleeping the first time
        dirlist_file = None

        # Get iterator
        if self.is_offline:
            data_iterator = iter(self.offline_mode_read_data())
        else:
            data_iterator = iter(self.provider.yield_dirlist())

        # Check for errors
        if self.has_errors:
            return

        try:
            dirlist_file = open(self.dirlist_path, "wb")

            for dirlist_line in data_iterator:
                # Should stop?
                if self.should_stop:
                    self.provider.stop()
                    break

                # GUI responsiveness
                if self.current_items % self.counter_items_before_sleep == 0:
                    time.sleep(self.seconds_sleep)

                if self.current_items - 1 >= self.max_items:
                    self.provider.stop()
                    break

                # Write to dirlist file if online
                if not self.is_offline:
                    dirlist_file.write(dirlist_line.encode())

                ### Process data ###
                # Parse line
                node = parse_dirlist_line(dirlist_line)

                # Make sure we don't have it yet
                if self.root_node.is_node_exists_yet(node):
                    continue

                # It's possible that new nodes will be created if one of the dirs
                #   in the hierarchy is new. For example in case we first encounter a new
                #   directory that we haven't processed before /new_dir/file
                new_nodes = self.root_node.process_sub_node(node) + [node]
                for new_node in new_nodes:
                    self.nodes_stats.process_node(new_node)
                    self.progress.emit(new_node)

                self.current_items += 1 # must be in the outter loop
        except Exception as e:
            self.has_errors = True
            self.report_error.emit(str(e))
            return
        finally:
            if not self.is_offline:
                dirlist_file.close()

        self.finished.emit()