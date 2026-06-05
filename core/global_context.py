# core/global_context.py

class GlobalContext:
    def __init__(self):
        self.entities = {}
        self.api_routes = []
        self.models = []
        self.services = []

    def register_model(self, name, schema):
        if name not in self.models:
            self.models.append(name)
        self.entities[name] = schema

    def register_route(self, route):
        if route not in self.api_routes:
            self.api_routes.append(route)

    def register_service(self, service_name):
        if service_name not in self.services:
            self.services.append(service_name)

    def summary(self):
        return {
            "models": self.models,
            "routes": self.api_routes,
            "entities": list(self.entities.keys()),
            "services": self.services
        }