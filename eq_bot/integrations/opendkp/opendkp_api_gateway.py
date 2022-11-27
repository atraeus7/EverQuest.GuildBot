import requests
import json

from datetime import datetime

from game.guild.dkp_entity_factory import build_summary_from_gateway

from integrations.opendkp.entities.opendkp_identity_settings import OpenDkpIdentitySettings

from utils.http import HttpClient
from utils.config import get_config, get_secret

from integrations.aws.sigv4 import generate_sigv4_headers
from integrations.aws.cognito_session import CognitoSession

OPEN_DKP_ROOT_ENDPOINT = get_config('opendkp.root_endpoint')
OPEN_DKP_HOST = get_config('opendkp.host')
OPEN_DKP_SUBDOMAIN = '.'.join(OPEN_DKP_HOST.split('.')[0:-2])
OPEN_DKP_AWS_REGION = OPEN_DKP_ROOT_ENDPOINT.split('.')[2]


class OpenDkpApiGateway:
    def __init__(self):
        self._client = HttpClient()

        self._identity_settings = None
        self._cognito_session = None

    @property
    def cognito_session(self):
        if not self._cognito_session:
            self._cognito_session = CognitoSession(
                user_pool = self.identity_settings.cognito_user_pool,
                client_id = self.identity_settings.cognito_client_id,
                pool_id = self.identity_settings.cognito_pool_id,
                region = OPEN_DKP_AWS_REGION
            )
        return self._cognito_session

    @property
    def identity_settings(self):
        if not self._identity_settings:
            self._identity_settings = self._get_identity_settings()
        return self._identity_settings

    def _get_identity_settings(self) -> None:
        response = self._client.get(
            f"https://4jmtrkwc86.execute-api.us-east-2.amazonaws.com/beta/client/{OPEN_DKP_SUBDOMAIN}"
        ).json()
        return OpenDkpIdentitySettings(
            client_id = response["ClientId"],
            cognito_user_pool = response["UserPool"],
            cognito_client_id = response["WebClientId"],
            cognito_pool_id = response['Identity']
        )

    def _make_secure_request(self, method, endpoint, body, headers):
        # sign with sigv4 headers
        headers.update(
            generate_sigv4_headers(
                self.cognito_session.iam_credentials,
                OPEN_DKP_AWS_REGION,
                method,
                endpoint,
                headers,
                body=json.dumps(body),
                content_type='application/json',
                service='execute-api'))

        return self._client.request(
            method,
            endpoint,
            body,
            headers)

    def create_raid(self, raid_name):
        # TODO: Handle errors
        return self._make_secure_request(
            'PUT',
            'https://orgl2496uk.execute-api.us-east-2.amazonaws.com/beta/raids',
            body = {
                "Attendance": 1,
                "Items": [],
                "Name": raid_name,
                "Pool": {
                    "Name": "DoN",
                    "IdPool": 10
                },
                "Ticks": [],
                "Timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "UpdatedBy": get_secret('dkp.admin.username'),
                "UpdatedTimestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            },
            headers = {
                "clientid": self.identity_settings.client_id,
                "cognitoinfo": self.cognito_session.tokens.id_token
            }
        ).json()

    def fetch_dkp_summary(self) -> dict:
        response = self._client.get(
            f"{OPEN_DKP_ROOT_ENDPOINT.rstrip('/')}/dkp",
            headers={ "clientid": self.identity_settings.client_id })
        
        # TODO: Handle errors
        return build_summary_from_gateway(response.json())
