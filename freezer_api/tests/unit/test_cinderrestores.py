"""
(c) Copyright 2015,2016 99cloud Company.

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

import unittest
import falcon
from mock import Mock, MagicMock, patch
from freezer_api.api.v1 import cinderrestores
from freezer_api.common.exceptions import BadDataFormat


class TestCinderRestoresResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.status = falcon.HTTP_200
        self.resource = cinderrestores.CinderRestoresResource()
        self.mock_json_body = Mock()
        self.mock_json_body.return_value = {}
        self.resource.json_body = self.mock_json_body

    def test_on_post_raises_when_missing_backup_id(self):
        self.assertRaises(BadDataFormat,
                          self.resource.on_post,
                          self.mock_req,
                          self.mock_req,
                          None)

    @patch('freezer_api.api.v1.cinderrestores.utils')
    def test_on_post_create_correct_backup(self, mock_utils):
        fake_data_0_backup_id = 'fake_baackup_id'
        fake_restore_0 = MagicMock(_info='fake_restore_0_info')
        fake_restore_opts = Mock()
        fake_restore_opts.return_value = fake_restore_0
        mock_restores = MagicMock(restore=fake_restore_opts)
        mock_utils.get_cinderclient.return_value = MagicMock(restores=mock_restores)
        self.resource.on_post(self.mock_req, self.mock_req, fake_data_0_backup_id)
        result = self.mock_req.body
        expected_result = 'fake_restore_0_info'
        self.assertEqual(self.mock_req.body, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)
