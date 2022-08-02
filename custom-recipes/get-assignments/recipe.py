# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import get_assignments_df


input_folder = dataiku.Folder(get_input_names_for_role('input_folder')[0])
input_config_filename = get_recipe_config()['input_config_filename']

exclude_banned = get_recipe_config()['exclude_banned']

environment = get_plugin_config()['environment']
token = get_plugin_config()['token']

toloka_client = TolokaClient(token, environment)

pool = input_folder.read_json(input_config_filename)
assignments_df = get_assignments_df(pool=pool, toloka_client=toloka_client, exclude_banned=exclude_banned)

output_name  = get_output_names_for_role('output_dataset')[0]
dataiku.Dataset(output_name).write_with_schema(assignments_df)