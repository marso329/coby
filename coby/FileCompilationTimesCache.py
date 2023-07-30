import os

class FileCompilationTimesCache:
    def __init__(self):
        self.times={}
        if os.path.isfile("./compilationCache"):
            with open("./compilationCache") as fobj:
                for line in fobj:
                    row = line.split()
                    self.times[row[0]]=float(row[1])
    
    
    def write(self):
        with open("./compilationCache", 'w+') as fobj:
            for fileName in self.times:
                fobj.write('{} {}\n'.format(fileName,self.times[fileName]))
    
    def getCompilationTime(self,fileName):
        if fileName in self.times:
            return self.times[fileName]
        return 0.0
    def setCompilationTime(self,fileName,time):
        self.times[fileName]=time