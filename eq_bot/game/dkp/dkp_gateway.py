import requests
import json

from datetime import datetime

from game.guild.dkp_entity_factory import build_summary_from_gateway
from game.guild.entities.dkp_summary import DkpSummary
from game.dkp.entities.opendkp_identity import OpenDkpIdentity

from utils.http import HttpClient
from utils.config import get_config, get_secret

from integrations.aws.sigv4 import generate_sigv4_headers
from integrations.aws.cognito_session import CognitoSession

OPEN_DKP_ROOT_ENDPOINT = get_config('guild_tracking.open_dkp.root_endpoint')

OPEN_DKP_HOST = get_config('guild_tracking.open_dkp.host')
OPEN_DKP_SUBDOMAIN = '.'.join(OPEN_DKP_HOST.split('.')[0:-2])

OPEN_DKP_AWS_REGION = 'us-east-2'


class DkpGateway:
    def __init__(self):
        self._client = HttpClient()

        self._opendkp_identity = self._get_opendkp_identity()
        self._cognito_session = CognitoSession(
            user_pool = self._opendkp_identity.cognito_user_pool,
            client_id = self._opendkp_identity.cognito_client_id,
            pool_id = self._opendkp_identity.cognito_pool_id,
            region = OPEN_DKP_AWS_REGION
        )
        

    def _get_opendkp_identity(self) -> None:
        response = self._client.get(
            f"https://4jmtrkwc86.execute-api.us-east-2.amazonaws.com/beta/client/{OPEN_DKP_SUBDOMAIN}"
        ).json()
        return OpenDkpIdentity(
            client_id = response["ClientId"],
            cognito_user_pool = response["UserPool"],
            cognito_client_id = response["WebClientId"],
            cognito_pool_id = response['Identity']
        )

    def create_raid(self, raid_name):
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
            }
        print('BODY', body)
        open_dkp_headers = {
            "clientid": self._opendkp_identity.client_id,
            "cognitoinfo": self._cognito_session.tokens.id_token
        }
        headers = {
            **open_dkp_headers,
            **generate_sigv4_headers(
                self._cognito_session.iam_credentials,
                'PUT',
                'us-east-2',
                'https://orgl2496uk.execute-api.us-east-2.amazonaws.com/beta/raids',
                json.dumps(body),
                headers=open_dkp_headers
            )
        }
        print('HEADERS', headers)
        result = requests.request('PUT',
            f"https://orgl2496uk.execute-api.us-east-2.amazonaws.com/beta/raids",
            json=body,
            headers=headers)
        print('RESULT', result, result.json())

    def fetch_dkp_summary(self) -> DkpSummary:
        response = self._client.get(
            f"{OPEN_DKP_ROOT_ENDPOINT.rstrip('/')}/dkp",
            headers={
                "clientid": self._opendkp_identity.client_id
            })
        print(response.json())
        return build_summary_from_gateway(response.json())
