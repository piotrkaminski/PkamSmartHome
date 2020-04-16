from configuration import ConfigurationService
from main_service import MainService
from hub_communication_service import HubCommunicationService

class Main:

    def __init__(self):
        self.configService = ConfigurationService()
        self.communicationService = HubCommunicationService()
        self.mainService = MainService()

    def main(self):
        configuration = self.configService.read_configuration()
        self.communicationService.initialize(configuration.get(CONFIG_CONNECTIVITY))
        self.mainService.initialize(configuration)
        
        self.mainService.execute()
        self.mainService.destroy()

main = Main()
main.main()