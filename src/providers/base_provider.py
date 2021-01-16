
class StorageProvider():
    NODE_BATCH_UPDATE_COUNT = 1

    def __init__(self, url):
        self.url = url
        self.should_stop = False

    @staticmethod
    def is_provider(url):
        return False

    def check(self):
        return True

    def get_download_url(self, relative_path):
        return relative_path

    def hostname(self):
        return self.url

    def yield_dirlist(self):
        pass

    def get_default_error_message(self):
        pass

    def stop(self):
        self.should_stop = True

