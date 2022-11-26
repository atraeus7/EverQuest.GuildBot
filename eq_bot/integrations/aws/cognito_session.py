import boto3

from botocore.config import Config

from warrant.aws_srp import AWSSRP

from utils.config import get_secret
from integrations.aws.entities.iam_credentials import IamCredentials
from integrations.aws.entities.cognito_credentials import CognitoCredentials

OPENDKP_ADMIN_USERNAME = get_secret('opendkp.admin.username')
OPENDKP_ADMIN_PASSWORD = get_secret('opendkp.admin.password')


class CognitoSession:
    def __init__(self, user_pool: str, client_id: str, pool_id: str, region):
        self._user_pool = user_pool
        self._client_id = client_id
        self._pool_id = pool_id
        self._region = region
        self._tokens = None
        self._identity_id = None
        self._iam_credentials = None

        self._client = boto3.client(
            'cognito-identity',
            config=Config(region_name=self._region))

    def _get_identity_id(self):
        response = self._client.get_id(
            IdentityPoolId=self._pool_id,
            Logins={
                f'cognito-idp.{self._region}.amazonaws.com/{self._user_pool}':
                    self._tokens.id_token
            }
        )
        return response["IdentityId"]
    
    def _get_iam_credentials(self):
        response = self._client.get_credentials_for_identity(
            IdentityId=self.identity_id,
            Logins={
                f'cognito-idp.{self._region}.amazonaws.com/{self._user_pool}':
                    self._tokens.id_token
            })
        print('RESPONSE', response)
        return IamCredentials(
            expires_at = response['Credentials']['Expiration'],
            access_key_id = response['Credentials']['AccessKeyId'],
            secret_key = response['Credentials']['SecretKey'],
            session_token = response['Credentials']['SessionToken'])
    
    def _refresh_tokens(self) -> None:
        tokens = AWSSRP(
            username=OPENDKP_ADMIN_USERNAME,
            password=OPENDKP_ADMIN_PASSWORD,
            pool_id=self._user_pool,
            client_id=self._client_id,
            pool_region=self._region).authenticate_user()
        return CognitoCredentials(
            id_token=tokens['AuthenticationResult']['IdToken'],
            refresh_token=tokens['AuthenticationResult']['RefreshToken'],
            access_token=tokens['AuthenticationResult']['AccessToken'])
    
    @property
    def tokens(self):
        # TODO: Check if cognito credentials are expired
        # and refresh if so
        if not self._tokens:
            self._tokens = self._refresh_tokens()
        return self._tokens

    @property
    def identity_id(self):
        if not self._identity_id:
            self._identity_id = self._get_identity_id()
        return self._identity_id

    @property
    def iam_credentials(self):
        if not self._iam_credentials or datetime.now() >= self._iam_credentials.expires_at:
            self._iam_credentials = self._get_iam_credentials()
        return self._iam_credentials
