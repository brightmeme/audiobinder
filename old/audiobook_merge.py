from clint import arguments
import fnmatch
import os
from subprocess import call

args = arguments.Args()
bookname = args.get(0)
bookfilename = bookname + ".m4b"

devnull = open(os.devnull, 'w')

#print "bookname - " + bookname
#print "bookfilename - " + bookfilename

filelist = []
files = [f for f in os.listdir('.') if os.path.isfile(f)]
for f in files:
    if fnmatch.fnmatch(f, bookname+'*'):
        filelist.append(f)

filelist = sorted(filelist)

if len(filelist) > 1:

    # copy the first file to the final m4b filename
    #print "copying first file - " + filelist[0]
    cmdline = 'cp "' + filelist[0] + '" "' + bookfilename + '"'
    #print cmdline
    call(cmdline, shell=True, stdout=devnull, stderr=devnull)
    filelist.remove(filelist[0])

    # use MP4Box to concatenate the other file to the first
    catlist = ''
    for file in filelist:
        catlist += ' -cat "' + file + '"'
 
    cmdline = 'MP4Box ' + catlist + ' "' + bookfilename + '"'
    #print cmdline
    call(cmdline, shell=True, stdout=devnull, stderr=devnull)
else:
    print "Not enough files found to merge!"
