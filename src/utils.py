import sys
import os
import subprocess
import urllib
from urllib.parse import urlparse

import requests
from PyQt5 import QtWidgets

from consts import USER_AGENT, DOWNLOAD_MIN_CHUNK_SIZE


# Get reference to running directory
RUNNING_DIR = os.path.dirname(os.path.abspath(__file__))
# PyInstaller - in case of PyInstaller the running directory is sys._MEIPASS
if hasattr(sys, '_MEIPASS'):
    RUNNING_DIR = sys._MEIPASS

def get_asset_path(relative_path):
    return os.path.join(RUNNING_DIR, relative_path)

def download_file(url, filename, report_hook):
    scheme = urlparse(url).scheme
    if "ftp" in scheme:
        urllib.request.urlretrieve(url, filename, reporthook=report_hook)
    elif "http" in scheme:
        counter = 0
        with open(filename, 'wb') as f:
            headers = {"User-Agent": USER_AGENT}
            response = requests.get(url, headers=headers, verify=False, stream=True)
            response.raise_for_status()
            total = response.headers.get('content-length')

            if total is None:
                f.write(response.content)
            else:
                downloaded = 0
                total = int(total)
                chunk_size = max(int(total/1000), DOWNLOAD_MIN_CHUNK_SIZE)
                for data in response.iter_content(chunk_size=chunk_size):
                    downloaded += len(data)
                    f.write(data)
                    report_hook(count=counter, blockSize=chunk_size, totalSize=total)
                    counter += 1
    else:
        raise Exception("Download error: unknown scheme")


def show_message_box(msg, alert_type=QtWidgets.QMessageBox.Warning):
    msg_box = QtWidgets.QMessageBox()
    msg_box.setText(msg)
    msg_box.setIcon(alert_type)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg_box.setDefaultButton(QtWidgets.QMessageBox.Ok)
    ret = msg_box.exec_()

def open_dir(path):
    try:
        if sys.platform == 'darwin':
            subprocess.check_call(['open', '--', path])
        elif sys.platform == 'linux2':
            subprocess.check_call(['xdg-open', '--', path])
        elif sys.platform == 'win32':
            subprocess.check_call(['explorer', path])
    except subprocess.CalledProcessError as e:
        pass

def open_file(path):
    try:
        if sys.platform == 'darwin':
            subprocess.check_call(['open', path])
        elif sys.platform == 'linux2':
            subprocess.check_call(['xdg-open', path])
        elif sys.platform == 'win32':
            os.startfile(path)
    except subprocess.CalledProcessError as e:
        pass

def extract_domain(url):
    domain = urlparse('url').netloc
    return domain or url

def decode_data(data):
    # Try brute forcing all popular encodings
    for encoding in ["utf-8", "utf-16-le", "utf-16-be", "latin-1", "ascii"]:
        try:
            return data.decode(encoding)
        except Exception as e:
            pass
    return None