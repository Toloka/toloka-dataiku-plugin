import logging
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from crowdkit.aggregation import DawidSkene
from toloka.client import Assignment, Pool, Project, Task, TolokaClient, Training
from toloka.client.analytics_request import CompletionPercentagePoolAnalytics
from toloka.client.assignment import GetAssignmentsTsvParameters
from toloka.client.batch_create_results import TaskBatchCreateResult
from toloka.util._managing_headers import add_headers

from ._utils import extract_id, structure_from_conf, unstructured, init_pool_tasks, init_training_tasks, init_control_tasks, get_task_from_fields


@unstructured
@add_headers('dataiku')
def create_project(
    obj: Union[Project, Dict, str, bytes],
    *,
    toloka_client: TolokaClient,
) -> Project:
    """
    Function to create a Toloka `Project` object from given config.

    Args:
        - obj (Project, Dict, str, bytes): Either a `Project` object itself or a config to make a `Project`.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - Project: Toloka project object with id assigned.

    Example:
        # May also be configured toloka.client.Project object.
        >>> project_conf = {...}
        >>> project = create_project(project_conf)
        ...
    """
    obj = structure_from_conf(obj, Project)
    return toloka_client.create_project(obj)


@unstructured
@add_headers('dataiku')
def create_training(
    obj: Union[Training, Dict, str, bytes],
    *,
    project: Union[Project, Dict, str, None] = None,
    project_id: str = None,
    toloka_client: TolokaClient,
) -> Training:
    """
    Function to create a Toloka `Training` pool object from given config.

    Args:
        - obj (Training, Dict, str, bytes): Either a `Training` object itself or a config to make a `Training`.
        - project (Project, Dict, str, optional): Project to assign a training pool to.
            May pass either an object or config value.
        - project_id (str): Project ID to assign a training pool to.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - Training: Toloka training pool object with id assigned.

    Example:
        >>> exam = create_training({...}, project=project)
        ...
    """
    obj = structure_from_conf(obj, Training)
    if project:
        obj.project_id = extract_id(project, Project)
    elif project_id:
        obj.project_id = project_id
    else:
        raise ValueError('Either project or project_id should be set')
    return toloka_client.create_training(obj)


@unstructured
@add_headers('dataiku')
def create_pool(
    obj: Union[Pool, Dict, str, bytes],
    *,
    project: Union[Project, Dict, str, None] = None,
    project_id: str = None,
    training: Union[Training, Dict, str, None] = None,
    training_id: str = None,
    expiration: Union[str, int, None] = None,
    reward_per_assignment: Optional[float] = None,
    toloka_client: TolokaClient,
) -> Pool:
    """
    Function to create a Toloka `Pool` object from given config.

    Args:
        - obj (Pool, Dict, str, bytes): Either a `Pool` object itself or a config to make a `Pool`.
        - project (Project, Dict, str, optional): Project to assign a pool to.
            May pass either an object or config value.
        - project_id (str): Project ID to assign a training pool to.
        - training (Training, Dict, str, optional): Related training pool
            May pass either an object or config value.
        - training_id (str): Related training pool ID
        - expiration (datetime, timedelta, optional): Expiration setting. May pass any of:
            `None` if this setting if already present;
            `datetime` object to set exact datetime;
            `timedelta` to set expiration related to the current time.
        - reward_per_assignment (float, optional): Allow to redefine reward per assignment.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - Pool: Toloka pool object with id assigned.

    Example:
        >>> pool = create_pool({...}, project=project, training=training)
        ...
    """
    obj = structure_from_conf(obj, Pool)
    if project:
        obj.project_id = extract_id(project, Project)
    elif project_id:
        obj.project_id = project_id
    else:
        raise ValueError('Either project or project_id should be set')
    if training or training_id:
        if obj.quality_control.training_requirement is None:
            raise ValueError(
                'pool.quality_control.training_requirement should be set before training assignment')
        obj.quality_control.training_requirement.training_pool_id = extract_id(
            training, Training) or training_id

    if expiration:
        obj.will_expire = datetime.utcnow() + timedelta(days=expiration) if isinstance(expiration,
                                                                                       int) else datetime.fromisoformat(expiration)
    if reward_per_assignment:
        obj.reward_per_assignment = reward_per_assignment
    return toloka_client.create_pool(obj)


@unstructured
@add_headers('dataiku')
def create_tasks(
    *,
    pool: Union[Pool, Training, Dict, str, None] = None,
    pool_id: str = None,
    pool_tasks: Optional[pd.DataFrame] = None,
    control_tasks: Optional[pd.DataFrame] = None,
    training_tasks: Optional[pd.DataFrame] = None,
    allow_defaults: bool = False,
    open_pool: bool = False,
    skip_invalid_items: bool = False,
    toloka_client: TolokaClient,
) -> TaskBatchCreateResult:
    """
    Function to create a list of tasks for a given pool.

    Args:
        - pool (Pool, Training, Dict, str, optional): Allow to set tasks pool.
            May be either a `Pool` or `Training` object or config
        - pool_id (str): Allow to set tasks pool ID.
        - pool_tasks (DataFrame, optional): DataFrame containing pool tasks configuraion.
        - control_tasks (DataFrame, optional): DataFrame containing control tasks configuraion.
            Should contain columns strats with \"GOLDEN\" to represent ground truth.
        - training_tasks (DataFrame, optional): DataFrame containing training tasks configuraion.
            Should contain columns strats with \"GOLDEN\" to represent ground truth.
            Should be chosen in case of Training pool.
        - allow_defaults (bool, optional): Allow to use the overlap that is set in the pool parameters.
        - open_pool (bool, optional): Open the pool immediately after creating a task suite, if the pool is closed.
        - skip_invalid_items (bool, optional): Allow to skip invalid tasks.
            You can handle them using resulting TaskBatchCreateResult object.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - TaskBatchCreateResult: Result object.

    Example:
        >>> tasks = create_tasks(tasks_df,
        ...                      pool_id='some-pool_id-123',
        ...                      open_pool=True,
        ...                      allow_defaults=True)
        ...
    """
    tasks: List[Task] = []
    if pool:
        try:
            pool_id = extract_id(pool, Pool)
        except Exception:
            pool_id = extract_id(pool, Training)
    elif not pool_id:
        raise ValueError("Either pool or pool_id should be set")

    if pool_tasks is not None:
        tasks.extend(init_pool_tasks(pool_tasks, pool_id))
    if control_tasks is not None:
        tasks.extend(init_control_tasks(control_tasks, pool_id))
    if training_tasks is not None:
        tasks.extend(init_training_tasks(training_tasks, pool_id))

    if not tasks:
        raise ValueError(
            "At least one of pool_tasks, control_tasks or training_tasks should be set")

    kwargs = {'allow_defaults': allow_defaults,
              'open_pool': open_pool, 'skip_invalid_items': skip_invalid_items}
    return toloka_client.create_tasks(tasks, **kwargs)


@unstructured
@add_headers('dataiku')
def open_pool(
    *,
    pool: Optional[Union[Pool, Dict, str]] = None,
    pool_id: Optional[str] = None,
    toloka_client: TolokaClient,
) -> Pool:
    """
    Function to open given Toloka pool.

    Args:
        - pool (Pool, Dict, str, optional): Pool or Pool config to be opened.
        - pool_id (str): Pool ID to be opened.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - Pool: Opened pool or training object.

    Example:
        >>> pool = open_pool(pool)
        ...
    """
    if pool:
        pool_id = extract_id(pool, Pool)
    if not pool_id:
        raise ValueError("Either pool or pool_id should be set")

    return toloka_client.open_pool(pool_id)


@unstructured
@add_headers('dataiku')
def open_training(
    *,
    training: Optional[Union[Training, Dict, str]] = None,
    training_id: Optional[str] = None,
    toloka_client: TolokaClient,
) -> Training:
    """
    Function to open given training training.

    Args:
        - training (Training, Dict, str, optional): Training or Training config to be opened.
        - training_id (str): Training ID to be opened.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - Training: Opened training object.

    Example:
        >>> training = open_training(training)
        ...
    """
    if training:
        training_id = extract_id(training, Training)
    if not training_id:
        raise ValueError("Either training or training_id should be set")

    return toloka_client.open_training(training_id)


@unstructured
@add_headers('dataiku')
def wait_pool(
    *,
    pool: Optional[Union[Pool, Dict, str]] = None,
    pool_id: Optional[str] = None,
    period: int = 60,
    open_pool: bool = False,
    toloka_client: TolokaClient,
) -> Pool:
    """
    Function to wait given Toloka pool until close.

    Args:
        - pool (Pool, Training, Dict, str, optional): Either a `Pool` object or it's config.
        - pool_id (str): pool ID.
        - period (timedelta): Interval between checks (in seconds). One minute by default.
        - open_pool (bool, optional): Allow to open pool at start if it's closed. False by default.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - Pool: Toloka pool object.

    Example:
        >>> pool = wait_pool(pool, open_pool=True)
        ...
    """
    if pool:
        pool_id = extract_id(pool, Pool)
    if not pool_id:
        raise ValueError("Either pool or pool_id should be set")

    pool = toloka_client.get_pool(pool_id)
    if pool.is_closed() and open_pool:
        pool = toloka_client.open_pool(pool_id)

    period = timedelta(seconds=period)
    while pool.is_open():
        op = toloka_client.get_analytics(
            [CompletionPercentagePoolAnalytics(subject_id=pool_id)])
        percentage = toloka_client.wait_operation(
            op).details['value'][0]['result']['value']
        logging.info(f'Pool {pool_id} - {percentage}%')

        time.sleep(period.total_seconds())
        pool = toloka_client.get_pool(pool_id)

    return pool


@add_headers('dataiku')
def get_assignments_df(
    status: Union[str, List[str], Assignment.Status,
                  List[Assignment.Status], None] = None,
    *,
    pool: Optional[Union[Pool, Dict, str]] = None,
    pool_id: Optional[str] = None,
    start_time_from: Optional[datetime] = None,
    start_time_to: Optional[datetime] = None,
    exclude_banned: bool = False,
    field: Optional[List[GetAssignmentsTsvParameters.Field]] = None,
    toloka_client: TolokaClient
) -> pd.DataFrame:
    """
    Function to get pool assignments of selected statuses in Pandas `DataFrame` format useful for aggregation.

    Args:
        - pool (Pool, Training, Dict, str, optional): Either a `Pool` object or it's config.
        - pool_id (str): pool ID.
        - status (str, List[str], optional): A status or a list of statuses to get.
            All statuses (None) by default.
        - start_time_from (str, optional): Upload assignments submitted after the specified date and time.
        - start_time_to (str, optional): Upload assignments submitted before the specified date and time.
        - exclude_banned (bool, optional): Exclude answers from banned performers,
            even if assignments in suitable status "ACCEPTED".
        - field (List[GetAssignmentsTsvParameters.Field], optional): Select some additional fields.
            You can find possible values in the `toloka.client.assignment.GetAssignmentsTsvParameters.Field` enum.
        - toloka_client (TolokaClient): Client to be used to create obects in Toloka

    Returns:
        - DataFrame: `pd.DataFrame` with selected assignments.
            Note that nested paths are presented with a ":" sign.

    Example:
        >>> df = get_assignments_df(pool, status=['ACCEPTED'])
        ...
    """
    if pool:
        pool_id = extract_id(pool, Pool)
    if not pool_id:
        raise ValueError("Either pool or pool_id should be set")

    if not status:
        status = []
    elif isinstance(status, (str, Assignment.Status)):
        status = [status]
    kwargs = {'start_time_from': start_time_from,
              'start_time_to': start_time_to,
              'exclude_banned': exclude_banned,
              'field': field}
    return toloka_client.get_assignments_df(
        pool_id=pool_id,
        status=status,
        **{key: value for key, value in kwargs.items() if value is not None}
    )


@add_headers('dataiku')
def aggregate_dawid_skene(
    answers_df: pd.DataFrame,
    n_iter: int = 20
) -> pd.DataFrame:
    """
    Function to aggregate pool assignments in case of categorial responses using Dawid-Skene algorithm

    Args:
        - answers_df (DataFrame): DataFrame containing raw pool assignments.
        - n_iter (int): The number of EM iterations (algorithm parameter).

    Returns:
        - Series: `pd.Series` with aggregated responses to each task, task is a Series index.

    Example:
        >>> predicted_answers = aggregate_dawid_skene(answers_df, n_iter)
        ...
    """
    answers_df['task'] = answers_df.apply(
        get_task_from_fields, axis=1, field_type='INPUT:')
    answers_df['label'] = answers_df.apply(
        get_task_from_fields, axis=1, field_type='OUTPUT:')
    # Prepare dataframe
    answers_df = answers_df.rename(columns={
        'ASSIGNMENT:worker_id': 'worker'
    })
    answers_df = answers_df[['task', 'label', 'worker']]
    # Run aggregation
    predicted_answers = DawidSkene(n_iter=n_iter).fit_predict(answers_df)

    return predicted_answers
