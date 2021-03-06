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
import mutagen

threadsToManage = 8  # How many threads should be run simultaneously

input_folder = "/home/tom/dev/data/audiobooks/input/"
working_folder = "/home/tom/dev/data/audiobooks/working/"
output_folder = "/home/tom/dev/data/audiobooks/done/"
archive_folder = "/home/tom/dev/data/audiobooks/archive/"
error_folder = "/home/tom/dev/data/audiobooks/error/"

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

    audiobook = Audiobook(author_name, book_name, source_folder, working_folder, output_folder, archive_folder, error_folder, threadsToManage)

    try:
        audiobook.create_working_folder()

        source_type = audiobook.determine_source_type()
        print(source_type)

        if source_type == audiobook.source_type_mp3_single_folder:
            # determine bitrate - first mp3 file in source folder
            bitrate = audiobook.determine_bitrate_from_mp3_file(audiobook.source_folder)

            # encode all mp3 files in source folder to aac
            audiobook.encode_mp3_files_in_source_folder(bitrate)

            # pull chapter lengths from source mp3s
            # audiobook.mp3_extract_chapter_metadata()

            # combine all aac files in working folder to m4b
            audiobook.merge_aac_files_in_working_folder_into_m4b()

            audiobook.load_chapters()

        elif source_type == audiobook.source_type_mp3_multi_folder:
            # copy all mp3 files to new single folder structure in working folder
            audiobook.deepcopy_mp3_files_to_working_folder()

            # determine bitrate - first mp3 file in working folder
            bitrate = audiobook.determine_bitrate_from_mp3_file(audiobook.working_folder)

            # encode all mp3 files in working folder to aac
            audiobook.encode_mp3_files_in_working_folder(bitrate)

            # combine all aac files in working folder to m4b
            audiobook.merge_aac_files_in_working_folder_into_m4b()

            audiobook.load_chapters()

        elif source_type == audiobook.source_type_aac_single_folder:
            # WARNING - ONLY WORKS IF ALL SOURCE FILES HAVE SAME BITRATE

            # copy aac files into well named aac files in working folder
            audiobook.copy_files_to_working_folder('aac')

            # combine all aac files in working folder to m4b
            audiobook.merge_aac_files_in_working_folder_into_m4b()

        elif source_type == audiobook.source_type_m4a_single_folder:
            # WARNING - ONLY WORKS IF ALL SOURCE FILES HAVE SAME BITRATE

            # copy m4a files into working folder
            audiobook.copy_files_to_working_folder('m4a')

            # extract aac audio from m4a
            audiobook.extract_aac_from_files_in_working_folder('m4a')

            # combine all aac files in working folder to m4b
            audiobook.merge_aac_files_in_working_folder_into_m4b()

        elif source_type == audiobook.source_type_m4b_single_folder:
            # WARNING - ONLY WORKS IF ALL SOURCE FILES HAVE SAME BITRATE

            # copy m4a files into working folder
            audiobook.copy_files_to_working_folder('m4b')

            # extract aac audio from m4a
            audiobook.extract_aac_from_files_in_working_folder('m4b')

            # combine all aac files in working folder to m4b
            audiobook.merge_aac_files_in_working_folder_into_m4b()


        # set metadata
        audiobook.set_metadata_on_m4b_audiobook_file()

        # move m4b to output folder
        audiobook.move_completed_encode_to_output_folder()

        # archive source folder
        audiobook.archive_source_files()

    # except mutagen.mp3.HeaderNotFoundError:
    #     audiobook.error_handle_mutagenmp3headernotfound()

    finally:

        # clear working folder
        audiobook.clear_working_folder()


