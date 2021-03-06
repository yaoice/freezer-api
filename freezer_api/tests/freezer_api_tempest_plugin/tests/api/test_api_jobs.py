# (C) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from freezer_api.tests.freezer_api_tempest_plugin.tests.api import base
from tempest import test

class TestFreezerApiJobs(base.BaseFreezerApiTest):

    @classmethod
    def resource_setup(cls):
        super(TestFreezerApiJobs, cls).resource_setup()

    @classmethod
    def resource_cleanup(cls):
        super(TestFreezerApiJobs, cls).resource_cleanup()

    @test.attr(type="gate")
    def test_api_jobs(self):

        resp, response_body = self.freezer_api_client.get_jobs()
        self.assertEqual(200, resp.status)

        response_body_json = json.loads(response_body)
        self.assertIn('jobs', response_body_json)
        jobs = response_body_json['jobs']
        self.assertEqual([], jobs)

    @test.attr(type="gate")
    def test_api_jobs_post(self):

        job = {
            "job_actions":
                [
                    {
                        "freezer_action":
                            {
                                "action": "backup",
                                "mode": "fs",
                                "src_file": "/home/tylerdurden/project_mayhem",
                                "backup_name": "project_mayhem_backup",
                                "container": "my_backup_container",
                            },
                        "exit_status": "success",
                        "max_retries": 1,
                        "max_retries_interval": 1,
                        "mandatory": True
                    }
                ],
            "job_schedule":
                {
                    "time_created": 1234,
                    "time_started": 1234,
                    "time_ended": 0,
                    "status": "stop",
                    "schedule_date": "2015-06-02T16:20:00",
                    "schedule_month": "1-6, 9-12",
                    "schedule_day": "mon, wed, fri",
                    "schedule_hour": "03",
                    "schedule_minute": "25",
                },
            "job_id": "blabla",
            "client_id": "blabla",
            "user_id": "blabla",
            "description": "scheduled one shot"
        }

        # Create the job with POST
        resp, response_body = self.freezer_api_client.post_jobs(job)
        self.assertEqual(201, resp.status)

        self.assertIn('job_id', response_body)
        job_id = response_body['job_id']

        # Check that the job has the correct values
        resp, response_body = self.freezer_api_client.get_jobs(job_id)
        self.assertEqual(200, resp.status)

       # Delete the job
        resp, response_body = self.freezer_api_client.delete_jobs(
            job_id)
        self.assertEqual(204, resp.status)
