import shutil
import subprocess
import codecs
from distutils.spawn import find_executable
from urllib.parse import urlparse

from utils import show_message_box
from providers.aws_provider import S3StorageProvider
from providers.httpindex_provider import HTTPIndexStorageProvider
from providers.ftp_provider import FTPStorageProvider
from providers.azure_provider import AzureStorageProvider


def find_provider_class_by_url(url):
    if AzureStorageProvider.is_provider(url):
        return AzureStorageProvider
    elif FTPStorageProvider.is_provider(url):
        return FTPStorageProvider
    elif S3StorageProvider.is_provider(url):
        return S3StorageProvider
    elif HTTPIndexStorageProvider.is_provider(url):
        return HTTPIndexStorageProvider
    return None
