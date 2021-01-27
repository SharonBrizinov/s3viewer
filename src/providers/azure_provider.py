import re
import os
import shutil
import subprocess
import codecs
from distutils.spawn import find_executable
from urllib.parse import urlparse

from utils import show_message_box
from providers.base_provider import StorageProvider

AZURE_LINE_REGEX = re.compile(r"INFO\: (.*); Content Length: (\d+)")

class AzureStorageProvider(StorageProvider):
    NODE_BATCH_UPDATE_COUNT = 1000

    @staticmethod
    def is_provider(url):
        url = url.lower()
        scheme = urlparse(url).scheme
        if scheme:
            if "http" in scheme:
                return ".blob.core.windows.net" in url
        return False

    #    - Azure Blog
    #    - http://BLOB_NAME.blob.core.windows.net/CONTAINER/PATH
    def check(self):
        # Check that azcopy works
        if not find_executable("azcopy") and not shutil.which("azcopy"):
            show_message_box("azcopy not found. Please make sure you have placed azcopy somewhere in the PATH. https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10")
            return False
        container = urlparse(self.url.lower()).path
        if not container or container == "/":
            show_message_box("Please provide container name as well. https://BLOBNAME.blob.core.windows.net/CONTAINER")
            return False
        return True

    def get_download_url(self, relative_path):
        return self.url.rstrip("/") + "/" + relative_path

    def _parse_line(self, line):
        # INFO: filename; Content Length: 1234
        line_parsed = AZURE_LINE_REGEX.findall(line)
        if line_parsed:
            file_path, size = line_parsed[0]
            # TODO: Currently there is no date in azcopy output, so we are faking one
            return "1970-01-01 00:00:00 {:>13} {}".format(size, file_path) + os.linesep
        return None

    def yield_dirlist(self):
        cmd = "azcopy list --machine-readable {azure_blob}".format(azure_blob=self.url)
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=False)
        # we want to work with strings (UTF-8) instead of bytes
        proc.stdout = codecs.getreader('utf-8')(proc.stdout)
        for stdout_line in iter(proc.stdout.readline, ""):
            # Stop
            if self.should_stop:
                break
            yield self._parse_line(stdout_line)
        proc.stdout.close()
        # Make sure it's dead
        if self.should_stop:
            proc.terminate()
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    def get_default_error_message(self):
        return "Could not get data from '{}' azure blob. Most likely the blob is private or you don't have azcopy placed somewhere in the PATH".format(self.hostname())

    def hostname(self):
        return self._extract_azure_blob_name()

    def _extract_azure_blob_name(self):
        return urlparse(self.url).netloc.split(".blob.core.windows.net")[0]