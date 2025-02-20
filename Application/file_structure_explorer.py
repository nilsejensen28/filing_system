'''
This file is used to explore the file structure of a given directory.
It generates a json file that represents the folder structure of the given directory.

{
    name: "Documents",
    id: "0",
    subfolders: [
        {
            name: "Work",
            id: "1",
            subfolders: [
                {
                    name: "Projects",
                    id: "12",
                    subfolders: []
                }
            ]    
        },
        {
            name: "Personal",
            id: "2",
            subfolders: [
                {
                    name: "Vacation",
                    id: "24",
                    subfolders: []
                }
            ]
        }
    ]

}


'''

import os
import json
import logging

LOGGING_LEVEL = logging.INFO

def generate_folder_tree_recursive(folder, root=False):
    logging.debug(f"Generating folder tree for folder: {os.path.basename(folder)}")
    id = os.path.basename(folder).split('_')[0]
    try:
        int(id)
    except ValueError:
        if not root:
            return None
    if len(os.path.basename(folder).split('_')) == 1:
        if not root:
            return None
        id = ""
        name = os.path.basename(folder)
    else:
        name = " ".join(os.path.basename(folder).split('_')[1:])
    children = []
    for subfolder in os.listdir(folder):
        subfolder_path = os.path.join(folder, subfolder)
        if os.path.isdir(subfolder_path):
            child = generate_folder_tree_recursive(subfolder_path)
            if child:
                children.append(child)
    children.sort(key=lambda x: int(x['id']))
    logging.debug(f"Folder tree for folder {os.path.basename(folder)} generated")
    return {
        'name': name,
        'id': id,
        'subfolders': children
    }

def generate_folder_tree_file(root_folder, output_file, label_type=False):
    logging.info(f"Generating folder tree for folder: {root_folder}")
    folder_tree = generate_folder_tree_recursive(root_folder, root=True)
    if label_type:
        add_label_type_to_tree(folder_tree)
    with open(output_file, 'w') as file:
        file.write(json.dumps(folder_tree, indent=4, ensure_ascii=False))
    logging.info(f"Folder tree generated and saved to {output_file}")

def add_label_type_to_tree(folder_tree):
    folder_tree['physical_location'] = ""
    for subfolder in folder_tree['subfolders']:
        add_label_type_to_tree(subfolder)
    #Reorder the json object for better readability
    childen = folder_tree['subfolders']
    folder_tree.pop('subfolders')
    folder_tree['subfolders'] = childen

def main():
    generate_folder_tree_file('/home/nils/Documents/Documents', 'Results/folder_tree.json', label_type=True)

if __name__ == '__main__':
    logging.basicConfig(level=LOGGING_LEVEL)
    main()