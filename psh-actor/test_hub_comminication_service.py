from hub_communication_service import HubCommunicationService
from unittest import TestCase

class HubCommunicationServiceTest(TestCase):

    def test_get_point_id_success(self):
        service = HubCommunicationService()
        self.assertEqual("/RoomX/PointDFS",service.get_point_id("/Ard/In/RoomX/PointDFS"))
        self.assertEqual("/Room1/Point1",service.get_point_id("/Pi/In/Room1/Point1"))
        self.assertEqual("/Room1/Point1/SubPoint",service.get_point_id("/Pi/In/Room1/Point1/SubPoint"))
        self.assertEqual(None,service.get_point_id("/Pi/Out/Room1/Point1"))