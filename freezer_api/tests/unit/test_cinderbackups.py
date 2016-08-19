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
from freezer_api.api.v1 import cinderbackups
from freezer_api.common.exceptions import BadDataFormat


class TestCinderBackupsCollectionResource(unittest.TestCase):

    def setUp(self):
        self.mock_req = Mock()
        self.mock_req.status = falcon.HTTP_200
        self.resource = cinderbackups.CinderBackupsCollectionResource()
        self.mock_json_body = Mock()
        self.mock_json_body.return_value = {}
        self.resource.json_body = self.mock_json_body

    @patch('freezer_api.api.v1.cinderbackups.utils')
    def test_on_get_return_empty_dict(self, mock_utils):
        fake_list = Mock()
        fake_list.return_value = []
        mock_backups= MagicMock(list=fake_list)
        mock_utils.get_cinderclient.return_value = MagicMock(backups=mock_backups)
        expected_result = {}
        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.body
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    @patch('freezer_api.api.v1.cinderbackups.utils')
    def test_on_get_return_correct_dict(self, mock_utils):
        fake_volume_0 = MagicMock(id='fake_id_0',
                                  volume_id='fake_volume_id_0',
                                  status='fake_status_0',
                                  name='fake_name_0',
                                  object_count='object_count_0',
                                  created_at='created_at_0',
                                  is_incremental='is_incremental_0')

        fake_volume_1 = MagicMock(id='fake_id_1',
                                  volume_id='fake_volume_id_1',
                                  status='fake_status_1',
                                  name='fake_name_1',
                                  object_count='object_count_1',
                                  created_at='created_at_1',
                                  is_incremental='is_incremental_1')

        fake_list = Mock()
        fake_list.return_value = [fake_volume_0, fake_volume_1]
        mock_backups= MagicMock(list=fake_list)
        mock_utils.get_cinderclient.return_value = MagicMock(backups=mock_backups)
        expected_result = {0: [fake_volume_0.id,
                               fake_volume_0.volume_id,
                               fake_volume_0.status,
                               fake_volume_0.name,
                               fake_volume_0.object_count,
                               fake_volume_0.created_at,
                               fake_volume_0.is_incremental],
                           1: [fake_volume_1.id,
                               fake_volume_1.volume_id,
                               fake_volume_1.status,
                               fake_volume_1.name,
                               fake_volume_1.object_count,
                               fake_volume_1.created_at,
                               fake_volume_1.is_incremental]}

        self.resource.on_get(self.mock_req, self.mock_req)
        result = self.mock_req.body
        self.assertDictEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_200)

    def test_on_post_raises_when_missing_create_opts(self):
        self.assertRaises(BadDataFormat, self.resource.on_post, self.mock_req, self.mock_req)

    @patch('freezer_api.api.v1.cinderbackups.utils')
    def test_on_post_create_correct_backup(self, mock_utils):
        fake_backup_0_create_opts = {'volume_id': 'fake_volume_id_0',
                                     'container': 'fake_container_0',
                                     'name': 'fake_name_0',
                                     'description': 'fake_description_0',
                                     'incremental': 'fake_incremental_0',
                                     'force': 'fake_force_0',
                                     'snapshot_id': 'fake_snapshot_id_0'}
        fake_backup_0 = MagicMock(_info='fake_backup_0_info')
        self.mock_json_body.return_value = fake_backup_0_create_opts
        fake_create_opts = Mock()
        fake_create_opts.return_value = fake_backup_0
        mock_backups = MagicMock(create=fake_create_opts)
        mock_utils.get_cinderclient.return_value = MagicMock(backups=mock_backups)
        self.resource.on_post(self.mock_req, self.mock_req)
        result = self.mock_req.body
        expected_result = 'fake_backup_0_info'
        self.assertEqual(result, expected_result)
        self.assertEqual(self.mock_req.status, falcon.HTTP_201)


class TestCinderBackupsResource(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.mock_req = Mock()
        self.mock_req.status = falcon.HTTP_200
        self.resource = cinderbackups.CinderBackupsResource()
        self.mock_json_body = Mock()
        self.mock_json_body.return_value = {}
        self.resource.json_body = self.mock_json_body

    @patch('freezer_api.api.v1.cinderbackups.utils')
    def test_on_delete_removes_proper_backup(self, mock_utils):
        fake_data_0_backup_id = 'fake_baackup_id'
        mock_utils.get_cinderclient.return_value = MagicMock(backups='fake_backups')
        mock_utils.find_resource.return_value = MagicMock()
        self.resource.on_delete(self.mock_req, self.mock_req, fake_data_0_backup_id)
        mock_utils.find_resource.assert_called_with('fake_backups', fake_data_0_backup_id)
        mock_utils.find_resource('fake_backups',
                                 fake_data_0_backup_id).delete.assert_called_with(None)
        result = self.mock_req.body
        expected_result = {'backup_id': fake_data_0_backup_id}
        self.assertEquals(self.mock_req.status, falcon.HTTP_201)
        self.assertEqual(result, expected_result)
