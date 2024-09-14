import yaml

import audio_resource as assets


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def __init__(self):
        self._load_config()

    def _load_config(self):
        config_yaml = assets.config_file()
        with open(config_yaml, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        self.print_all()

    def get(self, key, default=None):
        return self.config.get(key, default)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def print_all(self):
        for key, value in self.config.items():
            print(f"{key}: {value}")

    def get_app_key(self):
        return self.config.get('app_key')

    def get_api_key(self):
        return self.config.get('api_key')

    def get_ak_id(self):
        return self.config.get('ak_id')

    def get_ak_secret(self):
        return self.config.get('ak_secret')

    def get_model(self):
        return self.config.get('model')

    def get_system_prompt(self):
        return self.config.get('system_prompt')

    def get_say_hello(self):
        return self.config.get('say_hello')

    def get_service_url(self):
        return self.config.get('service_url')


if __name__ == '__main__':
    config = Config.get_instance()
    print("所有配置项:")
    config.print_all()
