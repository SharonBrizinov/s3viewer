import datetime
import os
import re
import urllib
from ftplib import FTP

from consts import FTP_MAX_RECURSE_LEVEL, FTP_USER_DEFAULT, FTP_PASS_DEFAULT
from dateutil import parser as dateutil_parser
from providers.base_provider import StorageProvider
from utils import show_message_box

TEMP_OUTPUT = []


def _ftp_dir_collector_callback(line):
    global TEMP_OUTPUT
    TEMP_OUTPUT.append(line)


# Took this function from https://github.com/codebynumbers/ftpretty/blob/master/ftpretty.py
def split_file_info(fileinfo):
    """ Parse sane directory output usually ls -l
        Adapted from https://gist.github.com/tobiasoberrauch/2942716
    """
    current_year = datetime.datetime.now().strftime('%Y')
    files = []

    # Example:
    #   drwxrwsr-x    2 844      i-admin      4096 Feb 18  2020 2020Census
    #   lrwxrwxrwx    1 844      i-admin        17 Jan 24  2014 AOA -> /acstabs/docs/AOA
    unix_format = re.compile(
        r'^([\-dbclps])' +                  # Directory flag [1]
        r'((?:[r-][w-][-xsStT]){3})\s+' +   # Permissions [2]
        r'(\d+)\s+' +                       # Number of items [3]
        r'([a-zA-Z0-9_-]+)\s+' +            # File owner [4]
        r'([a-zA-Z0-9_-]+)\s+' +            # File group [5]
        r'(\d+)\s+' +                       # File size in bytes [6]
        r'(\w{3}\s+\d{1,2})\s+' +           # 3-char month and 1/2-char day of the month [7]
        r'(\d{1,2}:\d{1,2}|\d{4})\s+' +     # Time or year (need to check conditions) [+= 7]
        r'(.+)$'                            # File/directory name [8]
    )
    # not exactly sure what format this, but seems windows-esque
    # attempting to address issue: https://github.com/codebynumbers/ftpretty/issues/34
    # can get better results with more data.
    # Examples:
    #   03-11-19  09:47AM       <DIR>          dirname
    #   07-28-16  02:59PM            318807244 filename.txt
    windows_format = re.compile(
        r'(\d{2})-(\d{2})-(\d{2})\s+' +     # month/day/2-digit year (assuming after 2000)
        r'(\d{2}):(\d{2})([AP])M\s+' +      # time
        r'(\d+)?(\<DIR\>)?\s+' +            # file size or directory
        r'(.+)$'                            # File/directory name [8]
    )

    for line in fileinfo:
        if unix_format.match(line):
            parts = unix_format.split(line)
            directory_flags = parts[1]
            is_directory = "d" in directory_flags or "l" in directory_flags # dir or link (junction)

            # Handling linking:
            #   lrwxrwxrwx    1 844      i-admin        12 Jan 24  2014 incoming -> pub/incoming
            name = parts[9]
            if "l" in directory_flags and " -> " in name:
                name = name.split(" -> ")[0]

            date = parts[7]
            time = parts[8] if ':' in parts[8] else '00:00'
            year = parts[8] if ':' not in parts[8] else current_year

            dt_obj = dateutil_parser.parse("%s %s %s" % (date, year, time))
            files.append({
                'is_directory': is_directory,
                'directory': parts[1],
                'perms': parts[2],
                'items': parts[3],
                'owner': parts[4],
                'group': parts[5],
                'size': int(parts[6]),
                'date': date,
                'time': time,
                'year': year,
                'name': name,
                'datetime': dt_obj
            })
        elif windows_format.match(line):
            parts = windows_format.split(line)

            is_directory = parts[8] == "<DIR>"
            if is_directory:
                size = 0
            else:
                size = int(parts[7])
            hour = int(parts[4])
            hour += 12 if 'P' in parts[6] else 0
            hour = 0 if hour == 24 else hour
            year = int(parts[3]) + 2000
            dt_obj = datetime.datetime(year, int(parts[1]), int(parts[2]), hour, int(parts[5]), 0)

            files.append({
                'is_directory': is_directory,
                'directory': None,
                'perms': None,
                'items': None,
                'owner': None,
                'group': None,
                'size': size,
                'date': "{}-{}-{}".format(*parts[1:4]),
                'time': "{}:{}{}".format(*parts[4:7]),
                'year': year,
                'name': parts[9],
                'datetime': dt_obj
            })
    return files


def is_directory(entry):
    return entry.get("is_directory")


def is_file_or_dir_ok(entry):
    name = entry.get("name")
    if not name or name == "." or name == "..":
        return False
    return True

def yield_fetch_dir(ftp_conn, cwd="/", max_recurse_level=FTP_MAX_RECURSE_LEVEL, recurse_level=0):
    global TEMP_OUTPUT
    if recurse_level == max_recurse_level:
        return
    queue_process = []
    recurse_level += 1

    ftp_conn.dir(cwd, _ftp_dir_collector_callback)
    listing = split_file_info(TEMP_OUTPUT)
    TEMP_OUTPUT.clear()

    # Fix cwd to support inner starting point
    #   cwd shouldn't start with /, but it should end with one
    cwd_name = cwd.strip("/")
    if cwd_name:
        cwd_name += "/"

    for f in listing:
        if not is_file_or_dir_ok(f):
            continue
        filename_output = cwd_name + f.get("name")
        # Fix name, only directories should end with /
        if is_directory(f):
            if not filename_output.endswith("/"):
                filename_output = filename_output + "/"
        else:
            filename_output = filename_output.strip("/")

        f["full_path"] = filename_output
        date_format = f.get("datetime").strftime('%Y-%m-%d %H:%M:%S')
        size_format = f.get("size") or "0"
        yield "{}{:>13} {}".format(date_format, size_format, filename_output) + os.linesep
        queue_process.append(f)
    for f in queue_process:
        if is_directory(f):
            yield from yield_fetch_dir(ftp_conn, cwd=f.get("full_path"), max_recurse_level=max_recurse_level, recurse_level=recurse_level)


class FTPStorageProvider(StorageProvider):
    NODE_BATCH_UPDATE_COUNT = 10

    @staticmethod
    def is_provider(url):
        url = url.lower()
        scheme = urllib.parse.urlparse(url).scheme
        if scheme and "ftp" in scheme:
            return True
        return False

    def check(self):
        try:
            self.ftp = FTP(self.hostname(), FTP_USER_DEFAULT, FTP_PASS_DEFAULT)
            if self.ftp.pwd():
                return True
            return False
        except Exception as e:
            show_message_box(self.get_default_error_message())
        return False

    def get_download_url(self, relative_path):
        uri_obj = urllib.parse.urlparse(self.url)
        return '{uri.scheme}://{uri.netloc}/{relative_path}'.format(uri=uri_obj, relative_path=relative_path)

    def yield_dirlist(self):
        if not self.ftp:
            self.ftp = FTP(self.hostname(), FTP_USER_DEFAULT, FTP_PASS_DEFAULT)

        for dirlist_line in yield_fetch_dir(self.ftp, self.url_path()):
            # Stop
            if self.should_stop:
                self.ftp.close()
                break
            yield dirlist_line

    def get_default_error_message(self):
        return "Could not enter FTP server. Are you sure anonymous access is allowed?"

    def hostname(self):
        return urllib.parse.urlparse(self.url).netloc

    def url_path(self):
        url_path = urllib.parse.urlparse(self.url).path
        if not url_path:
            url_path = "/"
        return url_path
