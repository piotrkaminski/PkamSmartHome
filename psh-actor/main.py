from configuration import ConfigurationService
from rooms_service import RoomsService
from hub_communication_service import HubCommunicationService
from signal import pause
import logging
import logging.config

class Main:

    def __init__(self):
        self.config_service = ConfigurationService()
        self.comm_service = HubCommunicationService()
        self.rooms_service = RoomsService()

    def main(self):
        try:
            logging.info("System initialization started")
            config = self.config_service.read_configuration()
            self.rooms_service.initialize(configuration=config, comm_service=self.comm_service)
            self.comm_service.initialize(configuration=config, rooms_service=self.rooms_service)
            self.rooms_service.reset()
            logging.info("System initialized")
            
            pause()
            
            logging.info("System shutdown started")
            self.comm_service.destroy()
            logging.info("System shutdown completed")
        except Exception as ex:
            logging.fatal("System execution failed due exception ", exc_info=True)
            raise ex

def main():
    logging.config.fileConfig("logging.conf")
    main = Main()
    main.main()

main()