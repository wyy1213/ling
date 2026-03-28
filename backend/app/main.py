"""FastAPI 应用入口 - 集成前端版本"""
import sys
import os
import re

# ========== 修复 uvloop 冲突 ==========
if sys.platform != "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    except Exception:
        pass
os.environ["UVICORN_LOOP"] = "asyncio"

# ========== 路径处理 ===========
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
KNOWLEDGE_DIR = os.path.join(PROJECT_DIR, "knowledge_base", "docs")

print(f"🔍 FRONTEND_DIR = {FRONTEND_DIR}")
print(f"🔍 KNOWLEDGE_DIR = {KNOWLEDGE_DIR}")
print(f"🔍 exists = {os.path.exists(FRONTEND_DIR)}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from app.routers import symposium
from app.tools.rag import init_knowledge_base
from app.config import settings

app = FastAPI(
    title="灵境Symposium API",
    description="多专家 AI 研讨系统后端服务",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(symposium.router, prefix="/api")

# 静态文件
os.makedirs("static/avatars", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 关键：挂载 frontend 为静态文件服务（必须在根路由之前）
if os.path.exists(FRONTEND_DIR):
    print(f"✅ 挂载 frontend 到 /frontend")
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# 根路由返回修复后的 HTML
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "灵境Symposium.html")
    
    if not os.path.exists(index_path):
        return HTMLResponse(content=f"<h1>❌ 未找到: {index_path}</h1>")
    
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 修复 API 地址
    content = content.replace('const API_BASE = \'http://localhost:8000/api/symposium\'', 
                              'const API_BASE = \'/api/symposium\'')
    
    print("✅ HTML 路径修复完成")
    return HTMLResponse(content=content)

# 新增：总结生成接口（需要异步版本）
@symposium.router.post("/summary")
async def generate_summary_endpoint(request: dict):
    """生成AI总结"""
    from app.services.discussion import discussion_service
    session_id = request.get("session_id")
    if not session_id:
        return {"error": "缺少session_id"}
    
    result = await discussion_service.generate_summary(session_id)
    return {"summary": result}

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化知识库"""
    print("=" * 50)
    print("🚀 灵境Symposium 启动中...")
    
    # 初始化知识库并加载文档
    try:
        kb = init_knowledge_base()
        print("✅ 向量模型加载完成")
        
        # 自动扫描并加载文档
        if os.path.exists(KNOWLEDGE_DIR):
            files = []
            for f in os.listdir(KNOWLEDGE_DIR):
                if f.endswith(('.txt', '.pdf', '.md')):
                    files.append(os.path.join(KNOWLEDGE_DIR, f))
            
            if files:
                print(f"📚 发现 {len(files)} 个知识库文档:")
                for f in files:
                    print(f"   - {os.path.basename(f)}")
                
                # 同步加载（避免阻塞，使用线程池）
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        executor, 
                        lambda: kb.add_documents(files)
                    )
                
                print(f"✅ 知识库加载完成: {result.get('added_chunks', 0)} 个片段")
                if result.get('errors'):
                    print(f"⚠️ 错误: {len(result['errors'])} 个")
            else:
                print("⚠️ 知识库目录为空，请将文档放入:", KNOWLEDGE_DIR)
        else:
            print(f"⚠️ 知识库目录不存在: {KNOWLEDGE_DIR}")
            os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
            print(f"✅ 已自动创建目录，请放入文档后重启服务")
            
    except Exception as e:
        print(f"⚠️ 知识库初始化失败（不影响主功能）: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print(f"🌐 服务地址: http://{settings.HOST}:{settings.PORT}")
    print("=" * 50)
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        loop="asyncio"
    )
       