import pytest
from unittest.mock import MagicMock
import numpy as np
from ..modules.MissileLauncher import MissileLauncher
from ..modules.Missile import Missile
from ..modules.utils import Target, TargetType
from ..modules.constants import CCP_ID
from ..modules.AirObject import Trajectory
from ..modules.Manager import Manager
from ..modules.Messages import CPPLaunchMissileRequestMessage, MissileCountRequestMessage, MissileCountResponseMessage
import numpy as np

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

class TestMissileLauncherStep:
    def setup_method(self):
        self.manager = MagicMock(spec=Manager)
        # Добавляем моки для всех необходимых атрибутов Manager
        self.manager.time = MagicMock()
        self.manager.time.get_time.return_value = 0.0
        self.manager.give_messages_by_id.return_value = []
        self.manager.add_message = MagicMock()  # Явно мокируем add_message
        
        self.position = np.array([0, 0, 0])
        self.missile_launcher = MissileLauncher(manager=self.manager, id=1, pos=self.position)

    def test_step_no_messages(self):
        self.missile_launcher.step()
        self.manager.give_messages_by_id.assert_called_once_with(1)
        self.manager.add_message.assert_not_called()

    def test_step_cpp_launch_missile_request_message(self):
        manager = MagicMock(spec=Manager)
        manager.time = MagicMock()
        manager.time.get_time.return_value = 0.0
        
        trajectory = MagicMock(spec=Trajectory)
        target = Target(manager=manager, 
                    id=1,
                    pos=np.array([1, 1, 1]),
                    trajectory=trajectory,
                    type=TargetType.AIR_PLANE)
        
        message = CPPLaunchMissileRequestMessage(sender_id=2, 
                                            receiver_id=1, 
                                            target=target, 
                                            target_id=1, 
                                            radar_id=1)
        self.manager.give_messages_by_id.return_value = [message]
        
        # Мокируем метод launch_missile с использованием autospec
        self.missile_launcher.launch_missile = MagicMock()
        
        self.missile_launcher.step()
        
        # Проверяем вызов с правильными именованными аргументами
        self.missile_launcher.launch_missile.assert_called_once_with(
            target_pos=target,
            target_id=1,
            radar_id=1
        )


    def test_step_missile_count_request_message(self):
        self.manager.time.get_time.return_value = 123.45
        message = MissileCountRequestMessage(sender_id=2, receiver_id=1)
        self.manager.give_messages_by_id.return_value = [message]
        
        self.missile_launcher.step()
        
        # Проверяем что был вызов add_message с правильными параметрами
        args, kwargs = self.manager.add_message.call_args
        response_msg = args[0]
        assert isinstance(response_msg, MissileCountResponseMessage)
        assert response_msg.sender_id == 1
        assert response_msg.receiver_id == 2
        assert response_msg.count == 0

