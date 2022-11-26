import requests
import boto3
import json

from requests_auth_aws_sigv4 import AWSSigV4
from botocore.config import Config

from datetime import datetime

from warrant.aws_srp import AWSSRP

from game.guild.dkp_entity_factory import build_summary_from_gateway
from game.guild.entities.dkp_summary import DkpSummary

from utils.http import HttpClient
from utils.config import get_config, get_secret

from integrations.aws_sigv4 import generate_headers

OPEN_DKP_ROOT_ENDPOINT = get_config('guild_tracking.open_dkp.root_endpoint')

OPEN_DKP_HOST = get_config('guild_tracking.open_dkp.host')
OPEN_DKP_SUBDOMAIN = '.'.join(OPEN_DKP_HOST.split('.')[0:-2])


class DkpGateway:
    def __init__(self):
        self._client = HttpClient()
        self._cognito_id_token = None
        self._cognito_refresh_token = None
        self._cognito_access_token = None

        self._client_id = None
        self._cognito_user_pool = None
        self._cognito_client_id = None
        self._cognito_pool_id = None
        self._get_site_details()

        self._aws_credentials = None
        self._aws_access_key_id = None
        self._aws_secret_key = None
        self._aws_session_token = None
        self._refresh_token()
        self._cognito_client = boto3.client(
            'cognito-identity',
            config=Config(region_name='us-east-2'))
        self._get_cognito_id()

    def fetch_dkp_summary(self) -> DkpSummary:
        response = self._client.get(
            f"{OPEN_DKP_ROOT_ENDPOINT.rstrip('/')}/dkp",
            headers={"clientid": self._client_id})
        print(response.json())
        return build_summary_from_gateway(response.json())

    def _get_site_details(self) -> None:
        response = self._client.get(
            f"https://4jmtrkwc86.execute-api.us-east-2.amazonaws.com/beta/client/{OPEN_DKP_SUBDOMAIN}"
        ).json()
        print(response)
        self._client_id = response["ClientId"]
        self._cognito_user_pool = response["UserPool"]
        self._cognito_client_id = response["WebClientId"]
        self._cognito_pool_id = response['Identity']
    
    def _get_credentials(self):
        response = self._cognito_client.get_credentials_for_identity(
            IdentityId=self._cognito_identity_id,
            Logins={
                f'cognito-idp.us-east-2.amazonaws.com/{self._cognito_user_pool}': self._cognito_id_token
            })
        self._aws_credentials = response['Credentials']
        print('CREDS',response)

    def _get_sigv4_headers(self):
        self._get_credentials()
        return AWSSigV4('execute-api',
            aws_access_key_id=self._aws_credentials["AccessKeyId"],
            aws_secret_access_key=self._aws_credentials["SecretKey"],
            aws_session_token=self._aws_credentials["SessionToken"],
            region="us-east-2"
        )
    
    def _get_cognito_id(self):
        response = self._cognito_client.get_id(
            IdentityPoolId=self._cognito_pool_id,
            Logins={
                f'cognito-idp.us-east-2.amazonaws.com/{self._cognito_user_pool}': self._cognito_id_token
            }
        )
        print('cognito id', response)
        self._cognito_identity_id = response["IdentityId"]

    def _refresh_token(self) -> None:
        aws = AWSSRP(
            username=get_secret('opendkp.admin.username'),
            password=get_secret('opendkp.admin.password'),
            pool_id=self._cognito_user_pool,
            client_id=self._cognito_client_id,
            pool_region='us-east-2')

        tokens = aws.authenticate_user()
        self._cognito_id_token = tokens['AuthenticationResult']['IdToken']
        self._cognito_refresh_token = tokens['AuthenticationResult']['RefreshToken']
        self._cognito_access_token = tokens['AuthenticationResult']['AccessToken']
        #token_type = tokens['AuthenticationResult']['TokenType']

    def _get_token(self):
        if not self._cognito_access_token:
            self._refresh_token()
        return self._cognito_access_token

    def create_raid(self, raid_name):
        self._get_credentials()
        print('creating raid', raid_name, self._get_token(), self._client_id)
        body = {
                "Attendance": 1,
                "Items": [],
                "Name": raid_name,
                "Pool": {
                    "Name": "DoN"
                },
                "Ticks": [],
                "Timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "UpdatedBy": get_secret('dkp.admin.username'),
                "UpdatedTimestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        open_dkp_headers = {
            "clientid": self._client_id,
            "cognitoinfo": self._cognito_id_token
        }
        headers = {
            **open_dkp_headers,
            **generate_headers(
                self._aws_credentials["AccessKeyId"],
                self._aws_credentials["SecretKey"],
                self._aws_credentials["SessionToken"],
                'POST',
                'us-east-2',
                'https://orgl2496uk.execute-api.us-east-2.amazonaws.com/beta/raids',
                json.dumps(body),
                headers=open_dkp_headers
            )
        }
        print('HEADERS', headers)
        result = requests.request('POST',
            f"https://orgl2496uk.execute-api.us-east-2.amazonaws.com/beta/raids",
            json=body,
            headers=headers)
        print('RESULT', result, result.json())
