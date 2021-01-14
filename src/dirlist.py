import subprocess

def yield_aws_dirlist(bucket_name):
    aws_cmd = "aws --no-sign-request s3 ls s3://{aws_bucket} --recursive".format(aws_bucket=bucket_name)
    popen = subprocess.Popen(aws_cmd.split(" "), stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)