"""YouTube service for fetching video info and transcripts."""
from typing import Optional, Dict, List
import re
import urllib.parse

# Try to use pytubefix first (more reliable), fallback to pytube
try:
    from pytubefix import YouTube, Search, Channel, Playlist
    from pytubefix.exceptions import VideoUnavailable, RegexMatchError
    USE_PYTUBEFIX = True
except ImportError:
    try:
        from pytube import YouTube, Search, Channel, Playlist
        from pytube.exceptions import VideoUnavailable, RegexMatchError
        USE_PYTUBEFIX = False
    except ImportError:
        raise ImportError("Neither pytubefix nor pytube is installed. Please install one of them.")


class YouTubeService:
    """YouTube service for video info and transcript fetching."""
    
    @staticmethod
    def get_video_info(video_url: str) -> Dict:
        """Get video information.
        
        Args:
            video_url: YouTube video URL or video ID
        
        Returns:
            Dictionary with video info: id, title, channel_id, channel_name, duration, etc.
        """
        try:
            # Extract video ID if full URL provided
            video_id = YouTubeService.extract_video_id(video_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL or video ID")
            
            # Create YouTube object
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            
            # Try to bypass age gate if needed (pytubefix only)
            if USE_PYTUBEFIX:
                try:
                    yt.bypass_age_gate()
                except:
                    pass
            
            return {
                "video_id": video_id,
                "title": yt.title,
                "channel_id": yt.channel_id,
                "channel_name": yt.author,
                "channel_url": yt.channel_url,
                "duration": yt.length,  # in seconds
                "thumbnail_url": yt.thumbnail_url,
                "description": yt.description,
                "view_count": yt.views,
            }
                    
        except (VideoUnavailable, RegexMatchError) as e:
            raise ValueError(f"Video not available: {e}")
        except Exception as e:
            error_msg = str(e)
            # Provide more helpful error message
            if "400" in error_msg or "Bad Request" in error_msg:
                raise RuntimeError(
                    f"Failed to get video info: YouTube API error. "
                    f"This may be due to pytube needing an update. "
                    f"Video ID: {video_id if 'video_id' in locals() else 'unknown'}. "
                    f"Original error: {error_msg}"
                )
            raise RuntimeError(f"Failed to get video info: {error_msg}")
    
    @staticmethod
    def extract_video_id(url_or_id: str) -> Optional[str]:
        """Extract video ID from URL or return as-is if already an ID.
        
        Args:
            url_or_id: YouTube URL or video ID
        
        Returns:
            Video ID or None if invalid
        """
        # If it's already a video ID (11 characters, alphanumeric)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
        
        # Try to extract from URL
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def get_transcript(video_id: str, lang: str = "en") -> Dict:
        """Get video transcript.
        
        Args:
            video_id: YouTube video ID
            lang: Language code (en, ja, etc.)
        
        Returns:
            Dict with 'transcript' (str) and 'segments' (List[Dict])
        """
        try:
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            
            # Try to bypass age gate if needed (pytubefix only)
            if USE_PYTUBEFIX:
                try:
                    yt.bypass_age_gate()
                except:
                    pass
            
            transcript_list = yt.captions
            
            # Build priority list of captions to try
            candidates = []
            
            # 1. Exact match
            if lang in transcript_list:
                candidates.append(transcript_list[lang])
            
            # 2. Japanese variations (since this is a Japanese learning app)
            if 'ja' in transcript_list and transcript_list['ja'] not in candidates:
                candidates.append(transcript_list['ja'])
            if 'a.ja' in transcript_list and transcript_list['a.ja'] not in candidates:
                candidates.append(transcript_list['a.ja'])
                
            # 3. English fallback
            if 'en' in transcript_list and transcript_list['en'] not in candidates:
                candidates.append(transcript_list['en'])
                
            # 4. Any other available captions
            for caption in transcript_list:
                if caption not in candidates:
                    candidates.append(caption)
            
            if not candidates:
                raise ValueError("No transcript available for this video (No captions found).")
            
            last_error = None
            
            # Try each candidate until one works
            for caption in candidates:
                try:
                    if hasattr(caption, 'generate_srt_captions'):
                        transcript_text = caption.generate_srt_captions()
                        segments = YouTubeService._parse_srt(transcript_text)
                        
                        # Validate segments
                        if not segments:
                            # If SRT parsed but empty, try next
                             print(f"[WARNING] Empty segments for caption {caption}")
                             continue
                             
                        return {
                            "transcript": transcript_text,
                            "segments": segments,
                            "lang_code": caption.code
                        }
                    else:
                        print(f"[WARNING] Caption object {caption} has no generate_srt_captions method")
                except Exception as e:
                    last_error = f"{type(e).__name__}: {e}"
                    print(f"[WARNING] Failed to load caption {caption}: {last_error}")
                    continue
            
            # If we get here, all candidates failed
            raise RuntimeError(f"Failed to load any transcript. Last error: {last_error}")

        except Exception as e:
            # Catch top-level errors (like network issues or yt object creation failure)
            raise RuntimeError(f"Failed to get transcript: {e}")
    
    @staticmethod
    def _parse_srt(srt_text: str) -> List[Dict]:
        """Parse SRT format transcript.
        
        Args:
            srt_text: SRT formatted text
        
        Returns:
            List of segments with text, start, and duration
        """
        segments = []
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)'
        
        matches = re.finditer(pattern, srt_text, re.DOTALL)
        
        for match in matches:
            start_str = match.group(2)
            end_str = match.group(3)
            text = match.group(4).strip().replace('\n', ' ')
            
            # Convert time to seconds
            start_seconds = YouTubeService._srt_time_to_seconds(start_str)
            end_seconds = YouTubeService._srt_time_to_seconds(end_str)
            duration = end_seconds - start_seconds
            
            segments.append({
                "text": text,
                "start": start_seconds,
                "duration": duration
            })
        
        return segments
    
    @staticmethod
    def _srt_time_to_seconds(time_str: str) -> float:
        """Convert SRT time format to seconds.
        
        Args:
            time_str: Time in format "HH:MM:SS,mmm"
        
        Returns:
            Time in seconds
        """
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    @staticmethod
    def search_videos(query: str, max_results: int = 10) -> List[Dict]:
        """Search YouTube videos (basic implementation).
        
        Note: pytube doesn't support search directly, this is a placeholder.
        In production, you might want to use YouTube Data API v3.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of video info dictionaries
        """
        """Search YouTube videos (basic implementation).

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of video info dictionaries
        """
        try:
            s = Search(query)
            results = []
            
            # Get up to max_results videos
            videos = s.results[:max_results] if s.results else []
            
            for vid in videos:
                try:
                    # Basic info available in search result
                    video_info = {
                        "id": vid.video_id,
                        "title": vid.title,
                        # Channel info might be limited in search results objects depending on library version
                        # but usually available
                        "channel_name": getattr(vid, 'author', 'Unknown Channel'), 
                        "duration": getattr(vid, 'length', 0),
                        "thumbnail_url": vid.thumbnail_url if hasattr(vid, 'thumbnail_url') else f"https://i.ytimg.com/vi/{vid.video_id}/hqdefault.jpg",
                        "view_count": getattr(vid, 'views', 0)
                    }
                    results.append(video_info)
                except Exception as e:
                    print(f"Error parsing search result item: {e}")
                    continue
                    
            return results
            
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    @staticmethod
    def get_channel_videos(channel_identifier: str, max_results: int = 15) -> List[Dict]:
        """Get videos from a specific channel using handle or URL."""
        try:
            # Construct channel URL
            url = ""
            if "youtube.com" in channel_identifier or "youtu.be" in channel_identifier:
                url = channel_identifier
            elif channel_identifier.startswith("@"):
                url = f"https://www.youtube.com/{channel_identifier}"
            else:
                # If it doesn't look like a handle, try adding @
                url = f"https://www.youtube.com/@{channel_identifier.replace(' ', '')}"
            
            try:
                c = Channel(url)
                results = []
                # Use videos property
                for i, vid in enumerate(c.videos):
                    if i >= max_results:
                        break
                    results.append({
                        "id": vid.video_id,
                        "title": vid.title,
                        "channel_name": getattr(c, 'channel_name', channel_identifier),
                        "duration": getattr(vid, 'length', 0),
                        "thumbnail_url": getattr(vid, 'thumbnail_url', f"https://i.ytimg.com/vi/{vid.video_id}/hqdefault.jpg"),
                        "view_count": getattr(vid, 'views', 0)
                    })
                if results:
                    return results
            except Exception as e:
                print(f"Channel object failed, falling back to search: {e}")
            
            # Fallback: Search for the channel name + videos
            search_query = f"{channel_identifier} videos"
            return YouTubeService.search_videos(search_query)

        except Exception as e:
            print(f"Failed to get channel videos: {e}")
            return []

    @staticmethod
    def get_related_videos(video_id: str) -> Dict[str, List[Dict]]:
        """Get related videos (simulated by searching channel videos).
        
        Args:
            video_id: Video ID to find related videos for
            
        Returns:
            Dict with 'videos' key containing list of video info
        """
        try:
            # First get video info to find the channel/author
            # We use a specialized lightweight check if possible, or just reuse get_video_info
            try:
                yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
                if USE_PYTUBEFIX:
                    try:
                        yt.bypass_age_gate()
                    except:
                        pass
                channel_name = yt.author
                keywords = yt.keywords
            except:
                channel_name = "Japanese Listening"
                keywords = []

            # Construct a search query based on channel or keywords
            query = channel_name
            if keywords and len(keywords) > 0:
                 query += " " + keywords[0]
            
            # Use search_videos
            videos = YouTubeService.search_videos(query, max_results=10)
            
            # Filter out the current video
            filtered_videos = [v for v in videos if v.get('id') != video_id]
            
            return {"videos": filtered_videos}
            
        except Exception as e:
            print(f"[ERROR] Failed to get related videos: {e}")
            return {"videos": []}

    @staticmethod
    def get_channel_playlists(channel_identifier: str, timeout: int = 10) -> List[Dict]:
        """Get playlists for a channel with timeout to prevent UI freezing.
        
        Uses threading to prevent blocking the UI thread for too long.
        Returns empty list if timeout is exceeded.
        """
        import threading
        result_container = {"playlists": [], "done": False}
        
        def fetch_worker():
            try:
                # Improved URL strategy: Try handle with /playlists, then just handle, then /videos as fallback
                urls_to_try = []
                cleaned_id = channel_identifier.strip()
                
                if cleaned_id.startswith("http"):
                    base_url = cleaned_id.split('?')[0].rstrip('/')
                    urls_to_try = [f"{base_url}/playlists", base_url]
                elif cleaned_id.startswith("@"):
                    urls_to_try = [
                        f"https://www.youtube.com/{cleaned_id}/playlists",
                        f"https://www.youtube.com/{cleaned_id}",
                    ]
                else:
                    # Clean identifier for URL - handle special characters for Vietnamese names if no handle provided
                    url_id = cleaned_id.replace(" ", "")
                    # If it has non-ascii, it's likely a name not a handle, but we try anyway
                    urls_to_try = [
                        f"https://www.youtube.com/@{url_id}/playlists",
                        f"https://www.youtube.com/@{url_id}",
                    ]
                
                print(f"[Playlist] Using identifier: {channel_identifier}")
                print(f"[Playlist] Trying URLs: {urls_to_try}")
                
                found_channel = False
                for url in urls_to_try:
                    if found_channel: break
                    try:
                        print(f"[Playlist] Attempting: {url}")
                        c = Channel(url)
                        
                        # Try to access playlists
                        if hasattr(c, 'playlists'):
                            playlists = []
                            playlist_iter = iter(c.playlists)
                            
                            for i in range(50):  # Limit to 50 playlists
                                try:
                                    p = next(playlist_iter)
                                    playlists.append({
                                        "title": p.title,
                                        "url": p.playlist_url,
                                        "id": p.playlist_id
                                    })
                                    print(f"[Playlist] Found: {p.title} -> {p.playlist_url}")
                                except StopIteration:
                                    break
                                except Exception as e:
                                    print(f"[Playlist] Error parsing playlist item: {e}")
                                    continue
                            
                            if playlists:
                                print(f"[Playlist] Total found: {len(playlists)}")
                                result_container["playlists"] = playlists
                                result_container["done"] = True
                                found_channel = True
                                return
                                
                    except Exception as e:
                        print(f"[Playlist] Failed for {url}: {e}")
                        continue
                
                # FALLBACK: Search for channel if direct URLs failed
                if not found_channel and not channel_identifier.startswith("http"):
                    try:
                        print(f"[Playlist] Fallback: Searching for channel '{channel_identifier}'")
                        from pytubefix import Search
                        s = Search(channel_identifier)
                        if s.results:
                            first_video = s.results[0]
                            channel_url = first_video.channel_url
                            print(f"[Playlist] Found channel URL via search: {channel_url}")
                            c = Channel(channel_url)
                            playlists = []
                            for p in c.playlists:
                                playlists.append({
                                    "title": p.title,
                                    "url": p.playlist_url,
                                    "id": p.playlist_id
                                })
                            if playlists:
                                result_container["playlists"] = playlists
                                result_container["done"] = True
                                return
                    except Exception as se:
                        print(f"[Playlist] Fallback search failed: {se}")

                print("[Playlist] No playlists found on any URL or search")
                result_container["done"] = True
                
            except Exception as e:
                print(f"[Playlist] Worker error: {e}")
                result_container["done"] = True
        
        # Start worker thread
        worker = threading.Thread(target=fetch_worker, daemon=True)
        worker.start()
        
        # Wait with timeout
        worker.join(timeout=timeout)
        
        if not result_container["done"]:
            print(f"[Playlist] Timeout after {timeout}s for: {channel_identifier}")
            return []
        
        return result_container["playlists"]

    @staticmethod
    def get_playlist_videos(playlist_url: str, max_results: int = 50) -> List[Dict]:
        """Get videos from a playlist with robust fallback."""
        try:
            print(f"[YouTubeService] Fetching videos for playlist: {playlist_url}")
            p = Playlist(playlist_url)
            results = []
            
            # Try to get videos. Use video_urls as it's more stable than .videos in some versions
            try:
                # Get basic info from video objects if possible
                count = 0
                for vid in p.videos:
                    if count >= max_results: break
                    try:
                        results.append({
                            "id": vid.video_id,
                            "title": vid.title,
                            "channel_name": getattr(p, 'owner', 'YouTube'), 
                            "duration": getattr(vid, 'length', 0),
                            "thumbnail_url": vid.thumbnail_url,
                            "view_count": getattr(vid, 'views', 0)
                        })
                        count += 1
                    except Exception as e:
                        print(f"Skipping video in playlist: {e}")
            except Exception as e:
                print(f"Direct video access failed, trying via URLs: {e}")
                # Fallback: create Video objects from URLs manually
                count = 0
                for url in p.video_urls:
                    if count >= max_results: break
                    try:
                        vid = YouTube(url)
                        results.append({
                            "id": vid.video_id,
                            "title": vid.title,
                            "channel_name": getattr(p, 'owner', 'YouTube'),
                            "duration": vid.length,
                            "thumbnail_url": vid.thumbnail_url,
                            "view_count": vid.views
                        })
                        count += 1
                    except:
                        continue
            
            print(f"[YouTubeService] Successfully fetched {len(results)} videos from playlist")
            return results
        except Exception as e:
             print(f"Error fetching playlist videos: {e}")
             return []

