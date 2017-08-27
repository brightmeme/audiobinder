class EncodeBook(object):

    def __init__(self, name, input_folder, working_folder, done_folder, archive_folder):
        """Return an EncodeBook object for the named book"""
        self.name = name
        self.input_folder = input_folder     # folder where unencoded book exists
        self.working_folder = working_folder # folder where work is to be done
        self.done_folder = done_folder       # folder where encoded output is to be stored
        self.archive_folder = archive_folder # folder where archived pre-encoding book is to be stored

    def encode(self):

        # determine bitrate

        # setup working folder

        # encode audio to aac in working folder

        # combine aac files into single m4a

        # rename to m4b - the audiobook filename

        # set metadata

        # move source folder to archive folder

        # compress source folder

        # clear working folder


    def archive(self):


