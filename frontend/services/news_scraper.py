"""News scraping service for BBC, CNN, NHK, Asahi Shimbun."""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import re


class NewsScraperService:
    """News scraping service."""
    @staticmethod
    def get_news_sources() -> List[Dict]:
        """Get pre-defined news sources."""
        return [
            {"id": "https://www.bbc.com/news", "name": "BBC News (EN)"},
            {"id": "https://edition.cnn.com", "name": "CNN (EN)"},
            {"id": "https://www3.nhk.or.jp/news/", "name": "NHK News (JP)"},
            {"id": "https://www.asahi.com/", "name": "Asahi Shimbun (JP)"},
        ]
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    @staticmethod
    def scrape_article(url: str) -> Dict:
        """Scrape article content from URL.
        
        Args:
            url: Article URL
        
        Returns:
            Dictionary with title, content, published_at
        """
        try:
            # Increase timeout and add retry logic
            try:
                response = requests.get(
                    url, 
                    headers=NewsScraperService.HEADERS, 
                    timeout=15,
                    verify=True,
                    allow_redirects=True
                )
                response.raise_for_status()
            except requests.exceptions.ConnectionError as e:
                raise RuntimeError(f"Không thể kết nối đến {url}. Vui lòng kiểm tra kết nối internet.")
            except requests.exceptions.Timeout as e:
                raise RuntimeError(f"Kết nối quá thời gian chờ đến {url}.")
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Lỗi khi tải bài viết: {str(e)}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try to extract title
            title = None
            title_tags = soup.find_all(['h1', 'title'])
            if title_tags:
                title = title_tags[0].get_text(strip=True)
            
            # Try to extract main content - site-specific selectors
            content = None
            
            # Check if this is NHK News
            is_nhk = 'nhk.or.jp' in url or 'news.web.nhk' in url
            
            if is_nhk:
                # NHK News specific selectors
                nhk_selectors = [
                    '.content--detail',
                    '.content-body',
                    '.article-body',
                    '.news-content',
                    '.content-body__text',
                    '[class*="content"]',
                    '[class*="article"]',
                    'main article',
                    'main .content'
                ]
                
                for selector in nhk_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        # Get all paragraphs within the content element
                        paragraphs = content_elem.find_all('p')
                        if paragraphs:
                            content_parts = []
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text and len(text) > 10:  # Filter out very short paragraphs
                                    content_parts.append(text)
                            if content_parts:
                                content = '\n\n'.join(content_parts)
                                break
                
                # If still no content, try to find main content area
                if not content:
                    main_content = soup.find('main') or soup.find('article')
                    if main_content:
                        # Remove unwanted elements
                        for unwanted in main_content.find_all(['nav', 'header', 'footer', 'aside', 'div', 'section'], 
                                                              class_=re.compile(r'nav|menu|sidebar|ad|social|share|comment')):
                            unwanted.decompose()
                        
                        paragraphs = main_content.find_all('p')
                        if paragraphs:
                            content_parts = []
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text and len(text) > 10:
                                    content_parts.append(text)
                            if content_parts:
                                content = '\n\n'.join(content_parts)
            
            # Common content selectors for other sites
            if not content:
                content_selectors = [
                    'article',
                    '.article-body',
                    '.content',
                    '.post-content',
                    'main',
                    '#main-content',
                    '.entry-content',
                    '.article-content'
                ]
                
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        # Get paragraphs for better formatting
                        paragraphs = content_elem.find_all('p')
                        if paragraphs:
                            content_parts = []
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text and len(text) > 10:
                                    content_parts.append(text)
                            if content_parts:
                                content = '\n\n'.join(content_parts)
                                break
                        else:
                            content = content_elem.get_text(separator='\n\n', strip=True)
                            if content and len(content) > 50:
                                break
            
            # Fallback: get all paragraphs from body
            if not content or len(content) < 50:
                body = soup.find('body')
                if body:
                    paragraphs = body.find_all('p')
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        # Filter out navigation, ads, etc.
                        if text and len(text) > 20 and not re.search(r'^(メニュー|ナビ|広告|広告|シェア|コメント)', text):
                            content_parts.append(text)
                    if content_parts:
                        content = '\n\n'.join(content_parts)
            
            # Try to extract published date
            published_at = None
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}',
                r'\d{4}年\d{1,2}月\d{1,2}日',
            ]
            
            time_tags = soup.find_all(['time', 'span', 'div'], class_=re.compile(r'date|time|published|datetime'))
            if time_tags:
                for tag in time_tags:
                    text = tag.get_text()
                    datetime_attr = tag.get('datetime') or tag.get('data-time')
                    if datetime_attr:
                        for pattern in date_patterns:
                            match = re.search(pattern, datetime_attr)
                            if match:
                                try:
                                    if '年' in match.group():
                                        # Japanese date format
                                        date_str = match.group().replace('年', '-').replace('月', '-').replace('日', '')
                                        published_at = datetime.strptime(date_str, "%Y-%m-%d")
                                    else:
                                        published_at = datetime.strptime(match.group(), "%Y-%m-%d")
                                    break
                                except:
                                    pass
                    if not published_at:
                        for pattern in date_patterns:
                            match = re.search(pattern, text)
                            if match:
                                try:
                                    if '年' in match.group():
                                        date_str = match.group().replace('年', '-').replace('月', '-').replace('日', '')
                                        published_at = datetime.strptime(date_str, "%Y-%m-%d")
                                    else:
                                        published_at = datetime.strptime(match.group(), "%Y-%m-%d")
                                    break
                                except:
                                    pass
            
            # Extract images
            images = []
            from urllib.parse import urljoin, urlparse
            base_url = urlparse(url).scheme + "://" + urlparse(url).netloc
            
            # Find all images in the article
            img_tags = soup.find_all('img')
            for img in img_tags:
                img_src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if img_src:
                    # Make absolute URL
                    if img_src.startswith('//'):
                        img_src = urlparse(url).scheme + ':' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(base_url, img_src)
                    elif not img_src.startswith('http'):
                        img_src = urljoin(url, img_src)
                    
                    # Filter out small icons, logos, etc.
                    img_alt = img.get('alt', '').lower()
                    img_class = img.get('class', [])
                    class_str = ' '.join(img_class).lower() if isinstance(img_class, list) else str(img_class).lower()
                    
                    # Skip if it's likely an icon/logo
                    if any(skip in img_alt or skip in class_str for skip in ['icon', 'logo', 'avatar', 'thumbnail']):
                        continue
                    
                    images.append(img_src)
            
            return {
                "title": title or "Untitled",
                "content": content or "",
                "published_at": published_at,
                "images": images[:10]  # Limit to 10 images
            }
        except Exception as e:
            raise RuntimeError(f"Failed to scrape article: {e}")
    
    @staticmethod
    def get_latest_articles(source_url: str, max_articles: int = 10) -> List[Dict]:
        """Get latest articles from a news source.
        
        Args:
            source_url: News source homepage URL
            max_articles: Maximum number of articles to fetch
        
        Returns:
            List of article info: {url, title, published_at}
        """
        try:
            # Increase timeout and add retry logic
            try:
                response = requests.get(
                    source_url, 
                    headers=NewsScraperService.HEADERS, 
                    timeout=15,
                    verify=True,
                    allow_redirects=True
                )
                response.raise_for_status()
            except requests.exceptions.ConnectionError as e:
                raise RuntimeError(f"Không thể kết nối đến {source_url}. Vui lòng kiểm tra kết nối internet.")
            except requests.exceptions.Timeout as e:
                raise RuntimeError(f"Kết nối quá thời gian chờ đến {source_url}.")
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Lỗi khi tải trang: {str(e)}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            from urllib.parse import urljoin, urlparse
            
            # Site-specific parsing
            domain = urlparse(source_url).netloc.lower()
            
            # CNN
            if 'cnn.com' in domain:
                # CNN uses various selectors
                selectors = [
                    'a[data-module-name="Article"]',
                    'a[data-module-name="Card"]',
                    '.container__item a',
                    '.cd__headline a',
                    'h3 a',
                    'article a'
                ]
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href', '')
                        if not href:
                            continue
                        if href.startswith('/'):
                            href = urljoin('https://www.cnn.com', href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 15 and 'cnn.com' in href:
                            articles.append({
                                "url": href,
                                "title": title,
                                "published_at": None
                            })
                            if len(articles) >= max_articles:
                                break
                    if len(articles) >= max_articles:
                        break
            
            # BBC News
            elif 'bbc.com' in domain or 'bbc.co.uk' in domain:
                selectors = [
                    'a[data-testid="internal-link"]',
                    '.gs-c-promo-heading a',
                    'h3 a',
                    'article a'
                ]
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href', '')
                        if not href:
                            continue
                        if href.startswith('/'):
                            href = urljoin('https://www.bbc.com', href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 15 and ('bbc.com' in href or 'bbc.co.uk' in href):
                            articles.append({
                                "url": href,
                                "title": title,
                                "published_at": None
                            })
                            if len(articles) >= max_articles:
                                break
                    if len(articles) >= max_articles:
                        break
            
            # NHK News
            elif 'nhk.or.jp' in domain or 'news.web.nhk' in domain:
                selectors = [
                    '.content--list a',
                    '.news-list-item a',
                    'article a',
                    '.news-item a',
                    'a[href*="/news/"]'
                ]
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href', '')
                        if not href:
                            continue
                        if href.startswith('/'):
                            href = urljoin('https://www3.nhk.or.jp', href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 10 and ('nhk.or.jp' in href or 'news.web.nhk' in href):
                            articles.append({
                                "url": href,
                                "title": title,
                                "published_at": None
                            })
                            if len(articles) >= max_articles:
                                break
                    if len(articles) >= max_articles:
                        break
            
            # Asahi Shimbun
            elif 'asahi.com' in domain:
                selectors = [
                    '.List a',
                    '.ArticleList a',
                    'article a',
                    'a[href*="/articles/"]'
                ]
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href', '')
                        if not href:
                            continue
                        if href.startswith('/'):
                            href = urljoin('https://www.asahi.com', href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 10 and 'asahi.com' in href:
                            articles.append({
                                "url": href,
                                "title": title,
                                "published_at": None
                            })
                            if len(articles) >= max_articles:
                                break
                    if len(articles) >= max_articles:
                        break
            
            # Fallback: generic parsing
            if not articles:
                article_links = soup.find_all('a', href=True)
                seen_urls = set()
                for link in article_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    if href.startswith('/'):
                        href = urljoin(source_url, href)
                    text = link.get_text(strip=True)
                    
                    # Filter valid article links
                    if text and len(text) > 20 and href not in seen_urls:
                        seen_urls.add(href)
                        articles.append({
                            "url": href,
                            "title": text,
                            "published_at": None
                        })
                        if len(articles) >= max_articles:
                            break
            
            return articles[:max_articles]
        except Exception as e:
            raise RuntimeError(f"Failed to get latest articles: {e}")

