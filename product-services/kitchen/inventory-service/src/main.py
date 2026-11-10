"""inventory-service - wiring comes from config/config.yaml; see grepx_service.serve."""
from grepx_service.serve import serve

if __name__ == "__main__":
    serve(__file__)
