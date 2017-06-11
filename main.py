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

import os
import shlex
import subprocess
import sys
import time

# find audiobooks to encode
for entry in os.listdir("input"):
    # each item in this folder must be a folder containing a single audiobook
    # each audiobook folder name must be named: "Author Name - Book Name"
    # if the audiobook is part of a series it must be named: "Author Name - Series Name NN - Book Name" where NN is the
    #  sequence of the book in the series.
    print("Found book ", entry)

    # the author name is the part of the folder name before the first dash
    # the book name is everything after the first dash
    bookdata = entry.partition("-")
    authorname = bookdata[0]
    bookname = bookdata[2]
    print("Author=", authorname, " Title=", bookname)

    # create working folder
    os.makedirs("working/" + entry)
    workingFolder = 'working/' + entry + '/'

    # get the list of files in some order
    rawfilelist = os.listdir("input/" + entry)
    rawfilelist.sort()

    filecounter = 0
    referenceToPopens = {}

    for rawfile in rawfilelist:
        if rawfile.endswith('.mp3'):
            filecounter += 1

            # TODO fix to use appropriate bitrate
            ##################################################################
            #            # <22.05 KHz # 22.05KHz   # 44.1 KHz   # >44.1KHz   #
            ##################################################################
            # Stereo     #  48 Kbps   #  64 Kbps   #  96 Kbps   # 112 Kbps   #
            # Mono       #  48 Kbps   #  48 Kbps   #  64 Kbps   #  80 Kbps   #
            ##################################################################
            # TODO determine input channels - stereo or mono?
            input_channels = 1  # mono

            # TODO determine input frequency in Hz
            input_freq = 44100

            bitrate = "64k"  # default - always overridden
            if input_channels > 1 and input_freq > 44100:
                bitrate = "112k"
            elif input_freq > 44100:
                bitrate = "80k"
            elif input_channels > 1 and input_freq > 44000:
                bitrate = "96k"
            elif input_freq > 44000:
                bitrate = "64k"
            elif input_channels > 1 and input_freq > 22000:
                bitrate = "64k"
            elif input_freq > 22000:
                bitrate = "48k"
            elif input_channels > 1:
                bitrate = "48k"
            else:
                bitrate = "48k"

            outputFilename = workingFolder + "outputfile%03d.aac" % filecounter

            commandline = 'ffmpeg -i "input/' + entry + '/' + rawfile + '" -loglevel panic -y -c:a aac -b:a  '
            commandline += bitrate + ' "' + outputFilename + '"'

            args = shlex.split(commandline)

            # launch the recode in the background..
            p = subprocess.Popen(args)
            referenceToPopens[filecounter] = p

    # wait here until all encodes are completed
    filesComplete = 0
    while True:
        # prevent thrashing
        time.sleep(.5)
        for key, value in referenceToPopens.items():
            outputLine = "\rEncoding to aac. " + str(filesComplete) + "/" + str(filecounter) + " completed"
            sys.stdout.write(outputLine)

            if value.poll() is None:
                time.sleep(.1)
            else:
                # delete item
                del referenceToPopens[key]

                # update counter
                filesComplete += 1
                outputLine = "\rEncoding to aac. " + str(filesComplete) + "/" + str(filecounter) + " completed"
                sys.stdout.write(outputLine)
                break

        # when all are complete, move to the next audiobook
        if filesComplete >= filecounter:
            outputLine = "\rEncoding to aac. " + str(filesComplete) + "/" + str(filecounter) + " completed"
            sys.stdout.write(outputLine)
            sys.stdout.flush()
            break

    # Merge the aac files into a single m4a file
    mergeCommandlineHead = 'ffmpeg -i "concat:'
    mergeCommandlineBody = ""
    mergeCommandlineTail = '" -c copy ' + '"' + workingFolder + entry + '.m4a"'

    fileMergeIterator = 0
    while fileMergeIterator < filecounter:
        fileMergeIterator += 1
        mergeCommandlineBody += workingFolder + "outputfile%03d.aac" % fileMergeIterator
        if fileMergeIterator < filecounter:
            mergeCommandlineBody += "|"

    mergeCommand = mergeCommandlineHead + mergeCommandlineBody + mergeCommandlineTail
    print(mergeCommand) # DEBUG

    args = shlex.split(mergeCommand)

    # Now run the merge process for this book - results in m4a containing all aac file content
    p = subprocess.Popen(args)


    # set metadata
    # - set author, book name
    # - TODO set cover image

    # rename to m4b

    # move source to completed folder

    # move m4b to output folder

    # clear working folder
