"""Smart filtering engine for tech news.

Filters articles based on "hardcore" developer interests.
Works with both English and Japanese sources.
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass
import re


# =============================================================================
# HARDCORE DEVELOPER TAGS
# =============================================================================
# These are the tags that match the user's interests:
# - AI/ML focus
# - System-level programming
# - DevOps/Automation
# - Cutting-edge tech

HARDCORE_TAGS: Dict[str, List[str]] = {
    # Core Languages & Paradigms
    "core": [
        "python", "rust", "go", "c++", "cpp",
        "machine-learning", "machinelearning", "機械学習",
        "ai", "artificial-intelligence", "人工知能",
        "data-science", "データサイエンス",
        "system-design", "architecture", "設計",
    ],
    
    # Hardware & AI Models
    "hardware_ai": [
        "nvidia", "cuda", "gpu", "vram", "tensor",
        "llm", "large-language-model", "大規模言語モデル",
        "llama", "mistral", "gemma", "phi",
        "genai", "generative-ai", "生成ai",
        "deep-learning", "deeplearning", "ディープラーニング", "深層学習",
        "openai", "gpt", "chatgpt", "claude", "gemini",
        "nlp", "natural-language-processing", "自然言語処理",
        "transformer", "attention", "rag",
        "fine-tuning", "lora", "qlora", "quantization",
    ],
    
    # Automation & DevOps
    "automation": [
        "automation", "自動化",
        "github-actions", "githubactions", "ci-cd", "cicd",
        "docker", "kubernetes", "k8s", "container",
        "devops", "sre", "infrastructure",
        "terraform", "ansible", "pulumi",
    ],
    
    # Vision & Robotics
    "vision": [
        "computer-vision", "computervision", "コンピュータビジョン",
        "opencv", "画像処理", "image-processing",
        "3d", "3dcg", "blender", "unity",
        "robotics", "ロボット", "ros", "ros2",
        "autonomous", "自動運転",
        "yolo", "object-detection", "segmentation",
    ],
    
    # Startup & Performance Vibe
    "vibe": [
        "startup", "スタートアップ",
        "performance", "optimization", "最適化", "高速化",
        "open-source", "opensource", "オープンソース", "oss",
        "benchmark", "ベンチマーク",
        "productivity", "生産性",
        "career", "キャリア",
    ],
}


def get_all_tags_flat() -> Set[str]:
    """Get all tags as a flat set for quick lookup."""
    all_tags = set()
    for category_tags in HARDCORE_TAGS.values():
        all_tags.update(tag.lower() for tag in category_tags)
    return all_tags


# Pre-compute for performance
_ALL_TAGS_FLAT = get_all_tags_flat()


@dataclass
class FilterResult:
    """Result of filtering an article."""
    is_match: bool
    matched_tags: List[str]
    score: float  # 0.0 to 1.0, higher = more relevant
    matched_categories: List[str]


class SmartFilter:
    """Smart filtering engine for tech news articles.
    
    Features:
    - Multi-language tag matching (EN + JP)
    - Category-based scoring
    - Configurable strictness
    
    Usage:
        filter = SmartFilter()
        
        # Check single article
        result = filter.check_article(article)
        if result.is_match:
            print(f"Matched tags: {result.matched_tags}")
        
        # Filter list of articles
        filtered = filter.filter_articles(articles)
    """
    
    def __init__(
        self,
        enabled_categories: Optional[List[str]] = None,
        custom_tags: Optional[List[str]] = None,
        min_score: float = 0.0
    ):
        """Initialize filter.
        
        Args:
            enabled_categories: List of category names to use (default: all)
            custom_tags: Additional custom tags to match
            min_score: Minimum score threshold (0.0 to 1.0)
        """
        self.enabled_categories = enabled_categories or list(HARDCORE_TAGS.keys())
        self.custom_tags = set(tag.lower() for tag in (custom_tags or []))
        self.min_score = min_score
        
        # Build active tag set
        self._active_tags: Set[str] = set()
        for cat in self.enabled_categories:
            if cat in HARDCORE_TAGS:
                self._active_tags.update(
                    tag.lower() for tag in HARDCORE_TAGS[cat]
                )
        self._active_tags.update(self.custom_tags)
    
    def _normalize_tag(self, tag: str) -> str:
        """Normalize tag for comparison."""
        # Lowercase
        tag = tag.lower().strip()
        # Remove common separators and normalize
        tag = re.sub(r'[-_\s]+', '-', tag)
        return tag
    
    def _extract_tags_from_text(self, text: str) -> Set[str]:
        """Extract potential tags from title/content."""
        if not text:
            return set()
        
        text_lower = text.lower()
        found_tags = set()
        
        # Check each active tag
        for tag in self._active_tags:
            # For Japanese tags, do substring match
            if any(ord(c) > 127 for c in tag):  # Contains non-ASCII
                if tag in text_lower:
                    found_tags.add(tag)
            else:
                # For English tags, do word boundary match
                pattern = r'\b' + re.escape(tag.replace('-', r'[-_\s]?')) + r'\b'
                if re.search(pattern, text_lower):
                    found_tags.add(tag)
        
        return found_tags
    
    def check_article(self, article) -> FilterResult:
        """Check if an article matches the filter criteria.
        
        Args:
            article: Article object with tags, title, summary
            
        Returns:
            FilterResult with match status and details
        """
        matched_tags: Set[str] = set()
        matched_categories: Set[str] = set()
        
        # 1. Check article's own tags
        if hasattr(article, 'tags') and article.tags:
            for tag in article.tags:
                normalized = self._normalize_tag(tag)
                if normalized in self._active_tags:
                    matched_tags.add(normalized)
                    # Find which category
                    for cat, cat_tags in HARDCORE_TAGS.items():
                        if cat in self.enabled_categories:
                            if normalized in [t.lower() for t in cat_tags]:
                                matched_categories.add(cat)
        
        # 2. Extract tags from title
        if hasattr(article, 'title') and article.title:
            title_tags = self._extract_tags_from_text(article.title)
            matched_tags.update(title_tags)
        
        # 3. Extract tags from summary (lower weight)
        if hasattr(article, 'summary') and article.summary:
            summary_tags = self._extract_tags_from_text(article.summary)
            matched_tags.update(summary_tags)
        
        # Calculate score
        if not matched_tags:
            score = 0.0
        else:
            # Score based on number of unique tags and categories
            tag_score = min(len(matched_tags) / 5.0, 1.0)  # Max at 5 tags
            cat_score = len(matched_categories) / len(self.enabled_categories)
            score = (tag_score * 0.7) + (cat_score * 0.3)
        
        is_match = len(matched_tags) > 0 and score >= self.min_score
        
        return FilterResult(
            is_match=is_match,
            matched_tags=list(matched_tags),
            score=score,
            matched_categories=list(matched_categories)
        )
    
    def filter_articles(
        self,
        articles: list,
        sort_by_score: bool = True
    ) -> list:
        """Filter a list of articles.
        
        Args:
            articles: List of Article objects
            sort_by_score: If True, sort results by relevance score
            
        Returns:
            List of matching articles
        """
        results = []
        
        for article in articles:
            result = self.check_article(article)
            if result.is_match:
                # Store filter result on article for later use
                article._filter_result = result
                results.append(article)
        
        if sort_by_score:
            results.sort(
                key=lambda a: getattr(a, '_filter_result', FilterResult(False, [], 0, [])).score,
                reverse=True
            )
        
        return results
    
    def get_active_tags(self) -> List[str]:
        """Get list of all active tags."""
        return sorted(self._active_tags)
    
    def get_enabled_categories(self) -> List[str]:
        """Get list of enabled categories."""
        return self.enabled_categories.copy()
