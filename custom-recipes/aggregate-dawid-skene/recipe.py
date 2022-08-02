# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

import logging
from toloka.client import TolokaClient

from toloka_dataiku import aggregate_dawid_skene


input_name = get_input_names_for_role('input_dataset' )[0]
answers_df = dataiku.Dataset(input_name).get_dataframe()

n_iter = get_recipe_config()['n_iter']

predicted_answers = aggregate_dawid_skene(answers_df, n_iter).to_frame().reset_index()

output_name  = get_output_names_for_role('output_dataset')[0]
dataiku.Dataset(output_name).write_with_schema(predicted_answers)