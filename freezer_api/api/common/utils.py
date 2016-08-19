"""
(c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from cinderclient import exceptions
from freezer_api.api.common import osclients
from freezer_api.context import FreezerContext
from oslo_log import log
from oslo_utils import encodeutils
import sys
import uuid

LOG = log.getLogger(__name__)


def inject_context(req, resp, params):
    user_id = req.headers.get('X-USER-ID')
    request_id = req.headers.get('X-Openstack-Request-ID'),
    auth_token = req.headers.get('X-AUTH-TOKEN')

    tenant = req.headers.get('X-TENANT-ID')

    roles = req.headers.get('X-ROLES')
    roles = roles and roles.split(',') or []
    ctxt = FreezerContext(auth_token=auth_token,
                          user=user_id,
                          tenant=tenant,
                          request_id=request_id,
                          roles=roles)

    req.env['freezer.context'] = ctxt
    LOG.info('Request context set')


def before_hooks():
    return [inject_context]


class FuncMiddleware(object):
    """
    Injecting some function as middleware for freezer-api
    """
    def __init__(self, func):
        self.func = func

    def process_resource(self, req, resp, resource, params=None):
        return self.func(req, resp, params)


def get_cinderclient(env):
    osopts = osclients.OpenstackOpts
    options = osopts.create_from_env(env).get_opts_dicts()
    client_manager = osclients.OSClientManager(
        auth_url=options.pop('auth_url', None),
        auth_method=options.pop('auth_method', 'password'),
        **options
        )
    cinderclient = client_manager.get_cinder()
    return cinderclient


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exceptions.NotFound:
        pass
    else:
        # now try to get entity as uuid
        try:
            uuid.UUID(name_or_id)
            return manager.get(name_or_id)
        except (ValueError, exceptions.NotFound):
            pass

    if sys.version_info <= (3, 0):
        name_or_id = encodeutils.safe_decode(name_or_id)

    try:
        try:
            resource = getattr(manager, 'resource_class', None)
            name_attr = resource.NAME_ATTR if resource else 'name'
            return manager.find(**{name_attr: name_or_id})
        except exceptions.NotFound:
            pass

        # finally try to find entity by human_id
        try:
            return manager.find(human_id=name_or_id)
        except exceptions.NotFound:
            msg = "No %s with a name or ID of '%s' exists." % \
                (manager.resource_class.__name__.lower(), name_or_id)
            raise exceptions.CommandError(msg)

    except exceptions.NoUniqueMatch:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exceptions.CommandError(msg)
