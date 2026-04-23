import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    # GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    # GLM_TEXT_MODEL: str = "glm-4-flash"   # Text Model
    # GLM_VISION_MODEL: str = "glm-4v-plus"  # Visual Model
    GLM_API_KEY: str = os.getenv("ZAI_API_KEY", "")
    GLM_BASE_URL: str = os.getenv("ZAI_BASE_URL", "https://api.ilmu.ai/v1")
    GLM_TEXT_MODEL: str = os.getenv("ZAI_MODEL_NAME", "ilmu-glm-5.1")
    GLM_VISION_MODEL: str = os.getenv("ZAI_MODEL_NAME", "ilmu-glm-5.1")
    PRICE_SPIKE_THRESHOLD: float = 1.20

    # Simulation
    SIM_TICK_REAL_SEC: float = 1.0
    SIM_TICK_SIM_MIN: int = 30
    SIM_ORDER_PROCESS_CAPACITY: int = 3
    SIM_BASE_ORDERS_PER_TICK: int = 2
    
    # Crisis monitor
    CRISIS_COOLDOWN_SECONDS: int = 30
    OIL_PRICE_SPIKE_THRESHOLD: float = 1.15   # 15% spike
    
    # Tools defaults
    DEFAULT_BURN_RATE: float = 250.0
    DEFAULT_ELASTICITY: float = -1.2
    LOGISTICS_SURCHARGE_FACTOR: float = 0.5

settings = Settings()