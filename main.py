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
from audiobook import Audiobook

threadsToManage = 8  # How many threads should be run simultaneously

input_folder = "input/"
working_folder = "working/"
output_folder = "done/"
archive_folder = "archive/"

# find audiobooks to encode
for entry in os.listdir(input_folder):
    # each item in this folder must be a folder containing a single audiobook
    # each audiobook folder name must be named: "Author Name - Book Name"
    # if the audiobook is part of a series it must be named: "Author Name - Series Name NN - Book Name" where NN is the
    #  sequence of the book in the series.
    print("Found book ", entry)

    source_folder = input_folder + entry + "/"

    # the author name is the part of the folder name before the first dash
    # the book name is everything after the first dash
    bookData = entry.partition("-")
    author_name = bookData[0].strip()
    book_name = bookData[2].strip()
    print("Author=", author_name, " Title=", book_name)

    audiobook = Audiobook(author_name, book_name, source_folder, working_folder, output_folder, archive_folder)

    # create working folder
    audiobook.create_working_folder()

    if audiobook.determine_source_type() == audiobook.source_type_mp3_single_folder:
        # determine bitrate - first mp3 file in source folder
        bitrate = "64k"

        # encode all mp3 files in source folder to aac
        audiobook.encode_mp3_files_in_source_folder(bitrate)

        # combine all aac files in working folder to m4b
        audiobook.merge_aac_files_in_working_folder_into_m4b()

    elif audiobook.determine_source_type() == audiobook.source_type_mp3_single_folder:
        # copy all mp3 files to new single folder structure in working folder

        # determine bitrate - first mp3 file in working folder
        bitrate = "64k"

        # encode all mp3 files in working folder to aac
        audiobook.encode_mp3_files_in_working_folder(bitrate)

        # combine all aac files in working folder to m4b
        audiobook.merge_aac_files_in_working_folder_into_m4b()

    elif audiobook.determine_source_type() == audiobook.source_type_aac_single_folder:
        # WARNING - ONLY WORKS IF ALL SOURCE FILES HAVE SAME BITRATE

        # copy aac files into well named aac files in working folder
        audiobook.copy_aac_files_to_working_folder()

        # combine all aac files in working folder to m4b
        audiobook.merge_aac_files_in_working_folder_into_m4b()

    # set metadata
    audiobook.set_metadata_on_m4b_audiobook_file()

    # move m4b to output folder
    audiobook.move_completed_encode_to_output_folder()

    # archive source folder
    audiobook.archive_source_files()

    # clear working folder
    audiobook.clear_working_folder()


