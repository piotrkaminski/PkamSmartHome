from configuration import ConfigurationService
from rooms_service import RoomsService
from hub_communication_service import HubCommunicationService
from signal import pause

class Main:

    def __init__(self):
        self.config_service = ConfigurationService()
        self.comm_service = HubCommunicationService()
        self.rooms_service = RoomsService()

    def main(self):
        config = self.config_service.read_configuration()
        self.rooms_service.initialize(configuration=config, comm_service=self.comm_service)
        self.comm_service.initialize(configuration=config, rooms_service=self.rooms_service)
        pause()

main = Main()
main.main()