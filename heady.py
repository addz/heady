
# Heady.py
# -----------
# Update source code header comment blocks.
# Adam Muhlbauer (admuhlbauer@gmail.com), http://addz.co

import os
import sys
import fileinput
import argparse


class HeaderReplacer (object):

    def __init__(self, updatedHeaderFilename):
        self.headerFilename = updatedHeaderFilename
        self.sourceFiles = []
        self.deltaSourceFiles = []

        self.updateAll = False
        self.newHeader = None
        self.headerContainsTokens = False
        
    def update(self, rootDir, fileExtensions, updateAll):
        """
        Main interactive process.
        """

        extensions = self.__parseFileExtensions(fileExtensions)
        self.updateAll = updateAll

        print "Source directory: " + rootDir
        print "Extensions: " + ", ".join(extensions)
        print "Header file: " + self.headerFilename

        self.__loadNewHeader()
        self.__showNewHeader()
        
        self.__findSourceFiles(rootDir, extensions)
        self.__showSourceFiles()

        # early exit.
        if (len(self.deltaSourceFiles) == 0 and not self.updateAll) or (len(self.sourceFiles) == 0 and self.updateAll):
            return

        if self.updateAll:
            print "*** Force update of all %i files selected (--all option)" % len(self.sourceFiles)
        
        if (self.__confirmUpdateFromUser()):
            print "Updating headers..."
            self.__performUpdate()
            print "done."
        else:
            print "Aborting. Nothing changed."
            
    def __parseFileExtensions(self, arg):
        """ Extract out file extensions """

        exts = [];
        for ext in arg:
            exts.append(ext.replace('.', ''))
        return set(exts)

    def __findSourceFiles(self, rootDir, fileExtensions):
        """ search the source directory, looking for matching files """

        self.sourceFiles = []
        
        for root, dirs, files in os.walk(rootDir):  #@UnusedVariable
            # ignore hidden dirs
            for d in dirs:
                if d.startswith('.'):
                    dirs.remove(d)
            
            # find matching files
            for filename in files:
                fileExt = os.path.splitext(filename)
                if fileExt[1][1:] in fileExtensions:
                    fullFilename = os.path.join(root, filename)
                    
                    self.sourceFiles.append(fullFilename)
                    
                    if not self.__headerMatches(fullFilename):
                        self.deltaSourceFiles.append(fullFilename);

    def __headerMatches(self, filename):
        """ 
        return True of the given filename has the same header as what we're 
        using as a replacement.
        """
        header = self.__loadHeader(filename)
        return header == self.newHeader


    def __loadHeader(self, filename):
        """ load the header of a file """

        inHeader = True
        openBlock = False
        header = []

        for line in fileinput.input (filename):
            content = line.strip()

            # track /* */ blocks
            if content.startswith('/*'):
                openBlock = True
         
            if inHeader and not content.startswith('//') and not (len(line) == 0 or line == '\n') and not openBlock:    
                inHeader = False

            if inHeader and not (len(line) == 0 or line == '\n'):
                header.append(line)

            if content.startswith('*/'):
                openBlock = False

        return header

    def __loadNewHeader(self):
        """ Load the new header to use as a replacement """
        self.newHeader = self.__loadHeader(self.headerFilename)
        
    def __showSourceFiles(self):
        """ Show the files we're going to update """

        numOfFiles = len(self.sourceFiles)
        numOfDeltaFiles = len(self.deltaSourceFiles)

        msg = ''
        if numOfFiles > 0:
            msg = "found %i %s, " % (numOfFiles, self.__plural("file", numOfFiles))

            if numOfDeltaFiles > 0:
                filesWord = self.__plural("file", numOfDeltaFiles)
                msg += "%i %s to update.\n\n" % (numOfDeltaFiles, filesWord)
                
                msg += "%s to update:\n" % filesWord
                for filename in self.deltaSourceFiles:
                    msg += "\t" + filename + "\n"
            else:
                msg += "all files are up to date."
        else:
            msg = "No files found with given extensions."

        print msg

    def __plural(self, word, count):
        s = word
        if count > 1 or count == 0:
            s += "s"
        return s

    def __showNewHeader(self):
        print "New Header is: "
        for line in self.newHeader:
            sys.stdout.write(line)
        print "\n"


    def __confirmUpdateFromUser(self):
        print ""
        try:
            response = raw_input('Are you sure you want to update these files? [yes/no] > ')
        except KeyboardInterrupt:
            print "\n"
            return False
        
        return response.lower().startswith('y')

    def __performUpdate(self):
        """ Do the actual file update. """

        files = self.deltaSourceFiles
        if self.updateAll:
            files = self.sourceFiles

        for filename in files:
            print "\tupdating %s" % filename
            self.__updateHeader(filename)
                
    def __updateHeader(self, filename):
        """ replace the old header with the new one """

        newHeaderWritten = False
        inHeader = True
        openBlock = False
        
        for line in fileinput.input (filename,inplace=1):
            
            content = line.strip()

            # insert new header
            if not newHeaderWritten:
                for headLine in self.newHeader:
                    sys.stdout.write(headLine)
                print ""
                newHeaderWritten = True

            # track /* */ blocks
            if content.startswith('/*'):
                openBlock = True

            # skip over old header on re-write.        
            if inHeader and not content.startswith('//') and not (len(line) == 0 or line == '\n') and not openBlock:    
                inHeader = False

            if content.startswith('*/'):
                openBlock = False
                #line  = ''

            if not inHeader:
                sys.stdout.write(line)




# script main line

parser = argparse.ArgumentParser(description="heady.py - Update source code header comment blocks.")
parser.add_argument('--sourcedir', dest='sourcedir', help='directory of source code', required=True)
parser.add_argument('--headerfile', dest='headfile', help='Filename of new header file to load from', required=True)
parser.add_argument('--ext', dest='ext', help='file extensions of files to update', required=True, nargs="+")
parser.add_argument('--all', action='store_true', default=False, dest='all')

args = parser.parse_args()

if not os.path.exists(args.sourcedir):
    print "Source directory '%s' does not exist" % args.sourcedir
    exit(1)

if not os.path.exists(args.headfile) or not os.path.isfile(args.headfile):
    print "Header file '%s' does not exist" % args.headfile
    exit(1)

replacer = HeaderReplacer(args.headfile)
replacer.update(args.sourcedir, args.ext, args.all)

