# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import wait_pool


input_folder = dataiku.Folder(get_input_names_for_role('input_folder')[0])
input_config_filename = get_recipe_config()['input_config_filename']

check_period = get_recipe_config()['check_period']
open_pool = get_recipe_config().get('open_pool')

environment = get_plugin_config()['environment']
token = get_plugin_config()['token']

toloka_client = TolokaClient(token, environment)

pool = input_folder.read_json(input_config_filename)
pool = wait_pool(pool=pool, period=check_period, open_pool=open_pool, toloka_client=toloka_client)

output_folder = dataiku.Folder(get_output_names_for_role('output_folder')[0])
output_pool_filename = get_recipe_config()['output_pool_config_filename']
output_folder.write_json(output_pool_filename, pool)