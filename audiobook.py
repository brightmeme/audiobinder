
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from collections import Counter
import fnmatch
import glob
import os
import shlex
import shutil
import subprocess
import sys
import time

class Audiobook:

    source_type_mp3_single_folder = "mp3single"
    source_type_mp3_multi_folder = "mp3multi"
    source_type_aac_single_folder = "aacsingle"
    source_type_m4a_single_folder = "m4asingle"
    source_type_m4b_single_folder = "m4bsingle"

    def __init__(self, author, title, source_folder, working_folder, output_folder, archive_folder,threads_to_manage):
        self.author = author
        self.title = title
        self.source_folder = source_folder
        self.working_folder = working_folder
        self.output_folder = output_folder
        self.archive_folder = archive_folder
        self.source_book_folder_name = author + ' - ' + title
        self.threads_to_manage = threads_to_manage

    def create_working_folder(self):
        os.makedirs(self.working_folder + self.source_book_folder_name)
        self.working_folder = self.working_folder + self.source_book_folder_name + '/'

    def prepare_mp3_multi_folder_source_for_encoding(self):
        # TODO copy all mp3 files into working folder prefixed with the name of their folder
        subfolders = self.get_subfolders_in_source_folder()
        #for each subfolder in subfolders:
            #move files up a level prefixed with the folder name

    def get_subfolders_in_source_folder(self):
        return [name for name in os.listdir(self.source_folder)
                if os.path.isdir(os.path.join(self.source_folder, name))]

    def determine_source_type(self):


        aac_file_counter = len(fnmatch.filter(os.listdir(self.source_folder), '*.aac'))
        if aac_file_counter > 0:
            return self.source_type_aac_single_folder

        m4a_file_counter = len(fnmatch.filter(os.listdir(self.source_folder), '*.m4a'))
        if m4a_file_counter > 0:
            return self.source_type_m4a_single_folder

        m4b_file_counter = len(fnmatch.filter(os.listdir(self.source_folder), '*.m4b'))
        if m4b_file_counter > 0:
            return self.source_type_m4b_single_folder

        mp3_file_counter = len(fnmatch.filter(os.listdir(self.source_folder), '*.mp3'))
        if mp3_file_counter > 0:
            return self.source_type_mp3_single_folder

        mp3_subfolder_counter = 0
        for r, d, files in os.walk(self.source_folder):
            for filename in fnmatch.filter(files,"*.mp3"):
                return self.source_type_mp3_multi_folder

        # unknown - raise error
        raise EnvironmentError()


    def merge_aac_files_in_working_folder_into_m4b(self):
        # Merge the aac files into a single m4a file

        # count aac files in working folder
        file_counter = len(fnmatch.filter(os.listdir(self.working_folder), '*.aac'))

        merge_commandline_head = 'ffmpeg -i "concat:'
        merge_commandline_body = ""
        merge_commandline_tail = '" -c copy ' + '"' + self.working_folder + self.source_book_folder_name + '.m4a"'

        file_merge_iterator = 0
        while file_merge_iterator < file_counter:
            file_merge_iterator += 1
            merge_commandline_body += self.working_folder + "outputfile%03d." % file_merge_iterator + "aac"
            if file_merge_iterator < file_counter:
                merge_commandline_body += "|"

        merge_command = merge_commandline_head + merge_commandline_body + merge_commandline_tail

        args = shlex.split(merge_command)

        # Now run the merge process for this book - results in m4a containing all aac file content
        subprocess.run(args)

        # rename to m4b
        os.rename(self.working_folder + self.source_book_folder_name + '.m4a',
                  self.working_folder + self.source_book_folder_name + '.m4b')

    def extract_aac_from_files_in_working_folder(self, extension):
        # Extract m4a/m4b files into a multiple aac files

        file_counter = len(fnmatch.filter(os.listdir(self.working_folder), '*.' + extension))

        file_extract_iterator = 0
        while file_extract_iterator < file_counter:
            file_extract_iterator += 1
            extract_commandline = 'ffmpeg -i ' + '"' + self.working_folder + "outputfile%03d." % file_extract_iterator \
                                  + extension + '"' + ' -acodec copy "' + self.working_folder \
                                  + "outputfile%03d." % file_extract_iterator + 'aac"'
            args = shlex.split(extract_commandline)
            subprocess.run(args)

    def encode_mp3_files_in_source_folder(self, bitrate):
        self.encode_mp3_files_in_folder(self.source_folder, bitrate)

    def encode_mp3_files_in_working_folder(self, bitrate):
        self.encode_mp3_files_in_folder(self.working_folder, bitrate)

    def encode_mp3_files_in_folder(self, parent_folder, bitrate):
        # get the list of files in good order
        raw_file_list = os.listdir(parent_folder)
        raw_file_list.sort()

        files_counter = 0
        files_complete = 0
        files_total = len(raw_file_list)
        encode_counter = 0
        encodes_in_progress = 0
        reference_to_popens = {}

        while True:

            # check for encodes that have finished
            for key, value in reference_to_popens.items():

                if value.poll() is None:
                    time.sleep(.1)
                else:
                    # delete item
                    del reference_to_popens[key]

                    # update counter
                    encodes_in_progress -= 1
                    files_complete += 1
                    output_line = "\rEncoding to aac - " + str(files_complete) \
                                + " of " + str(files_total) + " files complete"
                    sys.stdout.write(output_line)
                    break

            # start some new encodes if a thread is free
            if encodes_in_progress < self.threads_to_manage:
                while encodes_in_progress < self.threads_to_manage and files_counter < files_total:

                    files_counter += 1

                    if files_counter > files_total:
                        break

                    filename =  raw_file_list[files_counter - 1]

                    if filename.startswith('.'):
                        # skip this file
                        files_complete += 1

                    elif filename.upper().endswith(".MP3"):

                        encode_counter += 1

                        # start encode
                        output_filename = self.working_folder + "outputfile%03d.aac" % encode_counter

                        command_line = 'ffmpeg -i "' + parent_folder + filename + '"'
                        command_line += ' -loglevel panic -y -c:a aac -b:a  '
                        command_line += bitrate + ' "' + output_filename + '"'

                        args = shlex.split(command_line)

                        # launch the recode in the background..
                        p = subprocess.Popen(args)
                        reference_to_popens[encode_counter] = p

                        encodes_in_progress += 1

                    else:
                        # skip this file
                        files_complete += 1

            if files_complete >= files_counter:
                break

            time.sleep(.1)

    def copy_files_to_working_folder(self, extension):
        # for each aac file in source folder, copy to working folder
        raw_file_list = os.listdir(self.source_folder)
        raw_file_list.sort()

        file_counter = 0
        for rawfile in raw_file_list:
            if rawfile.startswith('.'):
                print('skipping hidden file ' + rawfile)
            elif rawfile.endswith('.' + extension) :
                file_counter += 1
                output_filename = self.working_folder + "outputfile%03d."% file_counter + extension

                shutil.copy(self.source_folder + rawfile, output_filename)

    def deepcopy_mp3_files_to_working_folder(self):
        file_counter = 0

        for src_dir, dirs, files in os.walk(self.source_folder):
            for filename in fnmatch.filter(files,"*.mp3"):
                file_counter += 1
                output_filename = self.working_folder + "outputfile%03d."% file_counter + 'mp3'

                shutil.copy(src_dir + "/" + filename, output_filename)

    def archive_source_files(self):
        # move source folder to the archive folder
        shutil.move(self.source_folder, self.archive_folder)

        time.sleep(1) # wait for transfer to complete

        # 7zip with ultra settings the source folder
        commandline = '7zr a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on'
        commandline += ' "' + self.archive_folder + self.source_book_folder_name + '.7z"'
        commandline += ' "' + self.archive_folder + self.source_book_folder_name + '/"'

        args = shlex.split(commandline)

        # compress the source media files
        p = subprocess.call(args)

        # delete the uncompressed source media files
        commandline = 'rm -rf "' + self.archive_folder + self.source_book_folder_name + '/"'

        args = shlex.split(commandline)

        # delete the uncompressed source media files
        p = subprocess.call(args)

    def determine_bitrate_from_mp3_file(self, folder):
        # Table of appropriate bit rates for spoken word content
        ##################################################################
        #            # <22.05 KHz # 22.05KHz   # 44.1 KHz   # >44.1KHz   #
        ##################################################################
        # Stereo     #  32 Kbps   #  48 Kbps   #  64 Kbps   #  96 Kbps   #
        # Mono       #  32 Kbps   #  32 Kbps   #  48 Kbps   #  80 Kbps   #
        ##################################################################

        bitrate = "64k"  # default - should always be overridden

        try:
            mp3_file_path = ""

            raw_file_list = os.listdir(folder)
            for raw_file in raw_file_list:
                if raw_file.upper().endswith('.MP3') and not(raw_file.startswith('.')):
                    mp3_file_path = folder + raw_file
                    break

            print("pull bitrate from " + mp3_file_path)

            mp3Info = MP3(mp3_file_path)

            # determine input channels - stereo or mono?
            input_channels = mp3Info.info.channels

            # determine input frequency in Hz
            input_freq = mp3Info.info.sample_rate

            if input_channels > 1 and input_freq > 44100:
                bitrate = "96k"
            elif input_freq > 44100:
                bitrate = "80k"
            elif input_channels > 1 and input_freq > 44000:
                bitrate = "64k"
            elif input_freq > 44000:
                bitrate = "48k"
            elif input_channels > 1 and input_freq > 22000:
                bitrate = "32k"
            elif input_freq > 22000:
                bitrate = "32k"
            elif input_channels > 1:
                bitrate = "32k"
            else:
                bitrate = "32k"

            bitrateMessage = "As the input file is " + str(input_freq) + "Hz"
            bitrateMessage += " and is " + str(input_channels) + " channel"
            bitrateMessage += ", use a bitrate of " + bitrate

            print(bitrateMessage)

        except:
            print('Could not determine bitrate from file, using default of 64k')

        return bitrate

    def set_metadata_on_m4b_audiobook_file(self):
        # open current metadata
        m4b_path = self.working_folder + self.source_book_folder_name + ".m4b"
        mp4_info = MP4(m4b_path)

        # set minimal tags
        mp4_info['\xa9ART'] = self.author
        mp4_info['\xa9alb'] = self.title

        mp4_info.save()

        self.set_metadata_cover_image_on_m4b_audiobook_file(m4b_path)

    def set_metadata_cover_image_on_m4b_audiobook_file(self, m4b_file_path):

        # open current metadata
        mp4_info = MP4(m4b_file_path)

        # find cover image
        cover_type = "none"
        cover_file = ""
        if os.path.isfile(self.source_folder + "cover.jpg"):
            cover_file = self.source_folder + "cover.jpg"
            cover_type = 'jpg'
        if os.path.isfile(self.source_folder + "cover.png"):
            cover_file = self.source_folder + "cover.png"
            cover_type = 'png'

        # look for any image file in the input folder if cover image doesn't exist
        if cover_type == "none":
            book_folder_file_list = os.listdir(self.source_folder)

            for book_folder_file in book_folder_file_list:
                if book_folder_file.endswith(".jpg"):
                    cover_type = 'jpg'
                    cover_file = self.source_folder + book_folder_file
                    break

                if book_folder_file.endswith(".png"):
                    cover_type = 'png'
                    cover_file = self.source_folder + book_folder_file
                    break

        if cover_type != "none":
            with open(cover_file, "rb") as f:
                if cover_type == "jpg":
                    mp4_info['covr'] = [
                        MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
                    ]
                else:
                    mp4_info['covr'] = [
                        MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_PNG)
                    ]

        mp4_info.save()

    def move_completed_encode_to_output_folder(self):
        shutil.move(self.working_folder + self.source_book_folder_name + '.m4b', self.output_folder)

    def clear_working_folder(self):
        shutil.rmtree(self.working_folder)




