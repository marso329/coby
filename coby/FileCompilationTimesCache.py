import os

class FileCompilationTimesCache:
    def __init__(self,directory):
        self.times={}
        self.directory=directory
        self.fileName=self.directory+os.sep+"compilationCache"
        if os.path.isfile( self.fileName):
            with open(self.fileName) as fobj:
                for line in fobj:
                    row = line.split()
                    self.times[row[0]]=float(row[1])
    
    
    def write(self):
        with open(self.fileName, 'w+') as fobj:
            for fileName in self.times:
                fobj.write('{} {}\n'.format(fileName,self.times[fileName]))
    
    def getCompilationTime(self,fileName):
        if fileName in self.times:
            return self.times[fileName]
        return 0.0
    def setCompilationTime(self,fileName,time):
        self.times[fileName]=time