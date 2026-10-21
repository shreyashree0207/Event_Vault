
from locust import HttpUser, task, between


class EventVaultUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def check_api(self):
        self.client.get("/openapi.json")
