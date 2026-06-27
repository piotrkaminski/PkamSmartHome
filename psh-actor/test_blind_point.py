from blind_point import BlindPoint
from point import Point
from unittest import TestCase
from unittest.mock import Mock, patch, call

class BlindPointTest(TestCase):

    def _createBlindPoint(self, position=0.0):
        comm_srv = Mock()
        relay_up = Mock()
        relay_down = Mock()
        point = BlindPoint(
            id="/RoomA/Blind1",
            controlPinUp=14,
            controlPinDown=15,
            buttonPinUp=23,
            buttonPinDown=24,
            fullTravelTimeSec=20.0,
            comm_service=comm_srv)
        point.relayUp = relay_up
        point.relayDown = relay_down
        point.position = position
        return point, comm_srv, relay_up, relay_down

    # --- moveUp tests ---

    def test_moveUp_activates_up_relay(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)

        point.moveUp()

        relay_up.on.assert_called_once()
        relay_down.on.assert_not_called()
        self.assertEqual("up", point._movementDirection)
        self.assertIsNotNone(point._movementStartTime)

    def test_moveUp_stops_down_relay_first(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point._movementDirection = "down"

        with patch('blind_point.sleep') as mock_sleep:
            point.moveUp()
            mock_sleep.assert_called_once_with(0.5)

        relay_up.off.assert_called()
        relay_down.off.assert_called()
        relay_up.on.assert_called_once()

    def test_moveUp_ignored_when_fully_open(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=0.0)

        point.moveUp()

        relay_up.on.assert_not_called()
        relay_down.on.assert_not_called()

    # --- moveDown tests ---

    def test_moveDown_activates_down_relay(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)

        point.moveDown()

        relay_down.on.assert_called_once()
        relay_up.on.assert_not_called()
        self.assertEqual("down", point._movementDirection)
        self.assertIsNotNone(point._movementStartTime)

    def test_moveDown_stops_up_relay_first(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point._movementDirection = "up"

        with patch('blind_point.sleep') as mock_sleep:
            point.moveDown()
            mock_sleep.assert_called_once_with(0.5)

        relay_up.off.assert_called()
        relay_down.off.assert_called()
        relay_down.on.assert_called_once()

    def test_moveDown_ignored_when_fully_closed(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=100.0)

        point.moveDown()

        relay_up.on.assert_not_called()
        relay_down.on.assert_not_called()

    # --- stop tests ---

    def test_stop_deactivates_both_relays(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point._movementDirection = "up"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1000.0):
            point.stop()

        relay_up.off.assert_called()
        relay_down.off.assert_called()
        self.assertIsNone(point._movementDirection)
        self.assertIsNone(point._movementStartTime)

    def test_stop_notifies_current_state(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)

        point.stop()

        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomA/Blind1", message="50")

    def test_stop_cancels_timer(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        mock_timer = Mock()
        point._movementTimer = mock_timer

        point.stop()

        mock_timer.cancel.assert_called_once()

    # --- position update tests ---

    def test_position_update_moving_down(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=0.0)
        point._movementDirection = "down"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1010.0):
            point._updatePosition()

        self.assertAlmostEqual(50.0, point.position, places=1)

    def test_position_update_moving_up(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=100.0)
        point._movementDirection = "up"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1010.0):
            point._updatePosition()

        self.assertAlmostEqual(50.0, point.position, places=1)

    def test_position_clamped_at_zero(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=10.0)
        point._movementDirection = "up"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1020.0):
            point._updatePosition()

        self.assertEqual(0.0, point.position)

    def test_position_clamped_at_hundred(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=90.0)
        point._movementDirection = "down"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1020.0):
            point._updatePosition()

        self.assertEqual(100.0, point.position)

    # --- moveToPosition tests ---

    def test_moveToPosition_down(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=0.0)

        with patch('blind_point.time', return_value=1000.0):
            with patch('threading.Timer') as mock_timer_class:
                mock_timer = Mock()
                mock_timer_class.return_value = mock_timer
                point.moveToPosition(50.0)

                mock_timer_class.assert_called_once_with(10.0, point._onTimerExpired, args=[50.0])
                mock_timer.start.assert_called_once()
        relay_down.on.assert_called_once()
        relay_up.on.assert_not_called()

    def test_moveToPosition_up(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=100.0)

        with patch('blind_point.time', return_value=1000.0):
            with patch('threading.Timer') as mock_timer_class:
                mock_timer = Mock()
                mock_timer_class.return_value = mock_timer
                point.moveToPosition(0.0)

                mock_timer_class.assert_called_once_with(20.0, point._onTimerExpired, args=[0.0])
                mock_timer.start.assert_called_once()
        relay_up.on.assert_called_once()
        relay_down.on.assert_not_called()

    def test_moveToPosition_already_at_target(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)

        point.moveToPosition(50.0)

        relay_up.on.assert_not_called()
        relay_down.on.assert_not_called()
        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomA/Blind1", message="50")

    def test_moveToPosition_two_thirds(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=0.0)

        with patch('blind_point.time', return_value=1000.0):
            with patch('threading.Timer') as mock_timer_class:
                mock_timer = Mock()
                mock_timer_class.return_value = mock_timer
                point.moveToPosition(67.0)

                expected_duration = 67.0 / 100.0 * 20.0
                mock_timer_class.assert_called_once_with(expected_duration, point._onTimerExpired, args=[67.0])

    # --- onTimerExpired tests ---

    def test_onTimerExpired_sets_position_and_notifies(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=0.0)
        point._movementDirection = "down"
        point._movementStartTime = 1000.0

        point._onTimerExpired(50.0)

        self.assertEqual(50.0, point.position)
        relay_up.off.assert_called()
        relay_down.off.assert_called()
        self.assertIsNone(point._movementDirection)
        self.assertIsNone(point._movementStartTime)
        self.assertIsNone(point._movementTimer)
        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomA/Blind1", message="50")

    # --- updateStatus tests ---

    def test_updateStatus_up(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point.moveUp = Mock()

        point.updateStatus("UP")

        point.moveUp.assert_called_once()

    def test_updateStatus_down(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point.moveDown = Mock()

        point.updateStatus("DOWN")

        point.moveDown.assert_called_once()

    def test_updateStatus_stop(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point.stop = Mock()

        point.updateStatus("STOP")

        point.stop.assert_called_once()

    def test_updateStatus_numeric_position(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=0.0)
        point.moveToPosition = Mock()

        point.updateStatus("50")

        point.moveToPosition.assert_called_once_with(50.0)

    def test_updateStatus_invalid_command(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point.moveUp = Mock()
        point.moveDown = Mock()
        point.stop = Mock()
        point.moveToPosition = Mock()

        point.updateStatus("INVALID")

        point.moveUp.assert_not_called()
        point.moveDown.assert_not_called()
        point.stop.assert_not_called()
        point.moveToPosition.assert_not_called()

    def test_updateStatus_out_of_range_position(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point.moveToPosition = Mock()

        point.updateStatus("150")

        point.moveToPosition.assert_not_called()

    # --- reset tests ---

    def test_reset_sets_position_to_zero(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=75.0)

        point.reset()

        self.assertEqual(0.0, point.position)
        relay_up.off.assert_called()
        relay_down.off.assert_called()
        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomA/Blind1", message="0")

    # --- notifyCurrentState tests ---

    def test_notifyCurrentState_reports_integer(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=66.7)

        point.notifyCurrentState()

        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomA/Blind1", message="67")

    # --- button tests ---

    def test_button_up_press_starts_moveUp(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)

        point._onButtonUpPressed()

        relay_up.on.assert_called_once()
        self.assertEqual("up", point._movementDirection)

    def test_button_up_release_stops(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point._movementDirection = "up"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1005.0):
            point._onButtonUpReleased()

        relay_up.off.assert_called()
        relay_down.off.assert_called()
        self.assertIsNone(point._movementDirection)

    def test_button_down_press_starts_moveDown(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)

        point._onButtonDownPressed()

        relay_down.on.assert_called_once()
        self.assertEqual("down", point._movementDirection)

    def test_button_down_release_stops(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point._movementDirection = "down"
        point._movementStartTime = 1000.0

        with patch('blind_point.time', return_value=1005.0):
            point._onButtonDownReleased()

        relay_up.off.assert_called()
        relay_down.off.assert_called()
        self.assertIsNone(point._movementDirection)

    def test_button_up_release_ignored_when_not_moving_up(self):
        point, comm_srv, relay_up, relay_down = self._createBlindPoint(position=50.0)
        point._movementDirection = "down"

        point._onButtonUpReleased()

        # Should not stop — blind is moving down, not up
        self.assertEqual("down", point._movementDirection)
