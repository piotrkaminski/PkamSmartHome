from hub_communication_service import HubCommunicationService
from unittest import TestCase
from unittest.mock import Mock

class HubCommunicationServiceTest(TestCase):

    def test_get_point_id_success(self):
        service = HubCommunicationService()
        self.assertEqual("/RoomX/PointDFS",service.get_point_id("/Ard/In/RoomX/PointDFS"))
        self.assertEqual("/Room1/Point1",service.get_point_id("/Pi/In/Room1/Point1"))
        self.assertEqual("/Room1/Point1/SubPoint",service.get_point_id("/Pi/In/Room1/Point1/SubPoint"))
        self.assertEqual(None,service.get_point_id("/Pi/Out/Room1/Point1"))
        self.assertEqual(None,service.get_point_id(""))

    def test_get_point_id_none(self):
        service = HubCommunicationService()
        self.assertEqual(None, service.get_point_id(None))
    
    def test_is_admin_channel_ok(self):
    	  service = HubCommunicationService()
    	  result = service.is_admin_channel("/ClientY/Admin")
    	  self.assertEqual(True, result)
    	  
    def test_is_admin_channel_not_ok(self):
        service = HubCommunicationService()
        result = service.is_admin_channel("/ClinetYY/ADM")
        self.assertEqual(False, result)

    def test_create_topic_name_sucess(self):
        service = HubCommunicationService()
        service.client_name = "ClientY"
        self.assertEqual("/ClientY/In/#", service.create_topic_name())

    def test_get_channel(self):
        service = HubCommunicationService()
        service.client_name = "ClientY"
        self.assertEqual("/ClientY/Out/Room3/Point4", service.get_channel("/Room3/Point4"))

    def test_sendStatusUpdate_sucess(self):
        service = HubCommunicationService()
        mqtt_client = Mock()
        service.client_name = "ClientE"
        service.client = mqtt_client
        service.sendStatusUpdate("/Room3/Point4", "message")
        mqtt_client.publish.assert_called_with(topic="/ClientE/Out/Room3/Point4",payload="message")

    def test_process_message__ctrl_success(self):
        service = HubCommunicationService()
        rooms_service = Mock()
        service.rooms_service = rooms_service

        service.process_message(channel="/ClientA/In/Room3/Point3", message="message")
        rooms_service.updateStatus.assert_called_with(point_id="/Room3/Point3",message="message")
        rooms_service.reset.assert_not_called()

    def test_process_message_none_point(self):
        service = HubCommunicationService()
        rooms_service = Mock()
        service.rooms_service = rooms_service

        service.process_message("/ClientA/In", "message")
        rooms_service.updateStatus.assert_not_called()

    def test_process_message_admin_sucess(self):
        service = HubCommunicationService()
        rooms_service = Mock()
        service.rooms_service = rooms_service

        service.process_message(channel="/ClientA/Admin", message="RESET")
        rooms_service.updateStatus.assert_not_called()
        rooms_service.reset.assert_called()

    def test_on_message(self):
        service = HubCommunicationService()
        message = Mock()
        message.topic = "/some/topic"
        decode_func = Mock(return_value = "some payload")
        message.payload.decode = decode_func
        service.process_message = Mock()
        service.on_message(None, None, message)
        service.process_message.assert_called_with(channel="/some/topic", message="some payload")
    
    def test_on_connect(self):
        service = HubCommunicationService()
        service.client_name = "ClientE"
        mqtt_client = Mock()
        service.client = mqtt_client

        service.on_connect(client=Mock(), userdata=None, flags=None, rc=None)
        mqtt_client.subscribe.assert_called_with("/ClientE/In/#")
