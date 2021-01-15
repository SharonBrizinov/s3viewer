import os
import subprocess
import tempfile

from PyQt5.QtCore import QObject, pyqtSignal

from utils import show_message_box, extract_domain
from nodefs import FSNode, parse_dirlist_line

class DirlistWorker(QObject):
    # Signals
    finished = pyqtSignal()
    progress = pyqtSignal(FSNode)

    def __init__(self, nodes_stats, root_node, provider, pre_generated_dirlist_path=None):
        super().__init__()
        # Data
        self.nodes_stats = nodes_stats
        self.root_node = root_node
        self.provider = provider
        self.pre_generated_dirlist_path = pre_generated_dirlist_path
        # Working modes
        self.is_offline = False # Should get dirlist
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
                raise Exception("Did not set provider for worker")

    def create_temp_dir(self):
        if not self.is_offline:
            # Create temp dir
            dirlist_name = self.provider.hostname() + ".dirlist.txt"
            self.working_dir = tempfile.mkdtemp()
            self.dirlist_path = os.path.join(self.working_dir, dirlist_name)
        else:
            self.dirlist_path = pre_generated_dirlist_path
            self.working_dir = os.path.dirname(os.path.abspath(self.dirlist_path))

    # Get dirlist
    def run(self):
        # Offline mode
        if self.is_offline:
            # TODO: support offline mode
            pass
        # Online mode
        else:
            for dirlist_line in self.provider.yield_dirlist():
                node = parse_dirlist_line(dirlist_line)
                # It's possible that new nodes will be created if one of the dirs
                #   in the hierarchy is new. For example in case we first encounter a new
                #   directory that we haven't processed before /new_dir/file
                new_nodes = self.root_node.process_sub_node(node) + [node]
                for new_node in new_nodes:
                    # TODO: Write to file <-----
                    self.nodes_stats.process_node(new_node)
                    self.progress.emit(new_node)
        self.finished.emit()