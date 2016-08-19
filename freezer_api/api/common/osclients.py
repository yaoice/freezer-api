# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
# (c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import swiftclient
import time

from cinderclient.client import Client as cinder_client
from glanceclient.client import Client as glance_client
from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient.client import Client as nova_client
from oslo_config import cfg
from oslo_log import log


CONF = cfg.CONF
logging = log.getLogger(__name__)


class OSClientManager(object):

    def __init__(self, auth_url, auth_method='password', **kwargs):
        self.swift = None
        self.glance = None
        self.nova = None
        self.cinder = None
        self.dry_run = kwargs.pop('dry_run', None)
        loader = loading.get_plugin_loader(auth_method)
        # copy the args for swift authentication !
        self.swift_args = kwargs.copy()
        self.swift_args['auth_url'] = auth_url
        # client specific arguments !
        self.client_kwargs = {}
        # session specific arguments
        session_kwargs = {}
        if 'verify' in kwargs.keys():
            session_kwargs['verify'] = kwargs.pop('verify')
        if 'cacert' in kwargs.keys():
            session_kwargs['cert'] = kwargs.pop('cacert')
        # client specific args
        if 'insecure' in kwargs.keys():
            self.client_kwargs['insecure'] = kwargs.pop('insecure')
            session_kwargs['verify'] = False
        if 'region_name' in kwargs.keys():
            self.client_kwargs['region_name'] = kwargs.pop('region_name')
        if 'endpoint_type' in kwargs.keys():
            self.client_kwargs['endpoint_type'] = kwargs.pop('endpoint_type')
        if 'identity_api_version' in kwargs.keys():
            kwargs.pop('identity_api_version')
        if 'auth_version' in kwargs.keys():
            kwargs.pop('auth_version')
        if 'interface' in kwargs.keys():
            self.client_kwargs['interface'] = kwargs.pop('interface')

        self.compute_version = kwargs.pop('compute_api_version', 2)
        self.image_version = kwargs.pop('image_api_version', 2)
        self.volume_version = kwargs.pop('volume_api_version', 2)
        self.auth = loader.load_from_options(auth_url=auth_url, **kwargs)

        self.sess = session.Session(auth=self.auth, **session_kwargs)

    def create_nova(self):
        """
        Use pre-initialized session to create an instance of nova client.
        :return: novaclient instance
        """
        self.nova = nova_client(self.compute_version, session=self.sess,
                                **self.client_kwargs)
        return self.nova

    def create_glance(self):
        """
        Use pre-initialized session to create an instance of glance client.
        :return: glanceclient instance
        """
        if 'endpoint_type' in self.client_kwargs.keys():
            self.client_kwargs.pop('endpoint_type')
        if 'insecure' in self.client_kwargs.keys():
            self.client_kwargs.pop('insecure')

        self.glance = glance_client(self.image_version, session=self.sess,
                                    **self.client_kwargs)
        return self.glance

    def create_cinder(self):
        """
        Use pre-initialized session to create an instance of cinder client.
        :return: cinderclient instance
        """
        self.cinder = cinder_client(self.volume_version, session=self.sess,
                                    **self.client_kwargs)
        return self.cinder

    def create_swift(self):
        """
        Swift client needs to be treated differently so we need to copy the
        arguments and provide it to swiftclient the correct way !
        :return: swiftclient instance
        """
        os_options = {}
        auth_version = None
        if 'region_name' in self.swift_args.keys():
            os_options['region_name'] = self.swift_args.get('region_name')
        if 'endpoint_type' in self.swift_args.keys():
            os_options['endpoint_type'] = self.swift_args.pop('endpoint_type')
        if 'tenant_id' in self.swift_args.keys():
            os_options['tenant_id'] = self.swift_args.pop('tenant_id')
        if 'identity_api_version' in self.swift_args.keys():
            os_options['identity_api_version'] = \
                self.swift_args.pop('identity_api_version')
            auth_version = os_options['identity_api_version']

        if 'token' in self.swift_args.keys():
            os_options['auth_token'] = self.swift_args.pop('token')
        if 'auth_version' in self.swift_args.keys():
            auth_version = self.swift_args.get('auth_version')

        tenant_name = self.swift_args.get('project_name') or self.swift_args.\
            get('tenant_name')
        self.swift = swiftclient.client.Connection(
            authurl=self.swift_args.get('auth_url'),
            user=self.swift_args.get('username'),
            key=self.swift_args.get('password'),
            tenant_name=tenant_name,
            insecure=self.swift_args.get('insecure', False),
            cacert=self.swift_args.get('cacert', None),
            os_options=os_options,
            auth_version=auth_version
        )

        if self.dry_run:
            self.swift = DryRunSwiftclientConnectionWrapper(self.swift)
        return self.swift

    def get_nova(self):
        """
        Get novaclient instance
        :return: novaclient instance
        """
        if not self.nova:
            self.nova = self.create_nova()
        return self.nova

    def get_glance(self):
        """
        Get glanceclient instance
        :return: glanceclient instance
        """
        if not self.glance:
            self.glance = self.create_glance()
        return self.glance

    def get_cinder(self):
        """
        Get cinderclient instance
        :return: cinderclient instance
        """
        if not self.cinder:
            self.cinder = self.create_cinder()
        return self.cinder

    def get_swift(self):
        """
        Get swiftclient instance
        :return: swiftclient instance
        """
        if not self.swift:
            self.swift = self.create_swift()
        return self.swift


class OpenstackOpts(object):
    """
    Gathering and maintaining the right Openstack credentials that will be used
    to authenticate against keystone. Now we support keystone v2 and v3.
    We need to provide a correct url that ends with either v2.0 or v3 or
    provide auth_version or identity_api_version
    """
    def __init__(self, auth_url, auth_method='password', auth_version=None,
                 username=None, password=None, region_name=None, cacert=None,
                 identity_api_version=None, project_id=None, project_name=None,
                 tenant_id=None, tenant_name=None, token=None, insecure=False,
                 endpoint_type='internalURL', interface=None,
                 compute_api_version=2, image_api_version=2,
                 volume_api_version=2, user_domain_name=None, domain_id=None,
                 user_domain_id=None, project_domain_id=None, domain_name=None,
                 project_domain_name=None):
        """
        Authentication Options to build a valid opts dict to be used to
        authenticate against keystone. You must provide auth_url with a vaild
        Openstack version at the end v2.0 or v3 or provide auth_version.
        :param auth_url: string Keystone API URL
        :param auth_method: string defaults to password or token (not tested)
        :param auth_version: string Keystone API version. 2.0 or 3
        :param username: string A valid Username
        :param password: string A valid Password
        :param region_name: string Region name or None
        :param cacert: string Path to CA certificate
        :param identity_api_version: string Keystone API version to use
        :param project_id: UUID string Project ID
        :param project_name: string Project Name
        :param tenant_id: string Project/ Tenant ID.
                          Use with keystone v2.0 only
        :param tenant_name: string Project/ Tenant Name. keystone v2.0 only
        :param token: string Valid token. Only if auth_method is token
        :param insecure: boolean Use insecure connections
        :param endpoint_type: string publicURL, adminURL, internalURL
        :param interface: string internal, ...
        :param compute_api_version: int NOVA API version to use default 2
        :param image_api_version: int Glance API version, default 2
        :param volume_api_version: int Cinder API version, default 2
        :param user_domain_name: string User Domain Name. only with keystone v3
        :param domain_id: string Domain ID. Only with keystone v3
        :param user_domain_id: string User Domain ID. only with keystone v3
        :param project_domain_id: string Project Domain ID. keystone v3 only
        :param domain_name: string Domain Name. only with keystone v3
        :param project_domain_name: string Project Domain Name.
                                    keystone v3 only
        :return: None
        """
        self.auth_url = auth_url
        self.auth_method = auth_method
        self.auth_version = auth_version
        self.username = username
        self.password = password
        self.region_name = region_name
        self.cacert = cacert
        self.identity_api_version = identity_api_version
        self.tenant_id = tenant_id or project_id
        self.project_id = project_id or tenant_id
        self.project_name = project_name or tenant_name
        self.tenant_name = tenant_name or project_name
        self.token = token
        self.insecure = insecure
        self.endpoint_type = endpoint_type
        self.interface = interface
        self.compute_api_version = compute_api_version
        self.image_api_version = image_api_version
        self.volume_api_version = volume_api_version
        self.user_domain_id = user_domain_id
        self.user_domain_name = user_domain_name
        self.project_domain_id = project_domain_id
        self.project_domain_name = project_domain_name
        self.domain_id = domain_id
        self.domain_name = domain_name
        if auth_url is None:
            raise Exception('auth_url required to authenticate. Make sure to '
                            'export OS_AUTH_URL=http://keystone_url:5000/v3')
        if auth_version is None and identity_api_version is None:
            version = auth_url.rstrip('/').rsplit('/')[-1]
            if version == 'v3':
                self.auth_version = self.identity_api_version = str('3')
            elif version == 'v2.0':
                self.auth_version = self.identity_api_version = str('2.0')
            else:
                raise Exception('Keystone Auth version {0} is not supported!. '
                                'Generated from auth_url: {1}'.format(version,
                                                                      auth_url)
                                )
        logging.info('Authenticating with Keystone version: {0},'
                     ' auth_url: {1},'
                     ' username: {2}, project: {3}'.format(self.auth_version,
                                                           self.auth_url,
                                                           self.username,
                                                           self.project_name))

    def get_opts_dicts(self):
        """
        Return opentack auth arguments as dict
        detects the auth version from url if not provided
        handles certificate issues
        """
        opts = self.__dict__
        if self.auth_method == 'password':
            opts.pop('token', None)
        elif self.auth_method == 'token':
            opts.pop('username', None)
            opts.pop('password', None)

        if not self.cacert:
            opts['verify'] = False
            opts['insecure'] = True
        self.auth_version = str(self.auth_version)
        self.identity_api_version = str(self.identity_api_version)

        if self.auth_version == '3' or self.identity_api_version == '3':
            opts['auth_version'] = opts['identity_api_version'] = '3'
            opts.pop('tenant_id', None)
            opts.pop('tenant_name', None)

        elif self.auth_version in ['2.0', '2'] or \
                self.identity_api_version in ['2.0', '2']:
            opts['auth_version'] = opts['identity_api_version'] = '2.0'
            # these parameters won't work with keystone v2.0
            opts.pop('project_id', None)
            opts.pop('project_name', None)
            opts.pop('project_domain_id', None)
            opts.pop('project_domain_name', None)
            opts.pop('user_domain_id', None)
            opts.pop('user_domain_name', None)
            opts.pop('domain_id', None)
            opts.pop('domain_name', None)
        else:
            raise Exception('Keystone Auth version {0} is not supported!. '
                            'Generated from auth_url: {1}'.
                            format(self.auth_version, self.auth_url))
        for i in opts.copy().keys():
            if opts.get(i) is None:
                opts.pop(i)
        return opts

    @staticmethod
    def create_from_env(context):
        """
        Parse environment variables and load Openstack related options.
        :return:
        """
        return OpenstackOpts.create_from_dict(context)

    @staticmethod
    def create_from_dict(src_dict):
        """
        Load Openstack arguments from dict and return OpenstackOpts object with
        the correct parameters to authenticate.
        :param src_dict: dict
        :return: OpenstackOpts object with the passed arguments in place
        """
        return OpenstackOpts(
            auth_url=src_dict.get('OS_AUTH_URL',
                                  CONF.keystone_authtoken.get('auth_uri')),
            auth_method='token',
            username=src_dict.get('X-USER-NAME', None),
            password=src_dict.get('X-USER-PASSWORD', ''),
            tenant_id=src_dict.get('X-TENANT-ID', None),
            tenant_name=src_dict.get('X-TENANT-NAME', None),
            project_id=src_dict.get('X-PROJECT-ID', None),
            project_name=src_dict.get('X-PROJECT-NAME', None),
            region_name=src_dict.get('X-REGION-NAME', None),
            endpoint_type=src_dict.get('X-ENDPOINT-TYPE', 'publicURL'),
            insecure=False,
            token=src_dict.get('X-AUTH-TOKEN', None),
            user_domain_name=src_dict.get('X-USER-DOMAIN-NAME', None),
            user_domain_id=src_dict.get('X-USER-DOMAIN-ID', 'Default'),
            project_domain_id=src_dict.get('X-PROJECT-DOMAIN-ID', None),
            project_domain_name=src_dict.get('X-PROJECT-DOMAIN-NAME', None),
            domain_id=src_dict.get('X-DOMAIN-ID', None),
            domain_name=src_dict.get('X-DOMAIN-NAME', None),
            compute_api_version=src_dict.get('OS_COMPUTE_API_VERSION', 2),
            volume_api_version=src_dict.get('OS_VOLUME_API_VERSION', 2),
            image_api_version=src_dict.get('OS_IMAGE_API_VERSION', 2)
                             )
