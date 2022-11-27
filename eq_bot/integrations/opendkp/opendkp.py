from game.guild.entities.dkp_summary import DkpSummary

from integrations.opendkp.opendkp_api_gateway import OpenDkpApiGateway

class OpenDkp:
    def __init__(self):
        self._api_gateway = OpenDkpApiGateway()

    def create_raid(self, raid_name):
        return self._api_gateway.create_raid(raid_name)

    def get_dkp_summary(self) -> DkpSummary:
        return self._api_gateway.fetch_dkp_summary()
