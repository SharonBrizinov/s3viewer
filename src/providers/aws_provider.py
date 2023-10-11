import shutil
import subprocess
import codecs
from distutils.spawn import find_executable
from urllib.parse import urlparse

from utils import show_message_box
from providers.base_provider import StorageProvider


class S3StorageProvider(StorageProvider):
    NODE_BATCH_UPDATE_COUNT = 1000

    @staticmethod
    def is_provider(url):
        url = url.lower()
        scheme = urlparse(url).scheme
        # If it's a full url and we must make sure we have amazonaws domain
        if scheme:
            if "http" in scheme:
                return ".amazonaws.com" in url
            elif "s3" in scheme:
                return True
            else:
                return False
        # If we don't have HTTP we assume it's just a AWS S3 bucket name
        return True

    # We accept a couple of formats. For example:
    #    - BUCKET_NAME
    #    - http://BUCKET_NAME.s3.amazonaws.com
    #    - https://BUCKET_NAME.s3-us-west-1.amazonaws.com
    #    - BUCKET_NAME.s3.amazonaws.com
    def check(self):
        # Check that aws cli works
        if not find_executable("aws") and not shutil.which("aws"):
            show_message_box("aws cli was not found. Please make sure you have aws cli installed and configured in the PATH environment variable\nhttps://aws.amazon.com/cli/")
            return False
        return True

    def get_download_url(self, relative_path):
        return "http://{}.s3.amazonaws.com/{}".format(self.hostname(), relative_path)

    def yield_dirlist(self):
        aws_cmd = "aws --no-sign-request s3 ls s3://{aws_bucket} --recursive".format(aws_bucket=self.hostname())
        proc = subprocess.Popen(aws_cmd.split(" "), stdout=subprocess.PIPE)
        # we want to work with strings (UTF-8) instead of bytes
        proc.stdout = codecs.getreader('utf-8')(proc.stdout)
        for stdout_line in iter(proc.stdout.readline, ""):
            # Stop
            if self.should_stop:
                break
            yield stdout_line
        proc.stdout.close()
        # Make sure it's dead
        if self.should_stop:
            proc.terminate()
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, aws_cmd)

    def get_default_error_message(self):
        return "Could not get data from '{}' bucket. Most likely the bucket is private or you didn't run 'aws configure' yet".format(self.hostname())

    def hostname(self):
        return self._extract_aws_s3_bucket_name()

    def _extract_aws_s3_bucket_name(self):
        bucket_name = self.url
        if ".amazonaws.com" in bucket_name:
            bucket_name = bucket_name.replace("https://", "")
            bucket_name = bucket_name.replace("http://", "")
            if ".s3." in bucket_name:
                bucket_name = bucket_name.split(".s3.amazonaws.com")[0]
            if ".s3-" in bucket_name:
                bucket_name = bucket_name.split(".s3-")[0]
        elif bucket_name.startswith("s3://"):
            bucket_name = bucket_name.replace("s3://", "")
        return bucket_name