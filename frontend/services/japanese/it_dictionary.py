"""IT/Tech Dictionary for programmers.

Provides quick lookup for technical terms in English, Japanese, and Vietnamese.
Focuses on programming, AI/ML, DevOps, and system design terminology.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import re


@dataclass
class TermDefinition:
    """A dictionary term with translations and examples."""
    term: str               # Original term (usually English)
    japanese: str           # Japanese translation/reading
    vietnamese: str         # Vietnamese translation
    category: str           # Category (AI, DevOps, Programming, etc.)
    definition: str         # Detailed definition in Vietnamese
    example: Optional[str] = None  # Example usage
    related: Optional[List[str]] = None  # Related terms


# =============================================================================
# BUILT-IN TECH DICTIONARY
# =============================================================================

TECH_DICTIONARY: Dict[str, TermDefinition] = {
    # === AI/ML Terms ===
    "machine learning": TermDefinition(
        term="Machine Learning",
        japanese="機械学習 (きかいがくしゅう)",
        vietnamese="Học máy",
        category="AI/ML",
        definition="Lĩnh vực AI cho phép máy tính học từ dữ liệu mà không cần lập trình tường minh.",
        example="Dùng machine learning để dự đoán giá nhà.",
        related=["deep learning", "neural network", "training"]
    ),
    "deep learning": TermDefinition(
        term="Deep Learning",
        japanese="深層学習 (しんそうがくしゅう)",
        vietnamese="Học sâu",
        category="AI/ML",
        definition="Nhánh của ML sử dụng mạng neural nhiều tầng để học các đặc trưng phức tạp.",
        example="Deep learning được dùng trong nhận dạng hình ảnh.",
        related=["CNN", "RNN", "transformer"]
    ),
    "neural network": TermDefinition(
        term="Neural Network",
        japanese="ニューラルネットワーク / 神経網",
        vietnamese="Mạng nơ-ron",
        category="AI/ML",
        definition="Mô hình tính toán lấy cảm hứng từ não người, gồm các node kết nối với nhau.",
        related=["neuron", "layer", "activation function"]
    ),
    "llm": TermDefinition(
        term="LLM (Large Language Model)",
        japanese="大規模言語モデル (だいきぼげんごモデル)",
        vietnamese="Mô hình ngôn ngữ lớn",
        category="AI/ML",
        definition="Mô hình AI được huấn luyện trên lượng text khổng lồ, có khả năng hiểu và sinh văn bản.",
        example="GPT-4, Claude, Gemini là các LLM phổ biến.",
        related=["GPT", "transformer", "fine-tuning"]
    ),
    "transformer": TermDefinition(
        term="Transformer",
        japanese="トランスフォーマー",
        vietnamese="Bộ biến đổi / Kiến trúc Transformer",
        category="AI/ML",
        definition="Kiến trúc neural network sử dụng cơ chế attention, nền tảng của GPT và BERT.",
        related=["attention", "self-attention", "encoder", "decoder"]
    ),
    "fine-tuning": TermDefinition(
        term="Fine-tuning",
        japanese="ファインチューニング / 微調整",
        vietnamese="Tinh chỉnh",
        category="AI/ML",
        definition="Quá trình điều chỉnh model đã được pre-train cho task cụ thể.",
        example="Fine-tune GPT-4 cho chatbot chăm sóc khách hàng."
    ),
    "inference": TermDefinition(
        term="Inference",
        japanese="推論 (すいろん)",
        vietnamese="Suy luận",
        category="AI/ML",
        definition="Quá trình sử dụng model đã train để đưa ra dự đoán trên dữ liệu mới.",
        related=["training", "prediction"]
    ),
    "embedding": TermDefinition(
        term="Embedding",
        japanese="埋め込み (うめこみ) / エンベディング",
        vietnamese="Nhúng / Vector nhúng",
        category="AI/ML",
        definition="Biểu diễn dữ liệu (từ, câu, hình ảnh) dưới dạng vector số trong không gian đa chiều.",
        example="Word2Vec tạo embedding cho từ vựng."
    ),
    "gpu": TermDefinition(
        term="GPU",
        japanese="GPU / グラフィックスプロセッシングユニット",
        vietnamese="Card đồ họa / Bộ xử lý đồ họa",
        category="Hardware",
        definition="Vi xử lý chuyên biệt cho tính toán song song, rất hiệu quả cho training AI.",
        related=["CUDA", "VRAM", "NVIDIA"]
    ),
    "cuda": TermDefinition(
        term="CUDA",
        japanese="CUDA (クーダ)",
        vietnamese="CUDA",
        category="Hardware",
        definition="Nền tảng tính toán song song của NVIDIA, cho phép lập trình GPU.",
        example="PyTorch sử dụng CUDA để tăng tốc training."
    ),
    
    # === Programming Terms ===
    "api": TermDefinition(
        term="API",
        japanese="API / アプリケーションプログラミングインターフェース",
        vietnamese="Giao diện lập trình ứng dụng",
        category="Programming",
        definition="Tập hợp các quy tắc cho phép các ứng dụng giao tiếp với nhau.",
        example="REST API để lấy dữ liệu từ server."
    ),
    "framework": TermDefinition(
        term="Framework",
        japanese="フレームワーク",
        vietnamese="Khung phần mềm",
        category="Programming",
        definition="Bộ công cụ và thư viện cung cấp cấu trúc cơ bản để phát triển ứng dụng.",
        example="Django, React, PyTorch là các framework phổ biến."
    ),
    "library": TermDefinition(
        term="Library",
        japanese="ライブラリ",
        vietnamese="Thư viện",
        category="Programming",
        definition="Tập hợp các hàm/class được đóng gói sẵn để tái sử dụng.",
        example="NumPy là thư viện tính toán số học cho Python."
    ),
    "algorithm": TermDefinition(
        term="Algorithm",
        japanese="アルゴリズム / 算法",
        vietnamese="Thuật toán",
        category="Programming",
        definition="Tập hợp các bước logic để giải quyết một vấn đề.",
        related=["time complexity", "space complexity"]
    ),
    "recursion": TermDefinition(
        term="Recursion",
        japanese="再帰 (さいき)",
        vietnamese="Đệ quy",
        category="Programming",
        definition="Kỹ thuật lập trình trong đó hàm gọi lại chính nó.",
        example="Tính factorial bằng đệ quy: n! = n * (n-1)!"
    ),
    "refactoring": TermDefinition(
        term="Refactoring",
        japanese="リファクタリング",
        vietnamese="Tái cấu trúc mã",
        category="Programming",
        definition="Cải thiện cấu trúc code mà không thay đổi hành vi.",
        related=["clean code", "code smell"]
    ),
    "debugging": TermDefinition(
        term="Debugging",
        japanese="デバッグ",
        vietnamese="Gỡ lỗi",
        category="Programming",
        definition="Quá trình tìm và sửa lỗi trong phần mềm.",
        related=["breakpoint", "stack trace", "logging"]
    ),
    "compile": TermDefinition(
        term="Compile",
        japanese="コンパイル",
        vietnamese="Biên dịch",
        category="Programming",
        definition="Chuyển đổi mã nguồn thành mã máy có thể thực thi.",
        related=["interpreter", "bytecode"]
    ),
    "runtime": TermDefinition(
        term="Runtime",
        japanese="ランタイム / 実行時",
        vietnamese="Thời gian chạy",
        category="Programming",
        definition="Thời điểm chương trình đang thực thi (so với compile time).",
        example="Lỗi runtime xảy ra khi chương trình đang chạy."
    ),
    
    # === DevOps Terms ===
    "docker": TermDefinition(
        term="Docker",
        japanese="Docker (ドッカー)",
        vietnamese="Docker",
        category="DevOps",
        definition="Nền tảng containerization cho phép đóng gói ứng dụng cùng dependencies.",
        related=["container", "image", "Kubernetes"]
    ),
    "container": TermDefinition(
        term="Container",
        japanese="コンテナ",
        vietnamese="Container / Thùng chứa",
        category="DevOps",
        definition="Đơn vị đóng gói phần mềm nhẹ, chứa đủ để chạy ứng dụng.",
        example="Docker container chạy độc lập với hệ thống host."
    ),
    "kubernetes": TermDefinition(
        term="Kubernetes",
        japanese="Kubernetes (クーバネティス) / K8s",
        vietnamese="Kubernetes / K8s",
        category="DevOps",
        definition="Hệ thống orchestration để quản lý containers ở quy mô lớn.",
        related=["pod", "deployment", "service"]
    ),
    "ci/cd": TermDefinition(
        term="CI/CD",
        japanese="CI/CD",
        vietnamese="Tích hợp liên tục / Triển khai liên tục",
        category="DevOps",
        definition="Quy trình tự động hóa build, test và deploy phần mềm.",
        example="GitHub Actions là công cụ CI/CD phổ biến."
    ),
    "deployment": TermDefinition(
        term="Deployment",
        japanese="デプロイメント / デプロイ",
        vietnamese="Triển khai",
        category="DevOps",
        definition="Quá trình đưa ứng dụng lên môi trường production.",
        related=["staging", "production", "rollback"]
    ),
    "microservice": TermDefinition(
        term="Microservice",
        japanese="マイクロサービス",
        vietnamese="Microservice / Vi dịch vụ",
        category="Architecture",
        definition="Kiến trúc chia ứng dụng thành các service nhỏ, độc lập.",
        related=["monolith", "API gateway", "service mesh"]
    ),
    
    # === Database Terms ===
    "database": TermDefinition(
        term="Database",
        japanese="データベース",
        vietnamese="Cơ sở dữ liệu",
        category="Database",
        definition="Hệ thống lưu trữ và quản lý dữ liệu có tổ chức."
    ),
    "query": TermDefinition(
        term="Query",
        japanese="クエリ",
        vietnamese="Truy vấn",
        category="Database",
        definition="Câu lệnh yêu cầu dữ liệu từ database.",
        example="SELECT * FROM users WHERE age > 18"
    ),
    "index": TermDefinition(
        term="Index",
        japanese="インデックス / 索引",
        vietnamese="Chỉ mục",
        category="Database",
        definition="Cấu trúc dữ liệu giúp tăng tốc độ truy vấn.",
        related=["B-tree", "hash index"]
    ),
    "cache": TermDefinition(
        term="Cache",
        japanese="キャッシュ",
        vietnamese="Bộ nhớ đệm",
        category="System",
        definition="Lưu trữ tạm thời dữ liệu để truy xuất nhanh hơn.",
        example="Redis thường được dùng làm cache layer."
    ),
    
    # === Web Terms ===
    "frontend": TermDefinition(
        term="Frontend",
        japanese="フロントエンド",
        vietnamese="Giao diện người dùng / Frontend",
        category="Web",
        definition="Phần ứng dụng mà người dùng tương tác trực tiếp (UI).",
        related=["React", "Vue", "CSS"]
    ),
    "backend": TermDefinition(
        term="Backend",
        japanese="バックエンド",
        vietnamese="Phía máy chủ / Backend",
        category="Web",
        definition="Phần xử lý logic, database, server của ứng dụng.",
        related=["Node.js", "Django", "FastAPI"]
    ),
    "restful": TermDefinition(
        term="RESTful",
        japanese="RESTful (レストフル)",
        vietnamese="RESTful",
        category="Web",
        definition="Kiến trúc API dựa trên HTTP methods (GET, POST, PUT, DELETE).",
        related=["endpoint", "HTTP", "JSON"]
    ),
    
    # === Security Terms ===
    "authentication": TermDefinition(
        term="Authentication",
        japanese="認証 (にんしょう)",
        vietnamese="Xác thực",
        category="Security",
        definition="Xác minh danh tính người dùng (bạn là ai?).",
        related=["authorization", "OAuth", "JWT"]
    ),
    "authorization": TermDefinition(
        term="Authorization",
        japanese="認可 (にんか)",
        vietnamese="Phân quyền",
        category="Security",
        definition="Xác định quyền truy cập của người dùng (bạn được làm gì?)."
    ),
    "encryption": TermDefinition(
        term="Encryption",
        japanese="暗号化 (あんごうか)",
        vietnamese="Mã hóa",
        category="Security",
        definition="Chuyển đổi dữ liệu thành dạng không đọc được nếu không có key.",
        related=["AES", "RSA", "SSL/TLS"]
    ),
    
    # === Git/VCS Terms ===
    "git": TermDefinition(
        term="Git",
        japanese="Git (ギット)",
        vietnamese="Git",
        category="VCS",
        definition="Hệ thống quản lý phiên bản phân tán phổ biến nhất thế giới.",
        related=["GitHub", "commit", "branch", "merge"]
    ),
    "commit": TermDefinition(
        term="Commit",
        japanese="コミット",
        vietnamese="Lưu thay đổi",
        category="VCS",
        definition="Lưu snapshot của các thay đổi vào repository.",
        example="git commit -m 'Add new feature'"
    ),
    "branch": TermDefinition(
        term="Branch",
        japanese="ブランチ / 枝",
        vietnamese="Nhánh",
        category="VCS",
        definition="Phiên bản độc lập của code, cho phép phát triển song song.",
        related=["merge", "checkout", "main"]
    ),
    "merge": TermDefinition(
        term="Merge",
        japanese="マージ",
        vietnamese="Hợp nhất",
        category="VCS",
        definition="Kết hợp thay đổi từ branch này sang branch khác.",
        related=["conflict", "pull request"]
    ),
    "pull request": TermDefinition(
        term="Pull Request",
        japanese="プルリクエスト / PR",
        vietnamese="Yêu cầu kéo",
        category="VCS",
        definition="Yêu cầu merge code và review từ team members.",
        example="Tạo PR để review code trước khi merge vào main."
    ),
    
    # === Agile/Scrum Terms ===
    "agile": TermDefinition(
        term="Agile",
        japanese="アジャイル",
        vietnamese="Phương pháp Agile",
        category="Methodology",
        definition="Phương pháp phát triển phần mềm linh hoạt, chia nhỏ thành sprint.",
        related=["Scrum", "Kanban", "sprint"]
    ),
    "sprint": TermDefinition(
        term="Sprint",
        japanese="スプリント",
        vietnamese="Giai đoạn phát triển",
        category="Methodology",
        definition="Khoảng thời gian ngắn (1-4 tuần) để hoàn thành một tập tính năng.",
        related=["backlog", "user story"]
    ),
    
    # === Cloud Terms ===
    "cloud": TermDefinition(
        term="Cloud Computing",
        japanese="クラウドコンピューティング",
        vietnamese="Điện toán đám mây",
        category="Cloud",
        definition="Cung cấp tài nguyên máy tính (server, storage) qua internet.",
        related=["AWS", "GCP", "Azure"]
    ),
    "serverless": TermDefinition(
        term="Serverless",
        japanese="サーバーレス",
        vietnamese="Không máy chủ",
        category="Cloud",
        definition="Mô hình cloud mà provider quản lý infrastructure, dev chỉ viết code.",
        example="AWS Lambda là dịch vụ serverless phổ biến."
    ),
    "aws": TermDefinition(
        term="AWS",
        japanese="AWS (アマゾンウェブサービス)",
        vietnamese="Amazon Web Services",
        category="Cloud",
        definition="Nền tảng cloud lớn nhất thế giới của Amazon.",
        related=["EC2", "S3", "Lambda"]
    ),
    
    # === Data Structure Terms ===
    "array": TermDefinition(
        term="Array",
        japanese="配列 (はいれつ)",
        vietnamese="Mảng",
        category="Data Structure",
        definition="Cấu trúc dữ liệu lưu trữ các phần tử liên tiếp trong bộ nhớ.",
        related=["list", "index", "loop"]
    ),
    "hash table": TermDefinition(
        term="Hash Table",
        japanese="ハッシュテーブル",
        vietnamese="Bảng băm",
        category="Data Structure",
        definition="Cấu trúc lưu trữ cặp key-value với tìm kiếm O(1).",
        example="Dictionary trong Python là hash table."
    ),
    "linked list": TermDefinition(
        term="Linked List",
        japanese="連結リスト (れんけつリスト)",
        vietnamese="Danh sách liên kết",
        category="Data Structure",
        definition="Cấu trúc mỗi phần tử chứa pointer đến phần tử tiếp theo.",
        related=["node", "pointer", "head"]
    ),
    "stack": TermDefinition(
        term="Stack",
        japanese="スタック",
        vietnamese="Ngăn xếp",
        category="Data Structure",
        definition="Cấu trúc LIFO - Last In First Out.",
        example="Call stack lưu trữ các hàm đang thực thi."
    ),
    "queue": TermDefinition(
        term="Queue",
        japanese="キュー",
        vietnamese="Hàng đợi",
        category="Data Structure",
        definition="Cấu trúc FIFO - First In First Out.",
        example="Message queue trong hệ thống phân tán."
    ),
    
    # === Testing Terms ===
    "unit test": TermDefinition(
        term="Unit Test",
        japanese="単体テスト (たんたいテスト)",
        vietnamese="Kiểm thử đơn vị",
        category="Testing",
        definition="Kiểm thử từng function/class riêng lẻ.",
        related=["integration test", "TDD", "mock"]
    ),
    "tdd": TermDefinition(
        term="TDD",
        japanese="TDD (テスト駆動開発)",
        vietnamese="Phát triển hướng kiểm thử",
        category="Testing",
        definition="Viết test trước, sau đó mới viết code để pass test.",
        example="Red-Green-Refactor cycle."
    ),
    
    # === OOP Terms ===
    "class": TermDefinition(
        term="Class",
        japanese="クラス",
        vietnamese="Lớp",
        category="OOP",
        definition="Bản thiết kế để tạo các object có chung thuộc tính và phương thức.",
        related=["object", "instance", "method"]
    ),
    "inheritance": TermDefinition(
        term="Inheritance",
        japanese="継承 (けいしょう)",
        vietnamese="Kế thừa",
        category="OOP",
        definition="Cho phép class con kế thừa thuộc tính và phương thức từ class cha.",
        related=["extends", "super", "override"]
    ),
    "polymorphism": TermDefinition(
        term="Polymorphism",
        japanese="ポリモーフィズム / 多態性",
        vietnamese="Đa hình",
        category="OOP",
        definition="Khả năng xử lý các object khác nhau thông qua cùng một interface.",
        related=["interface", "abstract class"]
    ),
}


class ITDictionary:
    """IT Dictionary service with fuzzy matching."""
    
    def __init__(self):
        self._dict = TECH_DICTIONARY
        self._build_search_index()
    
    def _build_search_index(self):
        """Build index for faster searching."""
        self._index = {}
        for key, term in self._dict.items():
            # Index by main term
            self._index[key.lower()] = term
            # Index by Japanese
            jp_clean = re.sub(r'[（）\s]', '', term.japanese.lower())
            self._index[jp_clean] = term
            # Index by Vietnamese
            self._index[term.vietnamese.lower()] = term
    
    def lookup(self, query: str) -> Optional[TermDefinition]:
        """Look up a term by exact or fuzzy match."""
        query = query.lower().strip()
        
        # Exact match
        if query in self._index:
            return self._index[query]
        
        # Partial match
        for key, term in self._index.items():
            if query in key or key in query:
                return term
        
        return None
    
    def search(self, query: str, limit: int = 5) -> List[TermDefinition]:
        """Search for terms matching query."""
        query = query.lower().strip()
        results = []
        
        for key, term in self._dict.items():
            score = 0
            
            # Check term
            if query in key:
                score += 10
            if query in term.vietnamese.lower():
                score += 8
            if query in term.japanese.lower():
                score += 8
            if query in term.definition.lower():
                score += 3
            if query in term.category.lower():
                score += 2
            
            if score > 0:
                results.append((score, term))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [term for _, term in results[:limit]]
    
    def get_by_category(self, category: str) -> List[TermDefinition]:
        """Get all terms in a category."""
        return [t for t in self._dict.values() if t.category.lower() == category.lower()]
    
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        return list(set(t.category for t in self._dict.values()))
    
    def format_result(self, term: TermDefinition) -> str:
        """Format term for display."""
        lines = [
            f"📘 **{term.term}**",
            f"🇯🇵 {term.japanese}",
            f"🇻🇳 {term.vietnamese}",
            f"",
            f"📂 *{term.category}*",
            f"",
            f"📝 {term.definition}",
        ]
        
        if term.example:
            lines.append(f"")
            lines.append(f"💡 Ví dụ: {term.example}")
        
        if term.related:
            lines.append(f"")
            lines.append(f"🔗 Liên quan: {', '.join(term.related)}")
        
        return "\n".join(lines)


# Global instance
_dictionary = None

def get_it_dictionary() -> ITDictionary:
    """Get singleton instance of IT Dictionary."""
    global _dictionary
    if _dictionary is None:
        _dictionary = ITDictionary()
    return _dictionary
