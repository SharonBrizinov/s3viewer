# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import urllib.request 
import shutil
from distutils.spawn import find_executable

from utils import *
from FSNode import *
from dirlist import *

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTreeWidgetItem, QApplication, QSpacerItem, QSizePolicy, QFrame
from PyQt5.QtGui import QIcon

# Get reference to running directory
RUNNING_DIR = os.path.dirname(os.path.abspath(__file__))
# PyInstaller - in case of PyInstaller the running directory is sys._MEIPASS
if hasattr(sys, '_MEIPASS'):
    RUNNING_DIR = sys._MEIPASS


class DirlistWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(FSNode)

    stats = FSNodeStats()
    root_node = FSNode("", None, 0)
    bucket_name = None

    def run(self):
        for dirlist_line in yield_aws_dirlist(self.bucket_name):
            node = parse_dirlist_line(dirlist_line)
            # It's possible that new nodes will be created if one of the dirs
            #   in the hierarchy is new. For example in case we first encounter a new
            #   directory that we haven't processed before /new_dir/file
            new_nodes = self.root_node.process_sub_node(node) + [node]
            for new_node in new_nodes:
                self.stats.process_node(new_node)
                self.progress.emit(new_node)
        self.finished.emit()


class Ui_MainWindow(QObject):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(686, 615)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit_bucket_name = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_bucket_name.setObjectName("lineEdit_bucket_name")
        self.horizontalLayout.addWidget(self.lineEdit_bucket_name)
        self.bucketNameButton = QtWidgets.QPushButton(self.centralwidget)
        self.bucketNameButton.setObjectName("bucketNameButton")
        self.horizontalLayout.addWidget(self.bucketNameButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_5.addWidget(self.label_3)
        self.lineEditDirlist = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditDirlist.setEnabled(True)
        self.lineEditDirlist.setObjectName("lineEditDirlist")
        self.horizontalLayout_5.addWidget(self.lineEditDirlist)
        self.buttonLoadData = QtWidgets.QPushButton(self.centralwidget)
        self.buttonLoadData.setObjectName("buttonLoadData")
        self.horizontalLayout_5.addWidget(self.buttonLoadData)
        self.buttonOpenDir = QtWidgets.QPushButton(self.centralwidget)
        self.buttonOpenDir.setObjectName("buttonOpenDir")
        self.horizontalLayout_5.addWidget(self.buttonOpenDir)
        self.verticalLayout.addLayout(self.horizontalLayout_5)

        # Seperator
        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape(QFrame.HLine)
        self.verticalLayout.addWidget(self.separatorLine)

        # Search
        self.horizontalLayout_Search = QtWidgets.QHBoxLayout()
        self.horizontalLayout_Search.setObjectName("horizontalLayout_Search")
        self.labelSearch = QtWidgets.QLabel(self.centralwidget)
        self.labelSearch.setObjectName("labelSearch")
        self.horizontalLayout_Search.addWidget(self.labelSearch)
        self.lineEditSearch = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditSearch.setEnabled(True)
        self.lineEditSearch.setObjectName("lineEditSearch")
        self.horizontalLayout_Search.addWidget(self.lineEditSearch)
        self.buttonSearchDo = QtWidgets.QPushButton(self.centralwidget)
        self.buttonSearchDo.setObjectName("buttonSearchDo")
        self.horizontalLayout_Search.addWidget(self.buttonSearchDo)
        self.buttonSearchClear = QtWidgets.QPushButton(self.centralwidget)
        self.buttonSearchClear.setObjectName("buttonSearchClear")
        self.horizontalLayout_Search.addWidget(self.buttonSearchClear)
        self.verticalLayout.addLayout(self.horizontalLayout_Search)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "Name")
        self.horizontalLayout_2.addWidget(self.treeWidget)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.labelStatistics = QtWidgets.QLabel(self.centralwidget)
        self.labelStatistics.setText("Please load S3 bucket")
        self.labelStatistics.setObjectName("labelStatistics")
        self.verticalLayout.addWidget(self.labelStatistics)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.labelStatus = QtWidgets.QLabel(self.centralwidget)
        self.labelStatus.setText("")
        self.labelStatus.setObjectName("labelStatus")
        self.verticalLayout.addWidget(self.labelStatus)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 686, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.bucketNameButton.clicked.connect(self.button_click_download_and_process_bucket_dirlist)
        self.buttonLoadData.clicked.connect(self.button_click_process_bucket_dirlist)
        self.buttonOpenDir.clicked.connect(self.button_click_open_working_dir)
        self.buttonSearchDo.clicked.connect(self.button_click_search_do)
        self.buttonSearchClear.clicked.connect(self.button_click_search_clear)
        self.treeWidget.doubleClicked['QModelIndex'].connect(self.treeViewFileDoubleClicked)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.working_dir = None
        self.selected_tree_item = None
        self.selected_tree_node = None
        self.current_bucket_name = None
        self.search_mode = False
        self.dirlist_path = "/tmp/a"
        self.list_new_nodes_to_process = []


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Amazon S3 File Viewer"))
        self.label.setText(_translate("MainWindow", "Bucket"))
        self.lineEdit_bucket_name.setPlaceholderText(_translate("MainWindow", "my_bucket_name"))
        self.bucketNameButton.setText(_translate("MainWindow", "Get Dirlist"))
        self.label_3.setText(_translate("MainWindow", "Dirlist File"))
        self.buttonLoadData.setText(_translate("MainWindow", "Load"))
        self.buttonOpenDir.setText(_translate("MainWindow", "Open Dir"))
        # Search
        self.labelSearch.setText(_translate("MainWindow", "Search"))
        self.buttonSearchDo.setText(_translate("MainWindow", "Search"))
        self.buttonSearchClear.setText(_translate("MainWindow", "Clear"))
        # Tree widget
        self.treeWidget.headerItem().setText(0, _translate("MainWindow", "Name"))
        self.treeWidget.headerItem().setText(1, _translate("MainWindow", "Size"))
        self.treeWidget.headerItem().setText(2, _translate("MainWindow", "Date Modified"))
        self.treeWidget.headerItem().setText(3, _translate("MainWindow", "Downloaded"))
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.menu_context_tree_view_widget)

    # Menu when right-click on a tree view item
    def menu_context_tree_view_widget(self, point):
        index = self.treeWidget.indexAt(point)
        if not index.isValid():
            return
        self.selected_tree_item = self.treeWidget.itemAt(point)
        self.selected_tree_node = self.tree_item_to_node(self.selected_tree_item)
        # Sanity
        if not self.selected_tree_node:
            self.selected_tree_item = None
            self.selected_tree_node = None
            return 
        is_dir = self.selected_tree_node.is_directory
        is_downloaded = self.selected_tree_node.is_downloaded
        children_files_count = self.selected_tree_node.get_how_many_childern_are_files()

        # Building the menu
        menu = QtWidgets.QMenu()
        fake_action_node_desc = menu.addAction(str(self.selected_tree_node))
        menu.addSeparator()
        # Set actions
        download_title = "Download"
        if is_dir and children_files_count > 0:
            download_title = "Download ({} files)".format(children_files_count)
        action_download = menu.addAction(download_title)
        action_download.triggered.connect(self.tree_item_download)
        can_download = (not is_downloaded) and ((not is_dir) or (is_dir and children_files_count > 0))
        action_download.setEnabled(can_download)

        action_open_file = menu.addAction("Open File")
        action_open_file.triggered.connect(self.tree_item_open_file)
        action_open_file.setEnabled(not is_dir and is_downloaded)
        action_open_dir = menu.addAction("Open Directory")
        action_open_dir.triggered.connect(self.tree_item_open_directory)
        action_open_dir.setEnabled(is_dir or is_downloaded)
        menu.exec_(self.treeWidget.mapToGlobal(point))

    def tree_item_download(self):
        if self.selected_tree_node.is_file:
            self.download_node_with_gui_update(self.selected_tree_node)
        else:
            # Download all child-files
            real_selected_node = self.selected_tree_node
            real_selected_tree = self.selected_tree_item
            real_selected_tree_child_count = real_selected_tree.childCount()
            for i in range(real_selected_tree_child_count):
                tree_child_item = real_selected_tree.child(i)
                tree_child_node = self.tree_item_to_node(tree_child_item)
                if tree_child_node.is_file:
                    self.selected_tree_item = tree_child_item
                    self.selected_tree_node = tree_child_node
                    self.download_node_with_gui_update(tree_child_node)
            self.selected_tree_node = real_selected_node
            self.selected_tree_item = real_selected_tree

    def tree_item_open_file(self):
        open_file(self.selected_tree_node.download_path)

    def tree_item_open_directory(self):
        file_path = self.prepare_dirs_for_download(self.selected_tree_node)
        dir_path = os.path.dirname(file_path)
        open_dir(dir_path)

    def show_message_box(self, msg, alert_type=QtWidgets.QMessageBox.Warning):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(msg)
        msg_box.setIcon(alert_type)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.Ok)
        ret = msg_box.exec_()

    def update_progress_bar(self, blocknum, blocksize, totalsize):
        ## calculate the progress 
        readed_data = blocknum * blocksize 
        if totalsize > 0: 
            download_percentage = readed_data * 100 / totalsize 
            self.progressBar.setValue(download_percentage)
            # Clear
            if self.progressBar.value() >= 100:
                self.progressBar.setValue(0)
                self.labelStatus.setText("")
            QApplication.processEvents()

    def get_tree_item_full_path(self, item):
        out = item.text(0)
        parent = item.parent()
        if parent:
            out = self.get_tree_item_full_path(parent) + "/" + out
        return out

    def check_input_details(self):
        bucket_name = self.lineEdit_bucket_name.text().strip()
        if not bucket_name:
            self.show_message_box("Please fill bucket name")
            return False
        self.current_bucket_name = extract_aws_s3_bucket_name(bucket_name)
        return True

    def prepare_dirs_for_download(self, node):
        path_download = node.full_path.lstrip("/") # remove the first / if any
        # Make dirs
        path_save_to = os.path.join(self.working_dir, self.current_bucket_name, path_download)
        path_save_to_dir = os.path.dirname(path_save_to)
        try:
            os.makedirs(path_save_to_dir, exist_ok=True)
        except Exception as e:
            self.show_message_box(str(e))
            return None
        return path_save_to

    def download_node(self, node):
        # Sanity
        if not self.check_input_details():
            return False
        path_save_to = self.prepare_dirs_for_download(node)
        if not path_save_to:
            return False
        path_download = node.full_path.lstrip("/") # remove the first / if any
        # Prepare URL
        #   http://BUCKETNAME.s3.amazonaws.com/FILE
        #   http://BUCKETNAME.s3.REGION.amazonaws.com/FILE
        url_download = "http://{}.s3.amazonaws.com/{}".format(self.current_bucket_name, path_download)
        url_download_encoded = urllib.parse.quote(url_download, safe=':/')
        try:
            # Download
            urllib.request.urlretrieve(url_download_encoded, path_save_to, self.update_progress_bar)
            node.is_downloaded = True
            node.download_path = path_save_to
        except Exception as e:
            self.show_message_box(url_download + ":\n" + str(e))
            return False
        return True

    def download_node_with_gui_update(self, node):
        if not self.selected_tree_node or not self.selected_tree_node.is_file:
            return
        # Update UI
        self.labelStatus.setText("Downloading {}...".format(node.full_path))
        # Download
        if self.download_node(node):
            self.selected_tree_item.setText(3, "   V ")
        self.progressBar.setValue(0)
        self.labelStatus.setText("")

    def tree_item_to_node(self, tree_item):
        selected_node = None
        # Get full path from item
        item_full_path = self.get_tree_item_full_path(tree_item)
        item_full_path = item_full_path.lstrip("/")
        # Find node from path
        try:
            selected_node = self.root_node.get_sub_node(item_full_path)
        except Exception as e:
            self.show_message_box(str(e))
        return selected_node

    @pyqtSlot( )
    def treeViewFileDoubleClicked(self):
        # Get selected item
        selected_items = self.treeWidget.selectedItems()
        if len(selected_items) < 1:
            self.selected_tree_item = None
            self.selected_tree_node = None
            return 
        self.selected_tree_item = selected_items[0]
        self.selected_tree_node = self.tree_item_to_node(self.selected_tree_item)
        self.download_node_with_gui_update(self.selected_tree_node)
        
    @pyqtSlot( )
    def button_click_process_bucket_dirlist(self):
        file_dialog_options = QtWidgets.QFileDialog.Options()
        file_dialog_options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_dialog_title = "Select Amazon S3 Bucket Dirlist file"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, file_dialog_title, "", "All Files (*)", options=file_dialog_options)
        self.dirlist_path = file_path
        # Update working dir
        self.working_dir = os.path.dirname(os.path.abspath(file_path))
        # Update UI
        self.populate_tree_view_with_gui(file_path)

    @pyqtSlot( )
    def button_click_open_working_dir(self):
        if self.working_dir:
            open_dir(self.working_dir)

    @pyqtSlot( )
    def button_click_download_and_process_bucket_dirlist(self):
        # Check bucket details
        if not self.check_input_details():
            return
        # Check that aws cli works
        if not find_executable("aws") and not shutil.which("aws"):
            self.show_message_box("aws cli was not found. Please make sure you have aws cli installed and configured in the PATH environment variable\nhttps://aws.amazon.com/cli/")
            return
        # # Create temp dir
        # dirlist_name = self.current_bucket_name + ".dirlist.txt"
        # self.working_dir = tempfile.mkdtemp()
        # self.dirlist_path = os.path.join(self.working_dir, dirlist_name)
        # # Downlaod dirlist using aws CLI
        # command_line = "aws --no-sign-request s3 ls s3://{} --recursive > {}".format(self.current_bucket_name, self.dirlist_path)
        # res = os.system(command_line)
        # if res != 0:
        #     self.show_message_box("Error in generating dirlist from {}. Is the name of the bucket correct? Did you run 'aws configure'?".format(self.current_bucket_name))
        #     return
        # Update UI
        self.populate_tree_view_with_gui(self.dirlist_path)
    
    @pyqtSlot( )
    def button_click_search_do(self):
        # Hide all
        for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            item.setHidden(True)
            # Mark as search mode only if there are items
            self.search_mode = True

        if self.search_mode:
            # Show only those that match the search
            search_query = self.lineEditSearch.text()
            flags = QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive
            #flags |= QtCore.Qt.MatchRegExp # use regex
            for item in self.treeWidget.findItems(search_query, flags):
                # Walk up the chain
                item_temp = item
                while item_temp:
                    item_temp.setHidden(False)
                    item_temp = item_temp.parent()
                    # If parent is not hidden, all the chain is visible so no need to redo
                    if item_temp and not item_temp.isHidden():
                        break
    
    @pyqtSlot( )
    def button_click_search_clear(self):
        self.lineEditSearch.setText("")
        if self.search_mode:
            self.search_mode = False
            # Show all
            for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
                item.setHidden(False)

    def get_tree_view_item(self, node, tree):
        # Create tree item
        tree_item = QTreeWidgetItem(tree, [node.basename, str(node.get_human_readable_size()), node.get_date_modified(), ""])
        # Set icon
        if node.is_directory:
            tree_item.setIcon(0, QIcon(os.path.join(RUNNING_DIR, 'assets/folder.png')))
        else:
            tree_item.setIcon(0, QIcon(os.path.join(RUNNING_DIR, 'assets/file.png')))
        return tree_item

    # Populate tree view with all items
    def populate_tree_view(self, node, tree):
        tree_item = self.get_tree_view_item(node, tree)
        # Populate children
        for child_node in node.children.values():
            self.populate_tree_view(child_node, tree_item)

    def dirlist_report_progress(self, node, force_update=False):
        if node:
            self.list_new_nodes_to_process.append(node)

        if len(self.list_new_nodes_to_process) % 3000:
            # Process batch
            for node in self.list_new_nodes_to_process:
                # TODO: Write to file too
                tree_view_item = self.get_tree_view_item(node, node.parent.gui_node)
                node.gui_node = tree_view_item
                self.labelStatus.setText("Currently processing: {}..".format(node.full_path))
                print(node.full_path)
            self.list_new_nodes_to_process.clear()

    def dirlist_thread_finished(self):
        self.dirlist_report_progress(None, force_update=True)
        self.labelStatus.setText("Working dir: {}".format(self.working_dir))
        self.progressBar.setValue(0)
        self.selected_tree_item = None
        self.selected_tree_node = None


    def populate_tree_view_with_gui(self, dirlist_path):
        self.treeWidget.clear()

        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = DirlistWorker()
        self.worker.bucket_name = self.current_bucket_name
        # Add root node to gui
        root_tree_item = self.get_tree_view_item(self.worker.root_node, self.treeWidget)
        self.worker.root_node.gui_node = root_tree_item
        self.root_node = self.worker.root_node

        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.dirlist_report_progress)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.thread.finished.connect(self.dirlist_thread_finished)

        # Update UI
        # self.lineEditDirlist.setText(dirlist_path)
        # self.treeWidget.clear()
        # # Parse dirlist and populate tree view
        # if dirlist_path:
        #     self.labelStatus.setText("Loading data from {}".format(dirlist_path))
        #     try:
        #         self.root_node, nodes_stats = parse_dirlist(dirlist_path)
        #     except Exception as e:
        #         self.show_message_box(str(e))
        #         return
        #     # Update UI
        #     self.populate_tree_view(self.root_node, self.treeWidget)
        #     self.labelStatistics.setText("Total items: {} (dirs: {}, files: {}) | Accumulated size: {} | Dates: {} - {}".format(nodes_stats.count_total,
        #         nodes_stats.count_dirs,
        #         nodes_stats.count_files,
        #         nodes_stats.get_human_readable_size(),
        #         nodes_stats.date_oldest,
        #         nodes_stats.date_newest))
        # else:
        #     self.root_node = None
        #     self.treeWidget.clear()
        #     self.labelStatistics.setText("")
        #     self.current_bucket_name = None
        # Clear
        # self.labelStatus.setText("Working dir: {}".format(self.working_dir))
        # self.progressBar.setValue(0)
        # self.selected_tree_item = None
        # self.selected_tree_node = None



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())