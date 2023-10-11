from .aws_provider import S3StorageProvider
from .azure_provider import AzureStorageProvider
from .ftp_provider import FTPStorageProvider
from .httpindex_provider import HTTPIndexStorageProvider


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
