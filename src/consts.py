import re

### Dirlist
# Example: '2016-11-14 16:14:10         10 DirName/File.txt'
DIRLIST_REGEX = re.compile("(\d+\-\d+\-\d+ \d+\:\d+\:\d+)\s+(\d+)\s+(.*)")