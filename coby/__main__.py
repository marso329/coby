#!/bin/python3
#start = := creation | assignment

#creation := creates "=" rule(args)

#creates := items

#items := name | enumerated

#rule := name

#name := string

#args is optional
#args :=   name=items{","name=items} 

#enumerated := [name {, name}]

#terminals= "=","(",")",string,"[","]"

import argparse

import coby
from coby import BuildDirectory
from coby import scanner
import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger("coby")
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)

def buildDirectory(ruleFile,targetFile,target,threads):
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    if threads:
        buildDir.setThreads(threads)
    if type(target)==str and target.lower()=="all":
        buildDir.buildAll()
    else:    
        buildDir.build()    

def generateDotFunction(arguments):
    ruleFile=None
    if arguments.rule:
        ruleFile=arguments.ruleFile
    targetFile=None
    if arguments.targetFile:
        targetFile=arguments.targetFile
    if not arguments.output:
        raise RuntimeError("generateDot requires an output file")
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    target=None
    if arguments.target:
        target=arguments.target
    buildDir.generateDot(arguments.output,target)    

def buildFunction(arguments):
    print("building")
    ruleFile=None
    if arguments.ruleFile:
        ruleFile=arguments.ruleFile
    targetFile=None
    if arguments.targetFile:
        targetFile=arguments.targetFile
    target=None
    if arguments.target:
        target=arguments.target
    threads=None
    if arguments.threads:
        threads=arguments.threads
    buildDirectory(ruleFile,targetFile,target,threads)

def testScannerFunction(arguments):
    print("printfile")
    if not arguments.file:
        raise RuntimeError("testScanner requires a file")
    print(scanner.scan(arguments.file))

def printBuildFunction(arguments):
    ruleFile=None
    if arguments.ruleFile:
        ruleFile=arguments.ruleFile
    targetFile=None
    if arguments.target:
        targetFile=arguments.target
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    print(buildDir)

def main():
    parser = argparse.ArgumentParser(prog='coby')
    #parser.add_argument('toDo',nargs='?',default="build",type=str)
    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands',help='additional help')
    build=subparsers.add_parser('build')
    build.add_argument('-ruleFile',"-rf")
    build.add_argument('-targetFile',"-tf")
    build.add_argument('-target',"-t")
    build.add_argument('-threads',"-th",type=int,default=8)
    build.set_defaults(func=buildFunction)
    
    testScanner=subparsers.add_parser('testScanner')
    testScanner.add_argument('-file',"-f")
    testScanner.set_defaults(func=testScannerFunction )
    
    generateDot=subparsers.add_parser('generateDot')
    generateDot.add_argument('-output',"-o")
    generateDot.add_argument('-ruleFile',"-rf")
    generateDot.add_argument('-targetFile',"-tf")
    generateDot.add_argument('-target',"-t")
    generateDot.set_defaults(func=generateDotFunction)
    
    printBuild=subparsers.add_parser('printBuild')
    printBuild.add_argument('-ruleFile',"-rf")
    printBuild.add_argument('-targetFile',"-tf")
    printBuild.add_argument('-target',"-t")
    printBuild.set_defaults(func=printBuildFunction)

    arguments = parser.parse_args()
    arguments.func(arguments)

if __name__ == "__main__":
    main()

