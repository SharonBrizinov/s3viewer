import shutil
import subprocess
import codecs
from distutils.spawn import find_executable
from urllib.parse import urlparse

from utils import show_message_box
from providers.aws_provider import S3StorageProvider
from providers.httpindex_provider import HTTPIndexStorageProvider

def find_provider_class_by_url(url):
    if S3StorageProvider.is_provider(url):
        return S3StorageProvider
    elif HTTPIndexStorageProvider.is_provider(url):
        return HTTPIndexStorageProvider
    return None
