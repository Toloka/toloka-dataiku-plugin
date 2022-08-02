

# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import create_tasks


pool_config_folder = dataiku.Folder(get_input_names_for_role('pool_config_folder')[0])
input_pool_filename = get_recipe_config()['input_pool_filename']
pool = pool_config_folder.read_json(input_pool_filename)

pool_tasks_dataset = get_input_names_for_role('pool_tasks_dataset')
pool_tasks = None
if pool_tasks_dataset:
    pool_tasks_dataset = pool_tasks_dataset[0]
    pool_tasks = dataiku.Dataset(pool_tasks_dataset).get_dataframe()
    
control_tasks_dataset = get_input_names_for_role('control_tasks_dataset')
control_tasks = None
if control_tasks_dataset:
    control_tasks_dataset = control_tasks_dataset[0]
    control_tasks = dataiku.Dataset(control_tasks_dataset).get_dataframe()
    
training_tasks_dataset = get_input_names_for_role('training_tasks_dataset')
training_tasks = None
if training_tasks_dataset:
    training_tasks_dataset = training_tasks_dataset[0]
    training_tasks = dataiku.Dataset(training_tasks_dataset).get_dataframe()

allow_defaults = get_recipe_config().get('allow_defaults')
open_pool = get_recipe_config().get('open_pool')
skip_invalid_items = get_recipe_config().get('skip_invalid_items')

environment = get_plugin_config()['environment']
token = get_plugin_config()['token']

toloka_client = TolokaClient(token, environment)

tasks = create_tasks(pool=pool, pool_tasks=pool_tasks, control_tasks=control_tasks, training_tasks=training_tasks, 
                     allow_defaults=allow_defaults, open_pool=open_pool, skip_invalid_items=skip_invalid_items,
                     toloka_client=toloka_client)

output_folder = dataiku.Folder(get_output_names_for_role('output_folder')[0])
output_tasks_filename = get_recipe_config()['output_tasks_filename']
output_folder.write_json(output_tasks_filename, tasks)