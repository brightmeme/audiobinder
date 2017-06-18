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
from mutagen.mp4 import MP4
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
    bookData = entry.partition("-")
    authorName = bookData[0]
    bookName = bookData[2]
    print("Author=", authorName, " Title=", bookName)

    # create working folder
    os.makedirs("working/" + entry)
    workingFolder = 'working/' + entry + '/'

    # get the list of files in some order
    rawfilelist = os.listdir("input/" + entry)
    rawfilelist.sort()

    fileCounter = 0
    referenceToPopens = {}

    bitrate = ''

    for rawfile in rawfilelist:
        if rawfile.endswith('.mp3'):
            fileCounter += 1

            # read details from first file - assumption all files encoded similarly
            if bitrate == '':
                # Table of appropriate bit rates for spoken word content
                ##################################################################
                #            # <22.05 KHz # 22.05KHz   # 44.1 KHz   # >44.1KHz   #
                ##################################################################
                # Stereo     #  48 Kbps   #  64 Kbps   #  96 Kbps   # 112 Kbps   #
                # Mono       #  32 Kbps   #  48 Kbps   #  64 Kbps   #  80 Kbps   #
                ##################################################################

                mp3Info = MP3('input/' + entry + '/' + rawfile)

                # TODO determine input channels - stereo or mono?
                input_channels = mp3Info.info.channels

                # TODO determine input frequency in Hz
                input_freq = mp3Info.info.sample_rate

                bitrate = "64k"  # default - should always be overridden
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
                    bitrate = "32k"

                bitrateMessage = "As the input file is " + str(input_freq) + "Hz"
                bitrateMessage += " and has " + str(input_channels) + " channel"
                bitrateMessage += ", use a bitrate of " + bitrate
                print(bitrateMessage)

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

    # set metadata
    mp4Info = MP4(workingFolder + entry + '.m4b')

    # set minimal tags - DOESNT SEEM TO WORK?
    mp4Info['\\xa9ART'] = authorName
    mp4Info['\\xa9alb'] = bookName

    # - TODO set cover image

    mp4Info.save()


    # move source folder to the completed folder

    # move m4b to output folder

    # clear working folder
