

# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import create_training


input_folder = dataiku.Folder(get_input_names_for_role('input_folder')[0])
input_config_filename = get_recipe_config()['input_config_filename']
training_config = input_folder.read_json(input_config_filename)

project_config_folder = dataiku.Folder(get_input_names_for_role('project_config_folder')[0])
input_project_filename = get_recipe_config().get('input_project_filename')
project = project_config_folder.read_json(input_project_filename)

environment = get_plugin_config()['environment']
token = get_plugin_config()['token']

toloka_client = TolokaClient(token, environment)

training = create_training(training_config, project=project, toloka_client=toloka_client)

output_folder = dataiku.Folder(get_output_names_for_role('output_folder')[0])
output_training_filename = get_recipe_config()['output_training_filename']
output_folder.write_json(output_training_filename, training)