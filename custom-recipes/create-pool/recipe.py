

# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import create_pool


input_folder = dataiku.Folder(get_input_names_for_role('input_folder')[0])
input_config_filename = get_recipe_config()['input_config_filename']
pool_config = input_folder.read_json(input_config_filename)

project_config_folder = dataiku.Folder(get_input_names_for_role('project_config_folder')[0])
input_project_filename = get_recipe_config().get('input_project_filename')
project = project_config_folder.read_json(input_project_filename)

training_config_folder = get_input_names_for_role('training_config_folder')[0]
input_training_filename = get_recipe_config().get('input_training_filename')
if training_config_folder and input_training_filename:
    training_folder = dataiku.Folder(training_config_folder)
    training = training_folder.read_json(input_training_filename)
else:
    training = None
    
pool_expiration_datetime = get_recipe_config().get('pool_expiration_datetime')
pool_expiration_days = get_recipe_config()['pool_expiration_days']

pool_reward_per_assignment = get_recipe_config()['pool_reward_per_assignment'] 

environment = get_plugin_config()['environment']
token = get_plugin_config()['token']

toloka_client = TolokaClient(token, environment)

pool = create_pool(pool_config, project=project, training=training, expiration = pool_expiration_datetime or pool_expiration_days,
                   reward_per_assignment=pool_reward_per_assignment, toloka_client=toloka_client)

output_folder = dataiku.Folder(get_output_names_for_role('output_folder')[0])
output_pool_filename = get_recipe_config()['output_pool_filename']
output_folder.write_json(output_pool_filename, pool)