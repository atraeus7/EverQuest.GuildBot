from dataclasses import dataclass

@dataclass
class CognitoCredentials:
    id_token: str
    refresh_token: str
    access_token: str
