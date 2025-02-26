'''
This file is used to explore the file structure of a given directory.
It generates a json file that represents the folder structure of the given directory.
'''

import os
import json
import logging
import subprocess
from abc import ABC, abstractmethod

LOGGING_LEVEL = logging.INFO
LATEX_TEMPLATE_PATH = 'Templates/folder_structure_template.tex'
LABEL_TYPES = ["hanging", "sticker", "outside_folder", "inside_folder"]

'''
This class represents a folder. It is a node in the folder tree.
'''
class Folder:
    name : str #Name of the folder
    id : str #ID of the folder
    label_type : str #Physical location of the folder
    subfolders : list #List of subfolders of the folder
    parent = None  #Parent folder of the folder

    def __init__(self, name : str, id : str, label_type="", parent=None):
        self.name = name
        self.id = id
        self.label_type = label_type
        self.subfolders = []
        self.parent = parent

    def add_subfolder(self, subfolder):
        '''Add a subfolder to the folder'''
        self.subfolders.append(subfolder)
        subfolder.parent = self

    def remove_subfolder(self, subfolder):
        '''Remove a subfolder from the folder'''
        self.subfolders.remove(subfolder)
        subfolder.parent = None

    def perform_check(self) -> bool:
        '''Perform a check on the folder'''
        if not self.name:
            logging.error("Folder name is empty")
            return False
        if not self.id:
            logging.error("Folder ID is empty")
            return False
        if not self.label_type in LABEL_TYPES:
            logging.error(f"Invalid label type {self.label_type}")
            return False
        return True
    
''' 

This class represents a folder tree. It is a tree structure that represents the folder structure of a given directory.
Every node in the tree is a Folder object.
'''
class FolderTree:
    root = None #Top level folder of the folder tree

    def __init__(self):
        pass
    
    def generate_folder_tree_from_file(self, file : os.path):
        '''Generate a folder tree from a json file'''
        with open(file, 'r') as file:
            json_dump = json.load(file)
        self.root = self._generate_folder_tree_from_json_recursive(json_dump)

    def _generate_folder_tree_from_json_recursive(self, json : dict) -> Folder:
        '''Generate a folder tree from a json object'''
        folder = Folder(json['name'], json['id'], json['physical_location'])
        for subfolder in json['subfolders']:
            folder.add_subfolder(self._generate_folder_tree_from_json_recursive(subfolder))
        return folder
    
    def generate_folder_tree_from_path(self, path : os.path):
        '''Generate a folder tree from a given path (directory)'''
        self.root = self._generate_folder_tree_from_path_recursive(path)
        pass 

    def _generate_folder_tree_from_path_recursive(self, path : os.path, ignore_non_numbered=True) -> Folder:
        '''Generate a folder tree from a given folder'''
        #Check if the folder is a directory
        if not os.path.isdir(path):
            return None
        #Create a folder object
        full_name = os.path.basename(path)
        id = full_name.split('_')[0]
        try :
            int(id)
            name = " ".join(full_name.split('_')[1:])
        except ValueError:
            if not ignore_non_numbered:
                id = ""
                name = full_name
            else:
                return None
        folder = Folder(name, id)
        #Iterate over the subfolders
        for child in os.listdir(path):
            subfolder = self._generate_folder_tree_from_path_recursive(os.path.join(path, child))
            if subfolder:
                folder.add_subfolder(subfolder)
        return folder

    def export_to_file(self, file : os.path):
        '''Export the folder tree to a json file'''
        dict = self.generate_folder_tree_json()
        with open(file, 'w') as file:
            file.write(json.dumps(dict, indent=4, ensure_ascii=False))

    def generate_folder_tree_json(self) -> dict:
        '''Generate a json object that represents the folder tree'''
        return self._generate_folder_tree_json_recursive(self.root)

    def _generate_folder_tree_json_recursive(self, folder : Folder) -> dict:
        '''Generate a json object that represents the folder tree'''
        json = {
            'name': folder.name,
            'id': folder.id,
            'physical_location': folder.physical_location,
            'subfolders': [
                self._generate_folder_tree_json_recursive(subfolder) for subfolder in folder.subfolders
            ]
        }
        return json
    
    def generate_latex_export(self, output_file : os.path, generate_pdf=True):
        '''Generate a latex file that represents the folder tree'''
        with open(LATEX_TEMPLATE_PATH, 'r') as file:
            latex_template = file.read()
        latex_template = latex_template.replace('##FOLDER_STRUCTURE##', self._generate_latex_tree_recursive(self.root))
        with open(output_file, 'w') as file:
            file.write(latex_template)
        if generate_pdf:
            subprocess.run(['xelatex', output_file, '-interaction=nonstopmode'])
            logging.info(f"PDF generated and saved to {output_file.replace('.tex', '.pdf')}")
            subprocess.run(['rm', output_file.replace('.tex', '.aux')])
            if not LOGGING_LEVEL == logging.DEBUG:
                subprocess.run(['rm', output_file.replace('.tex', '.log')])

    def _generate_latex_tree_recursive(self, folder : Folder) -> str:
        name = "\\textbf{" + folder.id + "} - " + folder.name
        content = f"[{name} \n"
        for subfolder in folder.subfolders:
            content += self._generate_latex_tree_recursive(subfolder)
        content += "]"
        return content
    
    def generate_labels(self, output_dir : os.path):
        '''Generate labels for the folders'''
        labels = {}


class AbstractLabel(ABC):
    folder: Folder
    template_file: str

    def __init__(self, folder: Folder, type: str):
        self.folder = folder
    
    @abstractmethod
    def to_latex(self) -> str:
        pass

class HangingFolderLabel(AbstractLabel):
    template_file = 'Templates/hanging_folder_label_template.tex'

    def to_latex(self) -> str:
        if self.folder.parent:
            return f"\\customlabel{{{self.folder.id}}}{{{self.folder.parent.name}}}{{{self.folder.name}}}"
        return f"\\customlabel{{{self.folder.id}}}{{}}{{{self.folder.name}}}"

       
def main():
    folder_tree = FolderTree()
    folder_tree.generate_folder_tree_from_file("Results/folder_tree.json")
    print(folder_tree.generate_folder_tree_json())
    folder_tree_2 = FolderTree()
    folder_tree_2.generate_folder_tree_from_path("0_Test")
    print(folder_tree_2.generate_folder_tree_json())
    folder_tree_2.generate_latex_export("folder_structure.tex")
    folder = Folder("Test", "0")
    label = HangingFolderLabel(folder, "hanging")
    print(label.to_latex())

if __name__ == '__main__':
    logging.basicConfig(level=LOGGING_LEVEL)
    main()