"""Content extractor for external article URLs.

Uses trafilatura for robust article extraction from web pages.
Trafilatura is specifically designed for extracting article content.
"""

import aiohttp
import asyncio
from typing import Optional, Tuple

# Try trafilatura first (best for articles), fallback to basic extraction
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False
    print("[ContentExtractor] trafilatura not installed, using basic extraction")


class ContentExtractor:
    """Extract article content from external URLs."""
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    @staticmethod
    async def fetch_html(url: str, timeout: int = 15) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            async with aiohttp.ClientSession(headers=ContentExtractor.DEFAULT_HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"[ContentExtractor] HTTP {response.status} for {url[:50]}")
                        return None
        except asyncio.TimeoutError:
            print(f"[ContentExtractor] Timeout fetching {url[:50]}")
            return None
        except Exception as e:
            print(f"[ContentExtractor] Error fetching {url[:50]}: {e}")
            return None
    
    @staticmethod
    def extract_with_trafilatura(html: str, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract content using trafilatura (best quality)."""
        if not HAS_TRAFILATURA:
            return None, None
        
        try:
            # Extract main content as markdown-like text
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=True,
                url=url
            )
            
            # Also get HTML version if needed
            html_content = trafilatura.extract(
                html,
                output_format='html',
                include_comments=False,
                include_tables=True,
                url=url
            )
            
            return text, html_content
        except Exception as e:
            print(f"[ContentExtractor] Trafilatura error: {e}")
            return None, None
    
    @staticmethod
    def extract_basic(html: str) -> Tuple[Optional[str], Optional[str]]:
        """Basic extraction using BeautifulSoup (fallback)."""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                tag.decompose()
            
            # Try to find article content
            article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
            
            if article:
                text = article.get_text(separator='\n', strip=True)
                html_content = str(article)
            else:
                # Fallback to body
                body = soup.find('body')
                if body:
                    text = body.get_text(separator='\n', strip=True)
                    html_content = str(body)
                else:
                    text = soup.get_text(separator='\n', strip=True)
                    html_content = str(soup)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n\n'.join(lines)
            
            # Limit length
            if len(text) > 50000:
                text = text[:50000] + "..."
            
            return text, html_content
            
        except Exception as e:
            print(f"[ContentExtractor] Basic extraction error: {e}")
            return None, None
    
    @classmethod
    async def extract_article(cls, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract article content from URL.
        
        Returns:
            Tuple of (text_content, html_content) or (None, None) on failure
        """
        # Skip certain URLs that won't work
        skip_domains = ['github.com', 'twitter.com', 'youtube.com', 'reddit.com']
        for domain in skip_domains:
            if domain in url:
                return (f"Nội dung từ {domain} không thể trích xuất tự động.\n\nVui lòng nhấn 'Mở nguồn' để xem.", None)
        
        # Fetch HTML
        html = await cls.fetch_html(url)
        if not html:
            return None, None
        
        # Extract content
        if HAS_TRAFILATURA:
            text, html_content = cls.extract_with_trafilatura(html, url)
            if text:
                return text, html_content
        
        # Fallback to basic extraction
        return cls.extract_basic(html)


# Synchronous wrapper for convenience
def extract_article_sync(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Synchronous wrapper for article extraction."""
    return asyncio.run(ContentExtractor.extract_article(url))
