import copy
import os
import shutil

class ProjectConf:
    def __init__(self, **dvargs):
        self.dico = dvargs
        self.original_file = None
        self.backup_file = None

    def set_folder(self, folder_path):
        self.original_file = f"{folder_path}/project-conf.h"
        if os.path.exists(self.original_file):
            self.backup_file = f"{folder_path}/project-conf.h.back"
        else:
            self.backup_file = None

    def update_file(self):
        if self.original_file == None:
            return

        lines = []
        last_endif = -1

        if os.path.exists(self.original_file):
            shutil.copy(self.original_file,self.backup_file)
            with open(self.original_file,'r') as f:
                i = 0
                for line in f:
                    if line != "" and line.endswith("#endif"):
                        last_endif = i
                    lines.append(line.strip())
                    i+=1
        else:
            lines = [
                "#ifndef __PROJECT_CONF_H__",
                "#define __PROJECT_CONF_H__",
                "#endif"]
            last_line = -1

        redefines = []
        for name, value in self.dico.items():
            redefines.append(f"#undef {name}")
            if type(value) == str and not value.isupper():
                value = f"\"{value}\""
            redefines.append(f"#define {name} {value}")

        lines = lines[:last_endif] + redefines + lines[last_endif:]

        try:
            with open(self.original_file, "w") as output:
                for line in lines:
                    output.write(f"{line}\n")
        except Exception as e:
            raise Exception("Problem occured while updating 'project-conf.h' file")

    def __setitem__(self, key, value):
        self.dico[key] = value

    def __str__(self):
        return str(self.dico)
    
    def restore_file(self):
        if(self.backup_file != None):
            shutil.copy(self.backup_file, self.original_file)
            os.remove(self.backup_file)
        else:
            os.remove(self.original_file)
