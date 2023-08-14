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


def buildDirectory(ruleFile,targetFile):
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    buildDir.build()    

def generateDotFunction(arguments):
    ruleFile=None
    if arguments.rule:
        ruleFile=arguments.rule
    targetFile=None
    if arguments.target:
        targetFile=arguments.target
    if not arguments.output:
        raise RuntimeError("generateDot requires an output file")
    buildDir=BuildDirectory.BuildDirectory(ruleFile,targetFile)
    buildDir.generateDot(arguments.output)    

def buildFunction(arguments):
    print("building")
    ruleFile=None
    if arguments.rule:
        ruleFile=arguments.rule
    targetFile=None
    if arguments.target:
        targetFile=arguments.target
    buildDirectory(ruleFile,targetFile)

def testScannerFunction(arguments):
    print("printfile")
    if not arguments.file:
        raise RuntimeError("testScanner requires a file")
    print(scanner.scan(arguments.file))

def printBuildFunction(arguments):
    ruleFile=None
    if arguments.rule:
        ruleFile=arguments.rule
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
    build.add_argument('-rule',"-r")
    build.add_argument('-target',"-t")
    build.set_defaults(func=buildFunction)
    
    testScanner=subparsers.add_parser('testScanner')
    testScanner.add_argument('-file',"-f")
    testScanner.set_defaults(func=testScannerFunction )
    
    generateDot=subparsers.add_parser('generateDot')
    generateDot.add_argument('-output',"-o")
    generateDot.add_argument('-rule',"-r")
    generateDot.add_argument('-target',"-t")
    generateDot.set_defaults(func=generateDotFunction)
    
    printBuild=subparsers.add_parser('printBuild')
    printBuild.add_argument('-rule',"-r")
    printBuild.add_argument('-target',"-t")
    printBuild.set_defaults(func=printBuildFunction)

    arguments = parser.parse_args()
    arguments.func(arguments)

if __name__ == "__main__":
    main()

