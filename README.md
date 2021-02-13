# S3Viewer [![Build Status](https://travis-ci.com/SharonBrizinov/s3viewer.svg?branch=main)](https://travis-ci.com/SharonBrizinov/s3viewer)
## Publicly open storage viewer (Amazon S3 Bucket, Azure Blob, FTP server, HTTP Index Of/)

<p align="center">
	<img src="packaging/icons/icon_3s.jpg" width="200">
</p>


`s3viewer` is a free tool for security researchers that lists the content of publicly open storages and helps to identify leaking data. The tool allows you to view all the files in a given storage and download selected files and directories. The goal is to identify the owner of the storage as quickly as possible in order to report that data is leaking from it.

Supported open storage:
- Amazon S3 Buckets
- Microsoft Azure Blobs
- FTP servers with Anonymous access allowed
- HTTP Index Of / Pages (Apache/nginx-style directory listing)


![Demo](example/demo.gif)


The tool lists directory contents and display them in a tree view GUI from which you can navigate to view all directories and files and even download them. You can also use the `Load` button to load a pre-downloaded dirlist to view the directory hierarchy offline.


![Simplified](example/simplified.png)

 
## Feature List
- Supporting multiple open storage types including S3 bucket, Azure blob, FTP, HTTP Index
- View, download, and interact with open storage directory hierarchy
- Generate offline dirlist and load it later to work offline
- Search for specific files easily
- Cross-platform (Windows, MAC, Linux) GUI desktop application
- Free

## Setup
**Prerequisites**

- python3
	- `python3 -m pip install -r packaging/requirements.txt`
- [aws cli](https://aws.amazon.com/cli/)
	- make sure `aws` works. Then configure once (`aws configure`) with a random region (e.g. `us-east-1`). No need for keys.
- [azure azcopy](https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10)
	- download and place `azcopy` somewhere along the PATH

## Run
```bash
python s3viewer.py
```
**Usage**
Fill the storage url and press `Get Dirlist`. Use double-click to download a file or use right-click for more options such as download all files in a directory. You can keep the generated dirlist to load quickly later.

**Supported URL schemes**
- AWS
	- http://<BUCKETNAME>.s3.<REGION>.amazonaws.com/
	- https://<BUCKETNAME>.s3.amazonaws.com
	- s3://<BUCKETNAME>
- Azure
	- https://<ACCOUNTNAME>.blob.core.windows.net/<CONTAINER>
- FTP
	- ftp://ftp.server.com
- HTTP Index
	- http://server.com/indexof


### TODO
- Features
  - Download manager
    - Background downloads
    - Parallel downloads
    - Stop/Pause/Resume a download
  - Explorer mode
  - Mac, Linux builds
- Bugs
  - Progress bar isn't synced with FTP downloads

## Motivation
### TL;DR
Publicly open storages have become a serious threat to many companies and people due to [massive data leaks](https://github.com/nagwww/s3-leaks) which led to countless breaches, extortions, and overall embarrassment to all invloved parties. I have personally discovered and reported on dozens of major publicly open storages open to the public belonging to companies that were completely unaware of them. This must be stopped and I hope this tool will help security researchers to identify misconfigured cloud instances in order to responsibly disclose it to the affected companies.

### Longer Version
Simple Storage Service (S3) bucket is a public cloud storage resource available in Amazon Web Services (AWS). They are favorable by developers and IT team, as their storages offer a simple web service interface which enables them to store and retrieve any amount of data at any time from anywhere. Companies are trying to keep up with the pace and ensure their cloud-stored data is safe, yet despite that, they haven't fully incorporated best practices from AWS and we see **[WAAAAAAAY TOO MANY](https://buckets.grayhatwarfare.com/) misconfigured publicly open buckets that can be easily accessed by anyone**.

As the popularity of s3 buckets increased I started to discover more and more publicly open buckets and needed a tool to assist me in identifying the companies behind the buckets. Sometimes correlating a bucket name to a company may prove to be an easy task, but sometimes the name of the bucket is too vague and it’s unclear of the company behind it, for example “devbucket” or “prod3bucket”.

The problem with cloud storage technologies, such as S3 buckets, is that they tend to be misconfigured, as proven in recent data breaches, and may leak data to anyone with a browser. That is why it is important to recognize and report any leaked information, since today's leaked information can be a random company's information, but  tomorrow's leaked information could be your business or personally identifying information leaked to criminals.
