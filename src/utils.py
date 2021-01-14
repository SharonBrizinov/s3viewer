import sys
import subprocess


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

def extract_aws_s3_bucket_name(bucket_name):
    # We accept a couple of formats. For example:
    #    - BUCKET_NAME
    #    - http://BUCKET_NAME.s3.amazonaws.com
    #    - https://BUCKET_NAME.s3-us-west-1.amazonaws.com
    #    - BUCKET_NAME.s3.amazonaws.com
    if ".amazonaws.com" in bucket_name:
        bucket_name = bucket_name.replace("https://", "")
        bucket_name = bucket_name.replace("http://", "")
        if ".s3." in bucket_name:
            bucket_name = bucket_name.split(".s3.amazonaws.com")[0]
        if ".s3-" in bucket_name:
            bucket_name = bucket_name.split(".s3-")[0]
    return bucket_name