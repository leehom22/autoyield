import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    GLM_TEXT_MODEL: str = "glm-4-flash"   # Text Model
    GLM_VISION_MODEL: str = "glm-4v-plus"  # Visual Model

settings = Settings()