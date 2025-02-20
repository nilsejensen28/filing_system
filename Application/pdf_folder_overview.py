'''
Generate a pdf overview of the folder structure using xelatex and the json file generated by file_structure_explorer.py
'''

import os
import json
import logging
import subprocess

LOGGING_LEVEL = logging.INFO
TEMPLATE_PATH = 'Templates/folder_structure_template.tex'

def generate_pdf_from_json(json_file, output_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    #Copy the template to the output file
    subprocess.run(['cp', TEMPLATE_PATH, output_file])
    #Replace the placeholder with the json data
    with open(output_file, 'r') as f:
        file = f.read()
    content = generate_recursive_latex_tree(data)
    file = file.replace('##FOLDER_STRUCTURE##', content)
    with open(output_file, 'w') as f:
        f.write(file)

    #Generate the pdf
    subprocess.run(['xelatex', output_file])
    logging.info(f"PDF generated and saved to {output_file.replace('.tex', '.pdf')}")
    #Remove the aux files
    subprocess.run(['rm', output_file.replace('.tex', '.aux')])
    if not LOGGING_LEVEL == logging.DEBUG:
        subprocess.run(['rm', output_file.replace('.tex', '.log')])
    
    
def generate_recursive_latex_tree(data):
    logging.debug(f"Generating latex tree for folder: {data['name']}")
    name = "\\textbf{" + data['id'] + "} - " + data['name']
    content = f"[{name} \n"
    for subfolder in data['subfolders']:
        content += generate_recursive_latex_tree(subfolder)
    content += "]"
    logging.debug(f"Latex tree for folder {data['name']} generated")
    return content

def main():
    generate_pdf_from_json('Results/folder_tree.json', 'folder_structure.tex')

if __name__ == '__main__':
    main()