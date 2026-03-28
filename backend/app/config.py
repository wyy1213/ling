"""配置管理"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = "sk-37907dc3166b4d1a98b5fe4458f336ac"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # 或 deepseek-reasoner
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # RAG 配置
    CHROMA_PERSIST_DIR: str = "./knowledge_base/chroma_db"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 3
    
    # 搜索配置
    SEARCH_MAX_RESULTS: int = 5
    
    # 专家配置
    EXPERTS_CONFIG: List[dict] = [
        {
            "id": "military_theory",
            "role": "军事理论研究专家",
            "perspective": "military",
            "avatar": "./军事理论研究专家.jpg",
            "color": "bg-morandi-red",
            "desc": "从军事理论角度研究算法战概念内涵、理论基础与作战体系"
        },
        {
            "id": "frontier_tech",
            "role": "前沿技术研究专家", 
            "perspective": "tech",
            "avatar": "./前沿技术研究专家.jpg",
            "color": "bg-morandi-blue",
            "desc": "探讨算法在无人系统、网络攻防、电磁频谱等领域的运用"
        },
        {
            "id": "intelligence",
            "role": "情报分析专家",
            "perspective": "intel", 
            "avatar": "./情报分析专家.jpg",
            "color": "bg-morandi-taupe",
            "desc": "研究算法战在情报搜集、动向分析、目标识别中的应用"
        },
        {
            "id": "command",
            "role": "战场指挥专家",
            "perspective": "cmd",
            "avatar": "./战场指挥专家.jpg",
            "color": "bg-morandi-green",
            "desc": "研究算法战在杀伤链闭环、OODA循环、辅助决策中的应用"
        },
        {
            "id": "cs",
            "role": "计算机科学家",
            "perspective": "computer",
            "avatar": "./计算机科学家.jpg",
            "color": "bg-morandi-clay",
            "desc": "关注算法设计、优化及其实现的技术细节与模型鲁棒性"
        },
        {
            "id": "history",
            "role": "历史学者",
            "perspective": "hist",
            "avatar": "./历史学者.jpg",
            "color": "bg-morandi-sage",
            "desc": "从历史角度审视算法与战争的关系演变，预测未来趋势"
        }
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()