from nonebot.adapters.onebot.v11 import Message

from .fake import fake_group_message_event_v11


def test_fake_group_message_event_v11():
    event = fake_group_message_event_v11(message=Message("测试消息"))

    assert event.message_type == "group"
    assert event.user_id == 12345678
    assert str(event.message) == "测试消息"
