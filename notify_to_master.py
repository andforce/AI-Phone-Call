import logger
import push_to_qiye_wx
from Config import Config


def notify(content):
    config = Config().get_instance()
    qiye_weixin = config.get('qiye_weixin')
    if qiye_weixin is None:
        logger.e("企业微信配置不存在, 不需要推送: {}".format(content))
        return
    secret = qiye_weixin['secret']
    qiye_id = qiye_weixin['qiye_id']
    agent_id = qiye_weixin['agent_id']
    if secret is None or qiye_id is None or agent_id is None:
        logger.e("企业微信配置不完整，不需要推送: {}".format(content))
        return
    push_to_qiye_wx.push_to_weixin(content)


if __name__ == '__main__':
    notify('测试')
