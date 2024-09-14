import sys
import os


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def say_hello_pcm_file():
    # 使用示例
    audio_file = resource_path('audio/say_hello.pcm')
    print(f"Audio file path: {audio_file}")
    return audio_file


def config_file():
    # 使用示例
    _config_file = resource_path('config.yaml')
    print(f"Config file path: {_config_file}")
    return _config_file
