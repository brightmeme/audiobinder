from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
import os


class Audiobook:

    def determine_bitrate_from_mp3_file(self, mp3_file_path):
        # Table of appropriate bit rates for spoken word content
        ##################################################################
        #            # <22.05 KHz # 22.05KHz   # 44.1 KHz   # >44.1KHz   #
        ##################################################################
        # Stereo     #  32 Kbps   #  48 Kbps   #  64 Kbps   #  96 Kbps   #
        # Mono       #  32 Kbps   #  32 Kbps   #  48 Kbps   #  80 Kbps   #
        ##################################################################

        print("pull bitrate from " + mp3_file_path)

        mp3Info = MP3(mp3_file_path)

        # determine input channels - stereo or mono?
        input_channels = mp3Info.info.channels

        # determine input frequency in Hz
        input_freq = mp3Info.info.sample_rate

        bitrate = "64k"  # default - should always be overridden
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

        return bitrate

    def set_metadata_on_m4b_audiobook_file(self, m4b_file_path, author_name, book_name, book_folder):
        # set metadata
        mp4Info = MP4(m4b_file_path)

        # set minimal tags
        mp4Info['\xa9ART'] = author_name
        mp4Info['\xa9alb'] = book_name

        # set cover image
        coverType = "none"
        coverFile = ""
        if os.path.isfile(book_folder + "/cover.jpg"):
            coverFile = book_folder + "/cover.jpg"
            coverType = 'jpg'
        if os.path.isfile(book_folder + "/cover.png"):
            coverFile = book_folder + "/cover.png"
            coverType = 'png'

        if coverType != "none":
            with open(coverFile, "rb") as f:
                if coverType == "jpg":
                    mp4Info['covr'] = [
                        MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
                    ]
                else:
                    mp4Info['covr'] = [
                        MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_PNG)
                    ]

        mp4Info.save()