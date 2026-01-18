import os
import json
import time
import threading
import requests
from dotenv import load_dotenv
from config.log import logger

load_dotenv()

APOLLO_URL = os.getenv("APOLLO_URL", "http://localhost:8080")
APP_ID = os.getenv("APP_ID", "python-demo")
CLUSTER = os.getenv("CLUSTER", "default")
NAMESPACE = os.getenv("NAMESPACE", "application")


class ApolloConfig:
    def __init__(self):
        self._config = {}
        self._notification_id = -1
        self._lock = threading.Lock()
        self._start_watcher()

    @property
    def config(self):
        """安全获取当前配置"""
        with self._lock:
            return self._config.copy()

    def fetch_config(self):
        """从 Apollo 拉取最新配置"""
        url = f"{APOLLO_URL}/configs/{APP_ID}/{CLUSTER}/{NAMESPACE}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            cfg = resp.json().get("configurations", {})
            with self._lock:
                self._config = cfg
            logger.info(f"[CONFIG LOADED] {cfg}")
            return cfg
        except Exception as e:
            logger.error(f"[FETCH ERROR] {e}")
            return {}

    def _watch_loop(self):
        """长轮询监听配置变化"""
        while True:
            try:
                notifications = json.dumps([{"namespaceName": NAMESPACE, "notificationId": self._notification_id}])
                url = f"{APOLLO_URL}/notifications/v2"
                params = {"appId": APP_ID, "cluster": CLUSTER, "notifications": notifications}
                r = requests.get(url, params=params, timeout=60)
                if r.status_code == 200 and r.json():
                    for n in r.json():
                        if n["namespaceName"] == NAMESPACE:
                            logger.info("[CONFIG CHANGE DETECTED]")
                            self.fetch_config()
                            self._notification_id = n["notificationId"]
            except Exception as e:
                logger.warning(f"[WATCH ERROR] {e}")
            time.sleep(1)

    def _start_watcher(self):
        """启动后台线程"""
        self.fetch_config()
        t = threading.Thread(target=self._watch_loop, daemon=True)
        t.start()


# 单例模式，其他模块直接 import config
apollo = ApolloConfig()