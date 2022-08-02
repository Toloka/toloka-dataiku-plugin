import json
import pandas as pd
import pickle

from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any, Callable, Type, List

from toloka.client import Task, unstructure

# To avoid `structure` pickling errors.
import toloka.client as _toloka_client_lib


_json_loads = partial(json.loads, parse_float=Decimal)


def structure_from_conf(obj: Any, cl: Type) -> object:
    if isinstance(obj, cl):
        return obj
    if isinstance(obj, bytes):
        try:
            return pickle.loads(obj)
        except Exception:
            pass
        obj = obj.decode()
    if isinstance(obj, str):
        obj = _json_loads(obj)
    return _toloka_client_lib.structure(obj, cl)


def extract_id(obj: Any, cl: Type) -> str:
    if isinstance(obj, str):
        try:
            obj = _json_loads(obj)
        except Exception:
            return obj
        if isinstance(obj, int):
            return str(obj)
    res = structure_from_conf(obj, cl).id
    if res is None:
        raise ValueError(f'Got id=None from: {obj}')
    return res


def unstructured(func: Callable) -> Callable:
    def _wrapper(
        *args,
        __func: Callable,
        **kwargs
    ) -> Any:
        obj = __func(*args, **kwargs)
        return unstructure(obj)

    return partial(_wrapper, __func=func)


class TaskType(Enum):
    POOL = 'POOL'
    TRAINING = 'TRAINING'
    HONEYPOT = 'HONEYPOT'


def init_pool_tasks(tasks_df: pd.DataFrame, pool_id: str) -> List[Task]:
    tasks: List[Task] = []

    headings = [
        column_name for column_name in tasks_df.columns if column_name.startswith('INPUT:')]

    for _, row in tasks_df.iterrows():
        tasks.append(
            Task(input_values={field[len('INPUT:'):]: row[field] for field in headings if not pd.isna(row[field])},
                 pool_id=pool_id))

    return tasks


def init_control_tasks(tasks_df: pd.DataFrame, pool_id: str) -> List[Task]:
    tasks: List[Task] = []

    input_headings = [column_name for column_name in tasks_df.columns if
                      column_name.startswith('INPUT:')]
    golden_headings = [column_name for column_name in tasks_df.columns if
                       column_name.startswith('GOLDEN:')]

    for _, row in tasks_df.iterrows():
        known_solutions = [{'output_values': {field[len('GOLDEN:'):]: row[field] for field in golden_headings if
                                              not pd.isna(row[field])}}]
        tasks.append(Task(
            input_values={field[len('INPUT:'):]: row[field]
                          for field in input_headings if not pd.isna(row[field])},
            known_solutions=known_solutions,
            pool_id=pool_id))

    return tasks


def init_training_tasks(tasks_df: pd.DataFrame, pool_id: str) -> List[Task]:
    tasks: List[Task] = []

    input_headings = [column_name for column_name in tasks_df.columns if
                      column_name.startswith('INPUT:')]
    golden_headings = [column_name for column_name in tasks_df.columns if
                       column_name.startswith('GOLDEN:')]
    hint_headings = [column_name for column_name in tasks_df.columns if
                     column_name.startswith('HINT:')]

    for _, row in tasks_df.iterrows():
        known_solutions = [{'output_values': {field[len('GOLDEN:'):]: row[field] for field in golden_headings if
                                              not pd.isna(row[field])}}]
        if len(hint_headings) > 0:
            hint = f'Correct solution: {"".join(row[field] for field in hint_headings if not pd.isna(row[field]))}'
        else:
            hint = f'Correct solution: {"".join(row[field] for field in golden_headings if not pd.isna(row[field]))}'

        tasks.append(Task(
            input_values={field[len('INPUT:'):]: row[field]
                          for field in input_headings if not pd.isna(row[field])},
            known_solutions=known_solutions,
            message_on_unknown_solution=hint,
            pool_id=pool_id))

    return tasks


def get_task_from_fields(row: pd.Series, field_type: str):
    values_lst = [val for idx, val in row.iteritems() if idx.startswith(field_type)]
    if len(values_lst) == 1:
        return values_lst[0]
    elif len(values_lst) > 1:
        return "|".join([val for idx, val in row if idx.startswith(field_type)])
    else:
        return ""
