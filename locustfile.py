from locust import HttpUser, task, between

class PaperlyUser(HttpUser):
    wait_time = between(1, 3)  # tiempo entre requests (simulación realista)

    def on_start(self):
        """Se ejecuta al iniciar cada usuario simulado"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "student@utec.edu.pe",
                "password": "password123"
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(2)  # más frecuente
    def search_papers(self):
        """Simular búsqueda de papers"""
        self.client.get(
            "/api/v1/search?q=machine%20learning",
            headers=self.headers
        )

    @task(1)  # menos frecuente
    def get_library(self):
        """Simular consulta de la librería personal"""
        self.client.get(
            "/api/v1/library",
            headers=self.headers
        )
