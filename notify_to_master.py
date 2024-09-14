import push_to_qiye_wx


def notify(content):
    push_to_qiye_wx.push_to_weixin(content)


if __name__ == '__main__':
    notify('测试')
