import json
import threading

import requests

import logger
from Config import Config


def push_to(_qiye_id, _agent_id, _secret, _msg):
    """
    https://blog.csdn.net/haijiege/article/details/86529460
    https://daliuzi.cn/tasker-forward-sms-wechat/

    :param _qiye_id:
    :param _agent_id:
    :param _secret:
    :param _msg:
    """
    gettoken = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + _qiye_id + "&corpsecret=" + _secret

    response = requests.get(gettoken)
    get_result = json.loads(response.text)
    _access_token = str(get_result['access_token'])

    _msg_builder = {
        "touser": "@all",
        "msgtype": "text",
        "agentid": _agent_id,
        "text": {
            "content": _msg
        },
        "safe": 0
    }

    msg_json = json.dumps(_msg_builder)
    send = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + _access_token

    post_result = requests.post(url=send, data=str(msg_json))
    # print(post_result.text)
    logger.i(f"推送结果: {post_result.text}")


def _threaded_push_to_weixin(sms):
    config = Config().get_instance()
    qiye_weixin = config.get('qiye_weixin')
    if qiye_weixin is None:
        logger.e("企业微信配置不存在")
        return
    secret = qiye_weixin['secret']
    qiye_id = qiye_weixin['qiye_id']
    agent_id = qiye_weixin['agent_id']
    if secret is None or qiye_id is None or agent_id is None:
        logger.e("企业微信配置不完整")
        return
    push_to(qiye_id, agent_id, secret, sms)


def push_to_weixin(sms):
    thread = threading.Thread(target=_threaded_push_to_weixin, args=(sms,))
    thread.start()


if __name__ == '__main__':
    push_to_weixin('测试')
