from configuration import ConfigurationService
from main_service import MainService

class Main:

    def __init__(self):
        self.configService = ConfigurationService()
        self.mainService = MainService()

    def main(self):
        configuration = self.configService.read_configuration()
        self.mainService.initialize(configuration)

        self.mainService.execute()


main = Main()
main.main()