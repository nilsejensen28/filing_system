'''
This file is used to explore the file structure of a given directory.
It generates a json file that represents the folder structure of the given directory.
'''

import os
import json
import logging
import subprocess
from abc import ABC, abstractmethod

LOGGING_LEVEL = logging.DEBUG
LATEX_TEMPLATE_PATH = 'Templates/folder_structure_template.tex'
LABEL_TYPES = ["hanging", "sticker", "outside_folder", "inside_folder", "none"]
TEMPLATES = {
    "hanging": "Templates/hanging_folder_label_template.tex",
    "sticker": "Templates/sticker_label_template.tex",
    "outside_folder": "",
    "inside_folder": ""
}

'''
This class represents a folder. It is a node in the folder tree.
'''
class Folder:
    name : str #Name of the folder
    id : str #ID of the folder
    label_type : str #Label type of the folder
    subfolders : list #List of subfolders of the folder
    parent = None  #Parent folder of the folder

    def __init__(self, name : str, id : str, label_type="", parent=None):
        self.name = name
        self.id = id
        if not label_type:
            label_type = "none"
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
    
    def __str__(self):
        return f"{self.id} - {self.name}"
    
    def sort_subfolders(self):
        '''Sort the subfolders by id'''
        self.subfolders = sorted(self.subfolders, key=lambda x: x.id)
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
        folder = Folder(json['name'], json['id'], json['label_type'])
        for subfolder in json['subfolders']:
            folder.add_subfolder(self._generate_folder_tree_from_json_recursive(subfolder))
        return folder
    
    def generate_folder_tree_from_path(self, path : os.path, ignore_non_numbered=True):
        '''Generate a folder tree from a given path (directory)'''
        self.root = self._generate_folder_tree_from_path_recursive(path, ignore_non_numbered, root=True)
        pass 

    def _generate_folder_tree_from_path_recursive(self, path : os.path, ignore_non_numbered=True, root=False) -> Folder:
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
            if not ignore_non_numbered or root:
                id = ""
                name = full_name
            else:
                return None
        folder = Folder(name, id)
        #Iterate over the subfolders
        for child in os.listdir(path):
            subfolder = self._generate_folder_tree_from_path_recursive(os.path.join(path, child), ignore_non_numbered)
            if subfolder:
                folder.add_subfolder(subfolder)
        folder.sort_subfolders()
        return folder

    def export_to_file(self, file : os.path):
        '''Export the folder tree to a json file'''
        dict = self.generate_folder_tree_json()
        with open(file, 'w') as file:
            file.write(json.dumps(dict, indent=4, ensure_ascii=False))

    def generate_folder_tree_json(self, sort=True) -> dict:
        '''Generate a json object that represents the folder tree'''
        return self._generate_folder_tree_json_recursive(self.root, sort=sort)

    def _generate_folder_tree_json_recursive(self, folder : Folder, sort=True) -> dict:
        '''Generate a json object that represents the folder tree'''
        logging.debug(f"Generating json for folder {folder}")
        json = {
            'name': folder.name,
            'id': folder.id,
            'label_type': folder.label_type,
            'subfolders': [
                self._generate_folder_tree_json_recursive(subfolder, sort=sort) for subfolder in folder.subfolders
            ]
        }
        #Sort the subfolders by id
        if sort:
            json['subfolders'] = sorted(json['subfolders'], key=lambda x: x['id'])
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
    
    def generate_labels(self, output_dir : os.path, generate_pdf=True):
        '''Generate labels for the folders'''
        label_str = {f"{label_type}": "" for label_type in LABEL_TYPES}
        self._generate_labels_recursively(self.root, label_str)
        for label_type in LABEL_TYPES:
            if label_type not in TEMPLATES.keys():
                continue
            if not TEMPLATES[label_type]:
                continue
            #Copy the template
            with open(TEMPLATES[label_type], 'r') as file:
                latex_template = file.read()
            latex_template = latex_template.replace('##CONTENT##', label_str[label_type])
            output_file = os.path.join(output_dir, label_type + ".tex")
            with open(output_file, 'w') as file:
                file.write(latex_template)
            if generate_pdf:
                subprocess.run(['xelatex', output_file, f'-interaction=nonstopmode -output-directory={output_dir}'])
                logging.info(f"PDF generated and saved to {output_file.replace('.tex', '.pdf')}")
                subprocess.run(['rm', output_file.replace('.tex', '.aux')])
                if not LOGGING_LEVEL == logging.DEBUG:
                    subprocess.run(['rm', output_file.replace('.tex', '.log')])


    def _generate_labels_recursively(self, folder, label_str):
        match folder.label_type:
            case "hanging":
                label_str["hanging"] = label_str["hanging"] + hanging_label_to_latex(folder)
            case "sticker":
                label_str["sticker"] = label_str["sticker"] + hanging_label_to_latex(folder)
            case "outside_folder":
                pass
            case "inside_folder":
                pass
            case "none":
                pass
            case _:
                logging.error(f"{folder.label_type} is not a valid label type")
        for subfolder in folder.subfolders:
            self._generate_labels_recursively(subfolder, label_str)

#--------------------------------------------------------------------------------------
# Different types of label generation
#--------------------------------------------------------------------------------------

def hanging_label_to_latex(folder) -> str:
    '''Generation of Hanging Labels'''
    if folder.parent:
        return f"\\customlabel{{{folder.id}}}{{{folder.parent.name}}}{{{folder.name}}} \n"
    return f"\\customlabel{{{folder.id}}}{{}}{{{folder.name}}} \n"

def sticker_label_to_latex(folder) -> str:
    '''Generation of Stickers'''
    if folder.parent:
        return f"\\customlabel{{{folder.id}}}{{{folder.parent.name}}}{{{folder.name}}} \n"
    return f"\\customlabel{{{folder.id}}}{{}}{{{folder.name}}} \n"
       
def main():
    folder_tree_2 = FolderTree()
    folder_tree_2.generate_folder_tree_from_file("Results/folder_tree.json")
    print(folder_tree_2.generate_folder_tree_json())
    folder_tree_3 = FolderTree()
    folder_tree_3.generate_folder_tree_from_path("0_Test")
    print(folder_tree_2.generate_folder_tree_json())
    folder_tree_3.generate_latex_export("folder_structure.tex")
    folder_tree_2.generate_labels(output_dir="Results")

if __name__ == '__main__':
    logging.basicConfig(level=LOGGING_LEVEL)
    main()