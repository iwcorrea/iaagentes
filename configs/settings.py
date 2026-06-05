from dotenv import load_dotenv
import os

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

MODEL_PRO = os.getenv("MODEL_PRO")

BASE_URL = os.getenv("DEEPSEEK_BASE_URL")