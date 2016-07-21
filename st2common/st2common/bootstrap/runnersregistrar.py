# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy

from st2common import log as logging
from st2common.exceptions.db import StackStormDBObjectNotFoundError
from st2common.models.api.action import RunnerTypeAPI
from st2common.persistence.runner import RunnerType
from st2common.util.action_db import get_runnertype_by_name

__all__ = [
    'register_runner_types',
]


LOG = logging.getLogger(__name__)



def register_runners(experimental=False):
    """
    :param experimental: True to also register experimental runners.
    :type experimental: ``bool``
    """
    LOG.debug('Start : register default RunnerTypes.')

    runner_types = []

    for runner_type in runner_types:
        runner_type = copy.deepcopy(runner_type)

        # For backward compatibility reasons, we also register runners under the old names
        runner_names = [runner_type['name']] + runner_type.get('aliases', [])
        for runner_name in runner_names:
            runner_type['name'] = runner_name
            runner_experimental = runner_type.get('experimental', False)

            if runner_experimental and not experimental:
                LOG.debug('Skipping experimental runner "%s"' % (runner_name))
                continue

            # Remove additional, non db-model attributes
            non_db_attributes = ['experimental', 'aliases']
            for attribute in non_db_attributes:
                if attribute in runner_type:
                    del runner_type[attribute]

            try:
                runner_type_db = get_runnertype_by_name(runner_name)
                update = True
            except StackStormDBObjectNotFoundError:
                runner_type_db = None
                update = False

            # Note: We don't want to overwrite "enabled" attribute which is already in the database
            # (aka we don't want to re-enable runner which has been disabled by the user)
            if runner_type_db and runner_type_db['enabled'] != runner_type['enabled']:
                runner_type['enabled'] = runner_type_db['enabled']

            runner_type_api = RunnerTypeAPI(**runner_type)
            runner_type_api.validate()
            runner_type_model = RunnerTypeAPI.to_model(runner_type_api)

            if runner_type_db:
                runner_type_model.id = runner_type_db.id

            try:
                runner_type_db = RunnerType.add_or_update(runner_type_model)

                extra = {'runner_type_db': runner_type_db}
                if update:
                    LOG.audit('RunnerType updated. RunnerType %s', runner_type_db, extra=extra)
                else:
                    LOG.audit('RunnerType created. RunnerType %s', runner_type_db, extra=extra)
            except Exception:
                LOG.exception('Unable to register runner type %s.', runner_type['name'])

    LOG.debug('End : register default RunnerTypes.')


def register_runner_types(experimental=False):
    pass
