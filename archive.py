# binds mp3 audiobooks into more manageable m4b audiobooks

# this software looks for audiobooks, each in its own folder, in the input folder
# for each book:
#   it creates a scratch folder in the working directory for this book, where it encodes each mp3 input
#    files into an aac file (in parallel)
#   -   the quality of the encoding is directly related to the properties of the input mp3, the higher the quality
#        the greater the bitrate
#   it merges each of the aac files into a single m4b file, then sets metadata on this file
#       to keep metadata clean, it is minimal and consists only of book name, author name
#   it moves the m4b file into the output folder and moves the mp3 audiobook into the completed folder

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
import os
import shlex
import shutil
import subprocess
import sys
import time

threadsToManage = 8  # How many threads should be run simultaneously? This will make best use of a multicore system

# find audiobooks to encode
for entry in os.listdir("archive"):
    # each item in this folder must be a folder containing a single audiobook
    # each audiobook folder name must be named: "Author Name - Book Name"
    # if the audiobook is part of a series it must be named: "Author Name - Series Name NN - Book Name" where NN is the
    #  sequence of the book in the series.
    print("Found book ", entry)
    # 7zip with ultra settings the source folder
    commandline = '7zr a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on'
    commandline += ' "archive/' + entry + '.7z"'
    commandline += ' "archive/' + entry + '/"'

    args = shlex.split(commandline)

    # compress the source media files
    p = subprocess.call(args)

    # delete the uncompressed source media files
    commandline = 'rm -rf "archive/' + entry + '/"'

    args = shlex.split(commandline)

    # delete the uncompressed source media files
    p = subprocess.call(args)

