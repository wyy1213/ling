"""RAG 本地知识库 - 使用本地 Embedding 模型"""
import os
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from typing import List, Dict, Optional
import hashlib

class MilitaryKnowledgeBase:
    """军事领域知识库 - 使用本地 Embedding"""
    
    def __init__(self, persist_dir: str = "./knowledge_base/chroma_db"):
        self.persist_dir = persist_dir
        self.collection_name = "military_docs"
        
        # 使用本地 HuggingFace embedding 模型
        print("🔄 正在加载本地 Embedding 模型...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ Embedding 模型加载完成")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        
        self._init_db()
    
    def _init_db(self):
        """初始化向量数据库"""
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(self.collection_name)
            print(f"✅ 加载已有知识库，包含 {self.collection.count()} 条记录")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ 创建新知识库")
        
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )
    
    def add_documents(self, file_paths: List[str]) -> Dict:
        """
        添加文档到知识库
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            {"added_chunks": int, "errors": List[str]}
        """
        added_chunks = 0
        errors = []
        
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    errors.append(f"文件不存在: {file_path}")
                    continue
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if not content.strip():
                    errors.append(f"文件为空: {file_path}")
                    continue
                
                # 文本分割
                chunks = self.text_splitter.split_text(content)
                
                if not chunks:
                    errors.append(f"无法分割文件: {file_path}")
                    continue
                
                # 生成元数据
                filename = os.path.basename(file_path)
                metadatas = [{
                    "source": filename,
                    "file_path": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "category": self._extract_category(content),
                    "doc_id": hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()[:8]
                } for i in range(len(chunks))]
                
                # 添加到向量库（批量添加）
                self.vectorstore.add_texts(
                    texts=chunks,
                    metadatas=metadatas,
                    ids=[f"{filename}_{i}" for i in range(len(chunks))]
                )
                
                added_chunks += len(chunks)
                print(f"   ✅ {filename}: {len(chunks)} 个片段")
                
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
                print(f"   ❌ {os.path.basename(file_path)}: {str(e)[:50]}")
        
        return {
            "added_chunks": added_chunks,
            "errors": errors
        }
    
    def _extract_category(self, content: str) -> str:
        """从内容中提取分类"""
        # 尝试从 【分类】标签提取
        if "【分类】" in content:
            try:
                start = content.find("【分类】") + 4
                end = content.find("\n", start)
                if end == -1:
                    end = len(content)
                category = content[start:end].strip()
                if category:
                    return category.split("/")[0]  # 取主分类
            except:
                pass
        
        # 根据关键词判断
        keywords = {
            "算法": "人工智能",
            "AI": "人工智能",
            "无人机": "无人系统",
            "蜂群": "无人系统",
            "太空": "航天",
            "卫星": "航天",
            "网络": "网络战",
            "网络战": "网络战",
            "认知": "认知战",
            "舆论": "认知战",
            "混合战争": "战略",
            "灰色地带": "战略"
        }
        
        content_lower = content[:1000]  # 只检查前1000字
        for keyword, category in keywords.items():
            if keyword in content_lower:
                return category
        
        return "综合"
    
    def add_text(self, text: str, metadata: Dict = None) -> str:
        """添加单段文本"""
        if not text.strip():
            return None
        
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return None
        
        doc_id = hashlib.md5(text[:100].encode()).hexdigest()[:8]
        
        metadatas = [{
            "source": metadata.get("source", "直接输入") if metadata else "直接输入",
            "category": metadata.get("category", "未分类") if metadata else "未分类",
            "chunk_index": i,
            "doc_id": doc_id
        } for i in range(len(chunks))]
        
        self.vectorstore.add_texts(
            texts=chunks,
            metadatas=metadatas,
            ids=[f"text_{doc_id}_{i}" for i in range(len(chunks))]
        )
        
        return doc_id
    
    async def query(self, query: str, perspective: str = None, top_k: int = 3) -> List[Dict]:
        """检索相关知识"""
        try:
            # 根据视角调整查询（如果有）
            search_query = query
            if perspective:
                perspective_keywords = {
                    "military": "军事战略作战",
                    "tech": "技术装备系统",
                    "intel": "情报分析侦察",
                    "cmd": "指挥控制战术",
                    "computer": "网络安全算法",
                    "hist": "历史经验案例"
                }
                if perspective in perspective_keywords:
                    search_query = f"{query} {perspective_keywords[perspective]}"
            
            results = self.vectorstore.similarity_search_with_score(
                query=search_query,
                k=top_k
            )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "本地知识库"),
                    "category": doc.metadata.get("category", "综合"),
                    "relevance_score": round(float(score), 3),
                    "doc_id": doc.metadata.get("doc_id", "")
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"RAG 查询错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def delete_document(self, source_name: str):
        """删除指定来源的所有片段"""
        try:
            # 使用 where 过滤删除
            self.collection.delete(
                where={"source": source_name}
            )
            print(f"🗑️ 已删除文档: {source_name}")
        except Exception as e:
            print(f"删除失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取知识库统计"""
        count = self.collection.count()
        return {
            "total_documents": count,
            "persist_dir": self.persist_dir
        }

# 全局实例
knowledge_base: Optional[MilitaryKnowledgeBase] = None

def init_knowledge_base(persist_dir: str = None):
    """初始化知识库"""
    global knowledge_base
    
    if persist_dir is None:
        # 自动查找 knowledge_base 目录
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_dir = os.path.dirname(backend_dir)
        persist_dir = os.path.join(project_dir, "knowledge_base", "chroma_db")
    
    knowledge_base = MilitaryKnowledgeBase(persist_dir)
    return knowledge_base

def get_knowledge_base() -> MilitaryKnowledgeBase:
    """获取知识库实例"""
    global knowledge_base
    if knowledge_base is None:
        return init_knowledge_base()
    return knowledge_base