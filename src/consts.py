import re

### Dirlist
# Example: '2016-11-14 16:14:10         10 DirName/File.txt'
DIRLIST_REGEX = re.compile("(\d+\-\d+\-\d+ \d+\:\d+\:\d+)\s+(\d+)\s+(.*)")

# User agent
USER_AGENT = "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19"

# Providers
DEFAULT_NODE_BATCH_UPDATE_COUNT = 100
HTTP_MAX_RECURSE_LEVEL = 50
FTP_MAX_RECURSE_LEVEL = 50
FTP_USER_DEFAULT = "anonymous"
FTP_PASS_DEFAULT = "anonymous"

# Download
DOWNLOAD_MIN_CHUNK_SIZE = 10*1024 # 10KB

# Max items
DEFAULT_MAX_ITEMS = 50_000