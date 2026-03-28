"""联网搜索工具 - 解决 AI 胡说八道问题"""
import aiohttp
import asyncio
from typing import List, Dict
from duckduckgo_search import DDGS
import json
from datetime import datetime

class WebSearchTool:
    """实时联网搜索工具"""
    
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()
    
    async def search(self, query: str, topic_context: str = "") -> List[Dict]:
        """
        执行联网搜索，获取最新信息
        
        Args:
            query: 搜索查询
            topic_context: 话题上下文，用于优化搜索词
        """
        try:
            # 优化搜索词，加入军事/战略相关关键词
            enhanced_query = self._enhance_query(query, topic_context)
            
            # 使用 DuckDuckGo 搜索（无需 API Key）
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    enhanced_query, 
                    max_results=self.max_results,
                    region='cn-zh'  # 中文结果优先
                )
                
                for r in search_results:
                    results.append({
                        "title": r["title"],
                        "url": r["href"],
                        "snippet": r["body"],
                        "source": self._extract_domain(r["href"]),
                        "timestamp": datetime.now().isoformat()
                    })
            
            return results
            
        except Exception as e:
            print(f"搜索出错: {e}")
            return []
    
    def _enhance_query(self, query: str, context: str) -> str:
        """增强搜索查询"""
        # 根据话题添加上下文关键词
        military_keywords = ["军事", "国防", "战略", "作战", "武器", "冲突"]
        tech_keywords = ["AI", "人工智能", "算法", "量子", "芯片", "技术"]
        
        enhanced = query
        if any(k in context for k in military_keywords):
            enhanced += " 军事 战略分析 2024 2025"
        if any(k in context for k in tech_keywords):
            enhanced += " 技术突破 最新进展"
            
        return enhanced
    
    def _extract_domain(self, url: str) -> str:
        """提取域名作为来源"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain.replace("www.", "")
        except:
            return "未知来源"

class SearchAggregator:
    """搜索结果聚合器 - 多源验证"""
    
    def __init__(self):
        self.search_tool = WebSearchTool()
    
    async def multi_source_verify(self, claim: str, topic: str) -> Dict:
        """
        多源验证：对 AI 的声明进行交叉验证
        
        Returns:
            {
                "verified": bool,
                "sources": List[Dict],
                "confidence": float,
                "contradictions": List[str]
            }
        """
        # 并行搜索多个角度
        search_queries = [
            f"{claim} 事实核查",
            f"{claim} 最新消息",
            f"{topic} 权威解读"
        ]
        
        all_results = []
        for query in search_queries:
            results = await self.search_tool.search(query, topic)
            all_results.extend(results)
        
        # 简单去重和可信度评分
        unique_sources = self._deduplicate(all_results)
        confidence = self._calculate_confidence(unique_sources)
        
        return {
            "verified": confidence > 0.6,
            "sources": unique_sources[:3],
            "confidence": confidence,
            "contradictions": []
        }
    
    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []
        for r in results:
            key = r["title"][:30]  # 简单去重
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
    
    def _calculate_confidence(self, sources: List[Dict]) -> float:
        """计算可信度"""
        if not sources:
            return 0.0
        # 基于来源数量简单计算
        base_score = min(len(sources) * 0.3, 0.9)
        # 如果有权威来源加分
        authoritative = ["gov.cn", "military", "defense", "新华社", "央视"]
        bonus = sum(0.1 for s in sources if any(a in s["url"] for a in authoritative))
        return min(base_score + bonus, 1.0)