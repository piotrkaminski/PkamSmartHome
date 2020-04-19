from configuration import ConfigurationService
from rooms_service import RoomsService
from hub_communication_service import HubCommunicationService
from signal import pause

class Main:

    def __init__(self):
        self.config_service = ConfigurationService()
        self.communication_service = HubCommunicationService()
        self.rooms_service = RoomsService()

    def main(self):
        configuration = self.config_service.read_configuration()
        self.rooms_service.initialize(configuration)
        self.communication_service.initialize(configuration, self.rooms_service)
        pause()

main = Main()
main.main()