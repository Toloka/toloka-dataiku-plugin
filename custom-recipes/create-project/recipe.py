

# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import create_project


input_folder = dataiku.Folder(get_input_names_for_role('input_folder')[0])
input_config_filename = get_recipe_config()['input_config_filename']

environment = get_plugin_config()['environment']
token = get_plugin_config()['token']

toloka_client = TolokaClient(token, environment)

project_config = input_folder.read_json(input_config_filename)
project = create_project(project_config, toloka_client=toloka_client)

output_folder = dataiku.Folder(get_output_names_for_role('output_folder')[0])
output_project_filename = get_recipe_config()['output_project_config_filename']
output_folder.write_json(output_project_filename, project)