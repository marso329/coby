import re
import coby
from coby import BuildDirectory

class TargetFile:
    def __init__(self,buildDir,fileName):
        with open(fileName) as f:
            for line in f:
                if line[0]!="\n" and line[0]!="#":
                    split_line=re.split('([,|(|)|=|\]|\[|@])', line)
                    clean_line = [i for i in split_line if i and i!="\n"]
                    self.match(buildDir,clean_line)


    def at(self,line):
        if not line:
            return False,"",line
        if line[0]=="@":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line

    def right_parenthesis(self,line):
        if not line:
            return False,"",line
        if line[0]==")":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line


    def left_parenthesis(self,line):
        if not line:
            return False,"",line
        if line[0]=="(":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line

    def comma(self,line):
        if not line:
            return False,"",line
        if line[0]==",":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line

    def left_square_bracket(self,line):
        if not line:
            return False,"",line
        if line[0]=="[":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line

    def right_square_bracket(self,line):
        if not line:
            return False,"",line
        if line[0]=="]":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line

    def equal(self,line):
        if not line:
            return False,"",line
        if line[0]=="=":
            val=line[0]
            line=line[1:]
            return True,val,line
        return False,"",line


    def args(self,line):
        success,arg_name,new_line=self.name(line)
        if not success:
            return True,{},line
        success,val,new_line=self.equal(new_line)
        if not success:
            return True,{},line 
        success,arg_val,new_line=self.items(new_line)
        if not success:
            return True,{},line 
        result={}
        result[arg_name]=arg_val
        #start repetition
        while True:
            success,val,new_line_second=self.comma(new_line)
            if not success:
                break
            success,arg_name,new_line_second=self.name(new_line_second)
            if not success:
                break
            success,val,new_line_second=self.equal(new_line_second)
            if not success:
                break
            success,arg_val,new_line_second=self.items(new_line_second)
            if not success:
                break
            new_line=new_line_second
            result[arg_name]=arg_val
        return True, result,new_line

    def enumerated(self,line):
        success,val,new_line=self.left_square_bracket(line)
        if not success:
            return False,"",line
        success,val,new_line=self.name(new_line)
        if not success:
            return False,"",line 
        result=[]
        result.append(val)
        #start repetition
        while True:
            success,val,new_line_second=self.comma(new_line)
            if not success:
                break
            success,val,new_line_second=self.name(new_line_second)
            if not success:
                break
            new_line=new_line_second
            result.append(val)
        success,val,new_line=self.right_square_bracket(new_line)
        if not success:
            return False,"",line
        return True, result,new_line    

    def name(self,line):
        if not line:
            return False,"",line
        _rex = re.compile("[/0-9a-zA-Z._-]+$")
        if _rex.match(line[0]):
            val=line[0]
            val=val.replace("\n","")
            line=line[1:]
            return True,val,line
        return False,"",line

    def items(self,line):
        success,val,new_line=self.name(line)
        if not success:
            success,val,new_line=self.enumerated(line)
            if not success:
                return False,"",line
        return success,val,new_line


    def creates(self,line):
        success,val,new_line=self.items(line)
        if not success:
            return False,"",line
        return success,val,new_line

    def creation(self,buildDir : BuildDirectory,line):
        success,valCreates,new_line=self.creates(line)
        if not success:
            return False,"",line
        success,val,new_line=self.equal(new_line)
        if not success:
            return False,"",line
        success,valName,new_line=self.name(new_line)
        if not success:
            return False,"",line
        success,val,new_line=self.left_parenthesis(new_line)
        if not success:
            return False,"",line
        success,valArgs,new_line=self.args(new_line)
        if not success:
            return False,"",line
        success,val,new_line=self.right_parenthesis(new_line)
        if not success:
            return False,"",line
        targets=[]
        if type(valCreates)==str:
            targets.append(valCreates)
        elif type(valCreates)==list:
            targets=valCreates
        else:
            raise RuntimeError("undefined type")
        for element in targets:
            if buildDir.findTarget(element):
                raise RuntimeError("duplicate target name {}".format(element))
            target=BuildDirectory.Target(buildDir)
            target.rule=valName
            target.target=element
            for arg in valArgs:
                if not target.checkSpecialVariables(arg,valArgs[arg]):
                    raise RuntimeError("invalid argument {} for target".format(arg))
            buildDir.targets[element]=target
        return True,"",new_line

    def assignment(self,buildDir : BuildDirectory,line):
        success,val,new_line=self.at(line)
        if not success:
            return False,"",line 
        success,valName,new_line=self.name(new_line)
        if not success:
            return False,"",line
        success,val,new_line=self.equal(new_line)
        if not success:
            return False,"",line
        success,valItems,new_line=self.items(new_line)
        if not success:
            return False,"",line
        if not buildDir.checkSpecialVariables(valName,valItems):
            raise RuntimeError("Undefined variable {} in target file".format(valName))
        return True,"",new_line

    def start(self,buildDir : BuildDirectory,line):
        success,val,new_line= self.creation(buildDir,line)
        if success:
            return success,val,new_line
        return self.assignment(buildDir,line)

    def match(self,buildDir : BuildDirectory,line):
        success,val,new_line= self.start(buildDir,line)
        assert success
        assert len(new_line)==0