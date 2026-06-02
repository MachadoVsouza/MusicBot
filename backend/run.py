import os
import logging
from dotenv import load_dotenv
from app import create_app

# Carrega variáveis do arquivo .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = create_app()

if __name__ == "__main__":
    app.run(
        host  = os.getenv("HOST",  "0.0.0.0"),
        port  = int(os.getenv("PORT", "5000")),
        debug = os.getenv("FLASK_ENV", "development") == "development",
    )