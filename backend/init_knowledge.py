#!/usr/bin/env python3
"""初始化知识库，导入本地文档"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.rag import init_knowledge_base

# 路径配置（相对于 backend 目录）
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
DOCS_DIR = os.path.join(PROJECT_DIR, "knowledge_base", "docs")

def read_file_with_fallback(filepath):
    """尝试多种编码读取文件"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法解码文件: {filepath}")

async def main():
    print("🚀 开始初始化知识库...")
    print(f"📂 文档目录: {DOCS_DIR}")
    
    # 初始化知识库（自动加载模型）
    try:
        kb = init_knowledge_base()
        print(f"✅ 向量模型加载完成 (类型: {type(kb).__name__})")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not os.path.exists(DOCS_DIR):
        print(f"❌ 文档目录不存在: {DOCS_DIR}")
        print("请创建目录并放入 .txt 或 .pdf 文件:")
        print(f"  mkdir -p {DOCS_DIR}")
        return
    
    # 获取所有文档
    files = []
    for f in os.listdir(DOCS_DIR):
        if f.endswith(('.txt', '.pdf', '.md')):
            files.append(os.path.join(DOCS_DIR, f))
    
    if not files:
        print("⚠️ 没有找到文档文件 (.txt, .pdf, .md)")
        return
    
    print(f"📚 发现 {len(files)} 个文档:")
    for f in files:
        size = os.path.getsize(f) / 1024  # KB
        print(f"   - {os.path.basename(f)} ({size:.1f} KB)")
    
    # 检查可用的方法名
    if hasattr(kb, 'add_documents'):
        print("🔧 使用 add_documents 方法 (批量)")
        method = 'batch'
    elif hasattr(kb, 'add_document'):
        print("🔧 使用 add_document 方法 (逐个)")
        method = 'single'
    elif hasattr(kb, 'add_texts'):
        print("🔧 使用 add_texts 方法 (LangChain风格)")
        method = 'texts'
    else:
        print("❌ 错误: 知识库对象没有 add_documents/add_document/add_texts 方法")
        print(f"   可用方法: {[m for m in dir(kb) if not m.startswith('_')]}")
        return
    
    # 处理文档
    added_count = 0
    errors = []
    
    for filepath in files:
        try:
            content = read_file_with_fallback(filepath)
            filename = os.path.basename(filepath)
            
            if method == 'batch':
                # 批量方法，传入列表
                result = kb.add_documents([filepath])
                if isinstance(result, dict) and 'added_chunks' in result:
                    added_count += result['added_chunks']
                else:
                    added_count += 1
                    
            elif method == 'single':
                # 逐个添加
                kb.add_document(filepath, content, {
                    "source": filename,
                    "category": "military",
                    "date": os.path.getmtime(filepath)
                })
                added_count += 1
                
            elif method == 'texts':
                # LangChain风格
                from langchain.schema import Document
                doc = Document(
                    page_content=content,
                    metadata={"source": filename, "category": "military"}
                )
                kb.add_texts([doc.page_content], [doc.metadata])
                added_count += 1
                
            print(f"   ✅ {filename}")
            
        except Exception as e:
            errors.append(f"{filepath}: {str(e)}")
            print(f"   ❌ {os.path.basename(filepath)}: {str(e)[:50]}")
    
    print(f"\n✅ 处理完成:")
    print(f"   成功添加: {added_count}")
    print(f"   错误数: {len(errors)}")
    
    if errors:
        print("\n❌ 错误详情:")
        for err in errors[:5]:  # 只显示前5个
            print(f"   - {err}")
    
    # 测试查询
    print("\n🔍 测试查询 '算法战':")
    try:
        if hasattr(kb, 'query'):
            results = await kb.query("算法战", top_k=2)
        elif hasattr(kb, 'search'):
            results = kb.search("算法战", k=2)
        else:
            print("   ⚠️ 知识库没有 query/search 方法，跳过测试")
            results = []
            
        if results:
            for i, r in enumerate(results, 1):
                score = r.get('relevance_score', r.get('score', 0))
                content = r.get('content', str(r))[:150]
                print(f"\n{i}. 相似度: {score:.3f}")
                print(f"   {content}...")
        else:
            print("   未找到相关内容（知识库可能为空）")
    except Exception as e:
        print(f"   查询失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())