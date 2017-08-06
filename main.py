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

import glob
import os
import shlex
import shutil
import subprocess
import sys
import time
from audiobook import Audiobook

threadsToManage = 8  # How many threads should be run simultaneously

# find audiobooks to encode
for entry in os.listdir("input"):
    # each item in this folder must be a folder containing a single audiobook
    # each audiobook folder name must be named: "Author Name - Book Name"
    # if the audiobook is part of a series it must be named: "Author Name - Series Name NN - Book Name" where NN is the
    #  sequence of the book in the series.
    print("Found book ", entry)

    # the author name is the part of the folder name before the first dash
    # the book name is everything after the first dash
    bookData = entry.partition("-")
    author_name = bookData[0].strip()
    book_name = bookData[2].strip()
    print("Author=", author_name, " Title=", book_name)

    # create working folder
    os.makedirs("working/" + entry)
    workingFolder = 'working/' + entry + '/'

    # get the list of files in some order
    raw_file_list = os.listdir("input/" + entry)
    raw_file_list.sort()

    fileCounter = 0
    referenceToPopens = {}

    bitrate = ''

    for rawfile in raw_file_list:
        if rawfile.startswith('.'):
            print('skipping hidden file ' + rawfile)
        elif rawfile.endswith('.mp3'):
            fileCounter += 1

            # read details from first file - assumption all files encoded similarly
            if bitrate == '':
                audiobook = Audiobook()
                bitrate = audiobook.determine_bitrate_from_mp3_file('input/' + entry + '/' + rawfile)

            outputFilename = workingFolder + "outputfile%03d.aac" % fileCounter

            commandline = 'ffmpeg -i "input/' + entry + '/' + rawfile + '" -loglevel panic -y -c:a aac -b:a  '
            commandline += bitrate + ' "' + outputFilename + '"'

            args = shlex.split(commandline)

            # launch the recode in the background..
            p = subprocess.Popen(args)
            referenceToPopens[fileCounter] = p

    # wait here until all encodes are completed
    filesComplete = 0
    while True:
        # prevent thrashing
        time.sleep(.5)
        for key, value in referenceToPopens.items():
            outputLine = "\rEncoding to aac " + str(filesComplete) + "/" + str(fileCounter)
            sys.stdout.write(outputLine)

            if value.poll() is None:
                time.sleep(.1)
            else:
                # delete item
                del referenceToPopens[key]

                # update counter
                filesComplete += 1
                outputLine = "\rEncoding to aac " + str(filesComplete) + "/" + str(fileCounter)
                sys.stdout.write(outputLine)
                break

        # when all are complete, move to the next audiobook
        if filesComplete >= fileCounter:
            outputLine = "\rEncoding to aac " + str(filesComplete) + "/" + str(fileCounter)
            sys.stdout.write(outputLine)
            sys.stdout.flush()
            break

    # Merge the aac files into a single m4a file
    mergeCommandlineHead = 'ffmpeg -i "concat:'
    mergeCommandlineBody = ""
    mergeCommandlineTail = '" -c copy ' + '"' + workingFolder + entry + '.m4a"'

    fileMergeIterator = 0
    while fileMergeIterator < fileCounter:
        fileMergeIterator += 1
        mergeCommandlineBody += workingFolder + "outputfile%03d.aac" % fileMergeIterator
        if fileMergeIterator < fileCounter:
            mergeCommandlineBody += "|"

    mergeCommand = mergeCommandlineHead + mergeCommandlineBody + mergeCommandlineTail
    print(mergeCommand) # DEBUG

    args = shlex.split(mergeCommand)

    # Now run the merge process for this book - results in m4a containing all aac file content
    subprocess.run(args)

    # rename to m4b
    os.rename(workingFolder + entry + '.m4a', workingFolder + entry + '.m4b')

    # TODO test parameters
    audiobook = Audiobook()
    audiobook.set_metadata_on_m4b_audiobook_file(workingFolder + entry + '.m4b', author_name, book_name, workingFolder + entry)

    # move source folder to the archive folder
    shutil.move("input/" + entry, "archive/" + entry)

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

    # move m4b to output folder
    shutil.move(workingFolder + entry + '.m4b', "done/")

    # clear working folder
    shutil.rmtree(workingFolder)


