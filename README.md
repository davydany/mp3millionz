# MP3Millionz

If you use MP3Million.com and you ever need to download a large amount of your purchased music,
and you don't want to do it manually, you can do it with this utility!

## Install

Ensure that you have pip installed.

```python
pip install -r requires.txt
```

## Run

Simply run this:

```bash
python millionz.py <username> <password>
```

## Arguments

```bash
usage: millionz.py [-h] [--output_directory OUTPUT_DIRECTORY]
                   username password

positional arguments:
  username
  password

optional arguments:
  -h, --help            show this help message and exit
  --output_directory OUTPUT_DIRECTORY
                        Absolute path to where to store downloaded files.
```
