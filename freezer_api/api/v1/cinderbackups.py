"""
(c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.

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

import falcon
from freezer_api.api.common import resource
from freezer_api.api.common import utils
from freezer_api.common import exceptions as freezer_api_exc


class CinderBackupsCollectionResource(resource.BaseResource):
    """
    Handler for endpoint: /v1/cinderbackups
    """
#    def __init__(self):
#        self.cinder = osclients.OpenstackOpts

    def on_get(self, req, resp):
        # GET /v1/cindernativebackups    Lists cinder backups
        search_opts = self.json_body(req)
        cinderclient = utils.get_cinderclient(req.headers)
        obj_list = cinderclient.backups.list(search_opts=search_opts)
        obj_dict = {}
        for index, backup in enumerate(obj_list):
            obj_dict[index] = [backup.id,
                               backup.volume_id,
                               backup.status,
                               backup.name,
                               backup.object_count,
                               backup.created_at,
                               backup.is_incremental]
        resp.body = obj_dict

    def on_post(self, req, resp):
        # POST /v1/cindernativebackups    Create cinder backups
        create_opts = self.json_body(req)
        if not create_opts:
            raise freezer_api_exc.BadDataFormat(
                message='Missing request body')
        cinderclient = utils.get_cinderclient(req.headers)
        backup = cinderclient.backups.create(create_opts.get('volume_id'),
                                             create_opts.get('container'),
                                             create_opts.get('name'),
                                             create_opts.get('description'),
                                             create_opts.get('incremental'),
                                             create_opts.get('force'),
                                             create_opts.get('snapshot_id')
                                             )
        resp.status = falcon.HTTP_201
        resp.body = backup._info


class CinderBackupsResource(resource.BaseResource):
    """
    Handler for endpoint: /v1/cinderbackups/{backup_id}
    """
    def on_delete(self, req, resp, backup_id):
        # DELETE /v1/cinderbackups/{backup_id}    Deletes the specified backup
        delete_opts = self.json_body(req)
        cinderclient = utils.get_cinderclient(req.headers)
        utils.find_resource(cinderclient.backups,
                            backup_id).delete(delete_opts.get('force', None))

        resp.body = {'backup_id': backup_id}
        resp.status = falcon.HTTP_201
