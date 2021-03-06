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
from freezer_api.cmd.api import build_app
from freezer_api.common import config
from paste import deploy


def freezer_app_factory(global_conf, **local_conf):
    return build_app()


def initialize_app(conf=None, name='main'):
    try:
        config.parse_args()
        config.setup_logging()
    except Exception as e:
        pass
    conf = config.find_paste_config()
    app = deploy.loadapp('config:%s' % conf, name=name)
    return app

