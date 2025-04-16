import pytest
from unittest.mock import MagicMock
import numpy as np
from modules.MissileLauncher import MissileLauncher
from modules.Missile import Missile
from modules.utils import Target, TargetType
from modules.Messages import LaunchMissileMessage, LaunchedMissileMessage
from modules.constants import CCP_ID
from modules.AirObject import Trajectory

class TestMissileLauncher:

    @pytest.fixture
    def missile_launcher(self):
        manager_mock = MagicMock()
        pos = np.array([0, 0, 0])
        return MissileLauncher(manager_mock, 1, pos, max_missiles=5)

    @pytest.fixture
    def missile(self):
        return Missile(MagicMock(), 1, np.array([0, 0, 0]))

    @pytest.fixture
    def target(self):
        trajectory = Trajectory()
        return Target(2, TargetType.AIR_PLANE, np.array([1000, 1000, 1000]), trajectory)

    def test_launch_missile_no_missiles(self, missile_launcher, target):
        result = missile_launcher.launch_missile(target)
        assert result is None
        # missile_launcher._manager.add_message.assert_not_called()

    def test_launch_missile_success(self, missile_launcher, missile, target):
        missile_launcher.missiles.append(missile)
        result = missile_launcher.launch_missile(target)
        assert result == missile
        # missile.set.assert_called_once_with(target)
        # missile_launcher._manager.add_message.assert_any_call(LaunchMissileMessage(receiver_id=missile.id, sender_id=missile_launcher.id))
        # missile_launcher._manager.add_message.assert_any_call(LaunchedMissileMessage(sender_id=missile_launcher.id, receiver_ID=CCP_ID, missile_id=missile.id, target_id=None))

    def test_launch_missile_failure(self, missile_launcher, target):
        # missile_launcher.missiles.append(missile)
        # missile_launcher._manager.add_message.side_effect = Exception("Launch failed")
        result = missile_launcher.launch_missile(target)
        assert result is None
        # missile_launcher._manager.add_message.assert_any_call(LaunchMissileMessage(receiver_id=missile.id, sender_id=missile_launcher.id))
        # missile_launcher._manager.add_message.assert_any_call(LaunchedMissileMessage(sender_id=missile_launcher.id, receiver_ID=CCP_ID, missile_id=missile.id, target_id=None))
