import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import openpyxl
from openpyxl.cell.cell import MergedCell

# A dictionary of Hán Việt readings for the Kanji characters found in the file.
# This is a comprehensive map based on common N1 Kanji.
HAN_VIET_MAP = {
    '一': 'Nhất', '亁E: 'NhềE, '丁E: 'Tam', '囁E: 'Tứ', '亁E: 'Ngũ', '六': 'Lục', '丁E: 'Thất', '八': 'Bát', '乁E: 'Cửu', '十E: 'Thập',
    '百': 'Bách', '十E: 'Thiên', '丁E: 'Vạn', '年': 'Niên', '朁E: 'Nguyệt', '日': 'Nhật', '晁E: 'Thời', '刁E: 'Phân', '私E: 'Miểu',
    '靁E: 'Thanh', '春': 'Xuân', '晩': 'Vãn', '最': 'Tối', '葬': 'Táng', '弁E: 'Thức', '丁E: 'Thế', '帯': 'Đới', '主': 'Chủ', '数': 'SềE,
    '人': 'Nhân', '家': 'Gia', '旁E: 'Tộc', '父': 'Phụ', '毁E: 'Mẫu', '允E: 'Huynh', '弁E: 'ĐềE, '姁E: 'Tỷ', '妹': 'Muội', '孁E: 'Tử',
    '身': 'Thân', '冁E: 'Nội', '夁E: 'Ngoại', '丁E: 'Thượng', '丁E: 'Hạ', '中': 'Trung', '左': 'Tả', '右': 'Hữu', '剁E: 'Tiền', '征E: 'Hậu',
    '甁E: 'Sinh', '死': 'Tử', '学': 'Học', '校': 'Hiệu', '允E: 'Tiên', '師': 'Sư', '叁E: 'Hữu', '強': 'Cường', '弱': 'Nhược', '髁E: 'Cao',
    '佁E: 'Đê', '大': 'Đại', '封E: 'Tiểu', '夁E: 'Đa', '封E: 'Thiểu', '長': 'Trường', '短': 'Đoản', '昁E: 'Minh', '暁E: 'Ám', '庁E: 'Quảng',
    '狭': 'Hiệp', '新': 'Tân', '古': 'CềE, '早': 'Tảo', '送E: 'Tốc', '遁E: 'Trì', '釁E: 'Trọng', '軽': 'Khinh', '甁E: 'Cam', '苦': 'KhềE,
    '辁E: 'Tân', '塩': 'Diêm', '酸': 'Toan', '油': 'Du', '水': 'Thủy', '火': 'Hỏa', '風': 'Phong', '圁E: 'ThềE, '釁E: 'Kim', '銀': 'Ngân',
    '鉁E: 'Thiết', '銁E: 'Đồng', '山': 'Sơn', '巁E: 'Xuyên', '极E: 'Lâm', '森': 'Sâm', '空': 'Không', '海': 'Hải', '天': 'Thiên', '地': 'Địa',
    '方': 'Phương', '国': 'Quốc', '都': 'Đô', '币E: 'ThềE, '町': 'Đinh', '杁E: 'Thôn', '遁E: 'Đạo', '路': 'LềE, '駁E: 'Dịch', '軁E: 'Xa',
    '自': 'Tự', '衁E: 'Hành', '来': 'Lai', '出': 'Xuất', '入': 'Nhập', '竁E: 'Lập', '座': 'Tọa', '歩': 'BềE, '走': 'Tẩu', '飁E: 'Phi',
    '要E: 'Kiến', '聁E: 'Văn', '言': 'Ngôn', '話': 'Thoại', '読': 'Độc', '書': 'Thư', '飁E: 'Thực', '飲': 'Ẩm', '買': 'Mãi', '売': 'Mại',
    '征E: 'Đãi', '持E: 'Trì', '使': 'Sử', '佁E: 'Tác', '吁E: 'Hợp', '知': 'Tri', '态E: 'Tư', '老E: 'Khảo', '決': 'Quyết', '宁E: 'Định',
    '政': 'Chính', '治': 'TrềE, '絁E: 'Kinh', '渁E: 'Tế', '況E: 'Pháp', '征E: 'Luật', '議': 'NghềE, '企E: 'Hội', '社': 'Xã', '団': 'Đoàn',
    '亁E: 'Sự', '業': 'Nghiệp', '勁E: 'Vụ', '用': 'Dụng', '橁E: 'Cơ', '関': 'Quan', '十E: 'Hiệp', '劁E: 'Lực', '制': 'Chế', '度': 'ĐềE,
    '愁E: 'ÁE, '想': 'Tưởng', '愁E: 'Cảm', '惁E: 'Tình', '愁E: 'Ái', '忁E: 'Tâm', '祁E: 'Thần', '琁E: 'Lý', '私E: 'Khoa', '斁E: 'Văn',
    '孁E: 'Tự', '誁E: 'Ngữ', '英': 'Anh', '咁E: 'Hòa', '佁E: 'ThềE, '顁E: 'Nhan', '頭': 'Đầu', '目': 'Mục', '耳': 'Nhĩ', '鼻': 'TềE,
    '口': 'Khẩu', '扁E: 'Thủ', '足': 'Túc', '持E: 'ChềE, '毁E: 'Mao', '血': 'Huyết', '肁E: 'Nhục', '骨': 'Cốt', '痁E: 'Bệnh', '院': 'Viện',
    '薬': 'Dược', '医': 'Y', '衁E: 'Thuật', '技': 'Kỹ', '員': 'Viên', '老E: 'Giả', '宁E: 'Quan', '代': 'Đại', '表': 'Biểu', '相': 'Tương',
    '筁E: 'Đẳng', '全': 'Toàn', '吁E: 'Các', '共': 'Cộng', '吁E: 'Đồng', '別': 'Biệt', '特': 'Đặc', '正': 'Chính', '省E: 'Chân', '確': 'Xác',
    '實': 'Thực', '宁E: 'Thực', '厁E: 'Nguyên', '匁E: 'Hóa', '琁E: 'Lý', '皁E: 'Đích', '性': 'Tính', '槁E: 'Cách', '質': 'Chất', '釁E: 'Lượng', '形': 'Hình',
    '慁E: 'Thái', '狀': 'Trạng', '状': 'Trạng', '現': 'Hiện', '象': 'Tượng', '畁E: 'Giới', '由': 'Do', '自': 'Tự', '然': 'Nhiên', '物': 'Vật', '髁E: 'ThềE,
    '品E: 'Phẩm', '杁E: 'Tài', '賁E: 'Tư', '產': 'Sản', '産': 'Sản', '溁E: 'Nguyên', '器': 'Khí', '具': 'Cụ', '設': 'Thiết', '傁E: 'BềE, '建': 'Kiến',
    '發': 'Phát', '発': 'Phát', '屁E: 'Triển', '進': 'Tiến', '退': 'Thoái', '閁E: 'Khai', '閁E: 'Bế', '勁E: 'Động', '靁E: 'Tĩnh', '靁E: 'Tĩnh', '止': 'ChềE, '送E: 'Thông',
    '連': 'Liên', '絡': 'Lạc', '送E: 'Tống', '叁E: 'Thụ', '叁E: 'Thủ', '舁E: 'Dữ', '丁E: 'Dữ', '酁E: 'Phối', '雁E: 'Tập', '散': 'Tán', '加': 'Gia',
    '渁E: 'Giảm', '墁E: 'Tăng', '墁E: 'Tăng', '夁E: 'Đa', '讁E: 'Biến', '夁E: 'Biến', '更': 'Canh', '改': 'Cải', '喁E: 'Thiện', '良': 'Lương', '惡': 'Ác', '悪': 'Ác', '険': 'Hiểm',
    '宁E: 'An', '危': 'Nguy', '樁E: 'Lạc', '楽': 'Lạc', '苦': 'KhềE, '喁E: 'HềE, '态E: 'NềE, '哀': 'Ai', '顁E: 'Nguyện', '汁E: 'Cầu',
    '朁E: 'Vọng', '币E: 'Hy', '滿': 'Mãn', '満': 'Mãn', '足': 'Túc', '丁E: 'Bất', '可': 'Khả', '能': 'Năng', '難': 'Nan', '昁E: 'Dịch',
    '勁E: 'Thắng', '負': 'Phụ', '爭': 'Tranh', '亁E: 'Tranh', '戰': 'Chiến', '戦': 'Chiến', '闁E: 'Đấu', '命': 'Mệnh', '遁E: 'Vận', '禁E: 'Phúc', '災': 'Tai', '害': 'Hại',
    '俁E: 'Bảo', '宁E: 'Thủ', '衁E: 'VềE, '査': 'Tra', '檢': 'Kiểm', '椁E: 'Kiểm', '譁E: 'Chứng', '証': 'Chứng', '誁E: 'Nhận', '信': 'Tín', '賴': 'Lại', '頼': 'Lại', '任': 'Nhiệm',
    '持E: 'ChềE, '封E: 'Đạo', '敁E: 'Giáo', '育': 'Dục', '翁E: 'Tập', '码E: 'Nghiên', '究': 'Cứu', '調': 'Điều', '訁E: 'Ký', '録': 'Lục',
    '報': 'Báo', '呁E: 'Cáo', '桁E: 'Án', '內': 'Nội', '解': 'Giải', '說': 'Thuyết', '説': 'Thuyết', '啁E: 'Vấn', '顁E: 'ĐềE, '筁E: 'Đáp', '桁E: 'Án',
    '訁E: 'Kế', '畫': 'Họa', '画': 'Họa', '亁E: 'Dự', '箁E: 'Toán', '決': 'Quyết', '箁E: 'Toán', '收': 'Thu', '叁E: 'Thu', '支': 'Chi', '征E: 'Đắc', '失': 'Thất',
    '盁E: 'Ích', '搁E: 'Tổn', '費': 'Phí', '用': 'Dụng', '價': 'Giá', '価': 'Giá', '格': 'Cách', '値': 'TrềE, '段': 'Đoạn', '品E: 'Phẩm', '啁E: 'Thương',
    '樁E: 'Tiêu', '溁E: 'Chuẩn', '要E: 'Quy', '剁E: 'Tắc', '基': 'Cơ', '篁E: 'Phạm', '圁E: 'Vi', '囲': 'Vi', '畁E: 'Giới', '陁E: 'Hạn', '制': 'Chế',
    # Adding more based on extracted Kanji
    '代': 'Đại', '表': 'Biểu', '相': 'Tương', '対': 'Đối', '諁E: 'Luận', '移': 'Di', '副': 'Phó', '避': 'Tỵ', '離': 'Ly', '敁E: 'Mẫn',
    '派': 'Phái', '码E: 'Toái', '統': 'Thống', '佁E: 'Dư', '緁E: 'Khẩn', '絁E: 'TềE, '異': 'DềE, '惁E: 'Tích', '直': 'Trực', '垁E: 'Hình',
    '允E: 'Nguyên', '虁E: 'Hư', '殺': 'Sát', '断': 'Đoạn', '釁E: 'Dã', '条': 'Điều', '俁E: 'Xúc', '飾': 'Sức', '訴': 'TềE, '訳': 'Dịch',
    '侵': 'Xâm', '辺': 'Biên', '独': 'Độc', '冷': 'Lãnh', '老E: 'Lão', '私E: 'Bí', '紁E: 'Văn', '邪': 'Tà', '痁E: 'Thống', '胁E: 'Bối',
    '綁E: 'Kế', '慣': 'Quán', '隁E: 'Đội', '裁E: 'Dụ', '縦': 'Tung', '乁E: 'Phạp', '僁E: 'Cận', '面': 'Diện', '創': 'Sáng', '棁E: 'Khí',
    '活': 'Hoạt', '允E: 'Khắc', '仁E: 'Giới', '捨': 'Xả', '娯': 'Giải', '繰': 'Sào', '劣': 'Liệt', '顁E: 'Hiển', '澁E: 'Trừng', '落': 'Lạc',
    '允E: 'Đảng', '交': 'Giao', '粁E: 'Niêm', '馁E: 'Hương', '痴': 'Si', '凁E: 'Điêu', '振': 'Chấn', '景': 'Cảnh', '譁E: 'Thức', '遁E: 'Quá',
    '送E: 'Giá', '容': 'Dung', '拠': 'Cứ', '墁E: 'Cảnh', '乁E: 'Thừa', '螁E: 'Dung', '衁E: 'Chúng', '突E: 'Song', '架': 'Giá', '偁E: 'Phiến',
    '趁E: 'Việt', '嫁E: 'Hiềm', '沿': 'Duyên', '浸': 'Tẩm', '帳': 'Trướng', '企E: 'Hội', '冁E: 'Viên', '筁E: 'Bút', '圁E: 'Viên', '突E: 'Đột',
    '穀': 'Cốc', '餁E: 'Dưỡng', '渁E: 'Thiệp', '幼': 'Ấu', '隁E: 'Cách', '雁E: 'CềE, '荁E: 'Trang', '役': 'Dịch', '萁E: 'Nuy', '趣': 'Thú',
    '是': 'ThềE, '遠': 'ViềE', '援': 'Viện', '照': 'Chiếu', '微': 'Vi', '氾': 'Phiếm', '撤': 'Triệt', '妁E: 'Như', '臁E: 'Ức', '滁E: 'TrềE,
    '呵': 'Ha', ' Doanh': 'Doanh', '持E: 'Cử', '壁E: 'Hoại', '激': 'Kích', '波': 'Ba', '次': 'Thứ', '否': 'Phủ', '暮': 'MềE, '念': 'Niệm',
    '膨': 'Bành', '朁E: 'Hữu', '巻': 'Quyển', '繁E: 'Phồn', '素': 'TềE, '廁E: 'Phế', '好': 'Hảo', '裁E: 'Trang', '羁E: 'Mỹ', '油': 'Du',
    '殁E: 'Tàn', '勁E: 'MềE, '無': 'Vô', '誤': 'NgềE, '馬': 'Mã', '席': 'Tịch', '晴': 'Tình', '忁E: 'Ứng', '訁E: 'Thảo', '絶': 'Tuyệt',
    '衡': 'Hành', '処': 'Xử', '細': 'Tế', '客': 'Khách', '接': 'Tiếp', '持E: 'Hiệp', '影': 'Ảnh', '臨': 'Lâm', '潤': 'Nhuận', '携': 'HuềE,
    '省E: 'Tỉnh', '流E: 'Thiển', '猁E: 'Mãnh', '板': 'Bản', '俁E: 'HềE, '支': 'Chi', '堁E: 'Kiên', '湯': 'Thang', '厁E: 'Ách', '埁E: 'Mai',
    '恥': 'SềE, '倁E: 'Bội', '優': 'Ưu', '据': 'Cứ', '綁E: 'Tục', '蝁E: 'Thực', '搁E: 'Tao', '誁E: 'Dụ', '乱': 'Loạn', '警': 'Cảnh',
    '仲': 'Trọng', '侁E: 'LềE, '旨': 'ChềE, '捁E: 'Sưu', '困': 'Khốn', '滁E: 'Hoạt', '莫': 'Mạc', '溁E: 'Câu', '華': 'Hoa', '几': 'KềE,
    '钁E: 'Độn', '并': 'Tịnh', '嘁E: 'Than', '貧': 'Bần', '佁E: 'VềE, '隠': 'Ẩn', '牁E: 'Phiến', '牁E: 'Bản', '宁E: 'Uyển', '推': 'Thôi',
    '整': 'Chỉnh', '肯': 'Khẳng', '懸': 'Huyền', '撫': 'Phủ', '极E: 'Quả', '屁E: 'Cư', '十E: 'Đơn', '寡': 'Quả', '慢': 'Mạn', '筁E: 'Sách',
    '孁E: 'Tồn', '酬': 'Thù', '平': 'Bình', '犠': 'Hy', '甁E: 'Thậm', '柁E: 'NhiềE', '濫': 'Lạm', '迁E: 'Nghênh', '釣': 'Điếu', '遁E: 'Đạt',
    '奁E: 'Tấu', '揁E: 'Dương', '戁E: 'Thành', '利': 'Lợi', '弁E: 'Dẫn', '篁E: 'Trúc', '揮': 'Huy', '宥': 'Hựu', '詰': 'Cật', '紁E: 'Ước',
    '最': 'Tối', '温': 'Ôn', '糸': 'Mịch', '良': 'Lương', '熁E: 'Thục', '垁E: 'Thùy', '関': 'Quan', '責': 'Trách', '短': 'Đoản', '己': 'Kỷ',
    '込': 'Nhập', '淡': 'Đạm', '倁E: 'Đảo', '着': 'Trước', '奮': 'Phấn', '駁E: 'Khu', '樹': 'Thụ', '隁E: 'Tế', '転': 'Chuyển', '昁E: 'Tích',
    '溺': 'Nịch', '老E: 'Nại', '送E: 'Tống', '煩': 'Phiền', '扶': 'Phù', '脱': 'Thoát', '種': 'Chủng', '宁E: 'Hoàn', '榁E: 'Khái', '没': 'Một',
    '賁E: 'Chẩn', '隁E: 'Chướng', '緩': 'Hoãn', '競': 'Cạnh', '息': 'Tức', '允E: 'Nhi', '冴': 'Ngà', '桁E: 'Hàng', '掴': 'Quặc', '穁E: 'Ổn',
    '靁E: 'Phi', '遁E: 'Toại', '止': 'ChềE, '陁E: 'Giáng', '寁E: 'Mật', '翻': 'Phiên', '擁E: 'Thao', '要E: 'Giác', '悲': 'Bi', '聴': 'Thính',
    '旁E: 'Kỳ', '惨': 'Thảm', '漁E: 'Phiêu', '執': 'Chấp', '謁E: 'Mê', '囁E: 'Chiếp', '焦': 'Tiêu', '旧': 'Cựu', '庁E: 'ĐềE, '登': 'Đăng',
    '掻': 'Tao', '諾': 'Nặc', '禁E: 'Cấm', '勁E: 'MiềE', '陽': 'Dương', '陥': 'Hãm', '驁E: 'Kinh', '倣': 'Phỏng', '儁E: 'Thường', '敢': 'Cảm',
    '仁E: 'Kim', '匁E: 'Bao', '亡': 'Vong', '跳': 'Khiêu', '財': 'Tài', '愁E: 'Ngu', '凁E: 'Ngưng', '欁E: 'Lan', '旦': 'Đán', '凭': 'Bằng',
    '稁E: 'Trĩ', '陰': 'Âm', '敁E: 'CềE, '賢': 'Hiền', '嵩': 'Tung', '弁E: 'Biện', '区': 'Khu', '奁E: 'Phụng', '仁E: 'Sĩ', '濁E: 'Nồng',
    '鋭': 'DuềE, '掲': 'Yết', '阵': 'Trận', '彁E: 'Đương', '妁E: 'Diệu', '怪': 'Quái', '姁E: 'Ủy', '注': 'Chú', '台': 'Đài', '旁E: 'Lữ',
    '汰': 'Thái', '焼': 'Thiêu', '冁E: 'Tả', '楯': 'Thuẫn', '抵': 'ĐềE, '精': 'Tinh', '要E: 'ThềE, '昁E: 'Tinh', '訪': 'Phóng', '詳': 'Tường',
    '胁E: 'Bào', '誠': 'Thành', '電': 'Điện', '酷': 'Khốc', '黁E: 'Mặc', '図': 'ĐềE, '賠': 'Bồi', '征E: 'Tùng', '企E: 'Xí', '循': 'Tuần',
    '紁E: 'Phân', '侮': 'Vũ', '般': 'Bát', '溢': 'Dật', '張': 'Trương', '捁E: 'Tróc', '致': 'Trí', '偽': 'Ngụy', '漠': 'Mạc', '痁E: 'Chứng',
    '室': 'Thất', '柁E: 'Bính', '抁E: 'Bả', '謁E: 'Tạ', '涁E: 'LềE, '夢': 'Mộng', '遣': 'Khiển', '佁E: 'Trú', '吁E: 'Hướng', '鮮': 'Tiên',
    '庶': 'Thứ', '十E: 'Ty', '逸': 'Dật', '庁E: 'Tý', '堪': 'Khám', '適': 'Thích', '脳': 'Não', '疁E: 'Nghi', '放': 'Phóng', '械': 'Giới',
    '獲': 'Hoạch', '剁E: 'Tước', '徳': 'Đức', '裁E: 'BềE, '渡': 'ĐềE, '硬': 'Ngạnh', '揁E: 'Hoán', '熱': 'Nhiệt', '雁E: 'Tạp', '涁E: 'Tiêu',
    '未': 'VềE, '義': 'Nghĩa', '衁E: 'Xung', '枯': 'Khô', '毁E: 'Độc', '暁E: 'Noãn', '兵': 'Binh', '催': 'Thôi', '捻': 'Niệm', '抁E: 'Kháng',
    '快': 'Khoái', '徴': 'Trưng', '改': 'Cải', '礼': 'LềE, '濡': 'Nhu', '揁E: 'Nhu', '亁E: 'LiềE', '諁E: 'Thỉnh', '倁E: 'Tá', '怠': 'Đãi',
    '宁E: 'Nghi', '強': 'Cường', '監': 'Giám', '敷': 'Phu', '労': 'Lao', '軁E: 'Hiên', '販': 'Phiến', '抁E: 'Bạt', '隁E: 'Giai', '忁E: 'Tất',
    '扱': 'Tráp', '勁E: 'Dũng', '置': 'Trí', '賁E: 'Thưởng', '斁E: 'Liệu', '眠': 'Miên', '濾': 'Lự', '騰': 'Đằng', '酵': 'Diếu', '亁E: 'HềE,
    '復': 'Phục', '士': 'Sĩ', '歯': 'XềE, '音': 'Âm', '寁E: 'Khoan', '貢': 'Cống', '励': 'LềE, '宁E: 'Bảo', '示': 'ThềE, '髪': 'Phát',
    '部': 'BềE, '添': 'Thiêm', '朁E: 'Kỳ', '勢': 'Thế', '浴': 'Dục', '瞭': 'Liệu', '囁E: 'Hồi', '況E: 'Pháp', '深': 'Thâm', '流E: 'Lưu',
    '似': 'Tự', '延': 'Diên', '極': 'Cực', '褁E: 'Bao', '衰': 'Suy', '屁E: 'Khuật', '拁E: 'Đảm', '旺': 'Vượng', '幾': 'Kỷ', '襲': 'Tập',
    '声': 'Thanh', '狁E: 'Cuồng', '承': 'Thừa', '忁E: 'Nhẫn', '去': 'Khứ', '扁E: 'Phiến', '舁E: 'Hưng', '刁E: 'San', '拁E: 'Thác', '送E: 'Nghịch',
    '穁E: 'Tích', '沢': 'Trạch', '豁E: 'Phong', '沸': 'Phí', '叁E: 'Cập', '錯': 'Thác', '僁E: 'Tượng', '泣': 'Khấp', '宣': 'Tuyên', '核': 'Hạch',
    '所': 'SềE, '護': 'HềE, '漫': 'Mạn', '欲': 'Dục', '喁E: 'Hoán', '犯': 'Phạm', '送E: 'Đào', '尽': 'Tận', '踁E: 'Đạp', '弾': 'Đạn',
    '庁E: 'Điếm', '層': 'Tằng', '撁E: 'Kích', '審': 'Thẩm', '寁E: 'Tẩm', '朴': 'Phác', '輸': 'Thâu', '番': 'Phiên', '坁E: 'Quân', '茁E: 'Mậu',
    '繁E: 'Thiện', '遁E: 'Vi', '却': 'Khước', '模': 'Mô', '杁E: 'Thúc', '墾': 'Khẩn', '潁E: 'Tiềm', '紁E: 'Cấp', '闁E: 'Ám', '揁E: 'Miêu',
    '若': 'Nhược', '給': 'Cấp', '遮': 'Già', '隁E: 'Khích', '槁E: 'Cấu', '蔽': 'Tế', '暁E: 'Hạ', '許': 'Hứa', '庁E: 'Tự', '鳴': 'Minh',
    '侁E: 'Y', '権': 'Quyền', '舁E: 'ThềE, '起': 'Khởi', '痁E: 'Bệnh', '発': 'Phát', '叁E: 'Phản', '軁E: 'NhuyềE', '冁E: 'Tái', '送E: 'Thấu',
    '至': 'Chí', '陶': 'Đào', '厁E: 'Hậu', '解': 'Giải', '慁E: 'Thận', '佁E: 'Đãn', '瀁E: 'Tần', '親': 'Thân', '歪': 'Oai', '頻': 'Tần',
    '企E: 'Truyền', '露': 'LềE, '俯': 'Phủ', '婁E: 'Hôn', '本': 'Bản', '蓁E: 'Súc', '絁E: 'Chung', '拁E: 'Chuyết', '緁E: 'Tự', '崁E: 'Nhai',
    '顧': 'CềE, '孫': 'Tôn', '稁E: 'Thuế', '脁E: 'Thúy', '健': 'Kiện', '諁E: 'Đàm', '寸': 'Thốn', '匹': 'Thất', '沁E: 'Sa', '観': 'Quan',
    '抱': 'Bão', '摁E: 'Nhiếp', '脁E: 'Hiếp', '敵': 'Địch', '魁E: 'MềE, '封E: 'Chuyên', '到': 'Đáo', '塁E: 'Khối', '欺': 'Khi', '雁E: 'Nhã',
    '銁E: 'Hàm', '凡': 'Phàm', '溶': 'Dung', '頁E: 'Lĩnh', '衷': 'Trung', '摁E: 'Trích', '迁E: 'Tấn', '遺': 'Di', '牲': 'Hy', '沁E: 'Trầm',
    '渦': 'Oa', '艶': 'DiềE', '扁E: 'Đả', '点': 'Điểm', '端': 'Đoan', '貫': 'Quán', '企E: 'Phục', '謀': 'Mưu', '捷': 'Tiệp', '擁E: 'Ủng',
    '寁E: 'Phú', '幁E: 'Phúc', '節': 'Tiết', '維': 'Duy', '持E: 'Khiêu', '革': 'Cách', '雁E: 'Hùng', '圧': 'Áp', '璧': 'Bích', '倁E: 'Hậu',
    '奨': 'Tưởng', '悁E: 'Hối', '幁E: 'Mạc', '戸': 'HềE, '暴': 'Bạo', '裁E: 'Lý', '叩': 'Khấu', '玁E: 'Suất', '懁E: 'Hoài', '要E: 'Phúc',
    '迫': 'Bách', '措': 'ThềE, '屁E: 'Ốc', '絁E: 'Kết', '屁E: 'Thuộc', '送E: 'ĐềE, '朁E: 'Phục', '揺': 'Dao', '迁E: 'Phản', '仁E: 'Tha',
    '遁E: 'NgềE, '姁E: 'Thủy', '老E: 'Canh', '妬': 'ĐềE, '怯': 'Khiếp', '占': 'Chiếm', '鬱': 'Uất', '拁E: 'Chiêu', '惰': 'Nọa', '滁E: 'Diệt',
    '根': 'Căn', '割': 'Cát', '阻': 'TrềE, '癁E: 'Liệu', '吁E: 'Danh', '帰': 'Quy', '悩': 'Não', '抁E: 'Ức', '赴': 'Phó', '枠': 'Khung',
    '貼': 'Thiếp', '別': 'Biệt', '擦': 'Sát', '便': 'Tiện', '妥': 'Thỏa', '忁E: 'Chí', '蚤': 'Tảo', '窮': 'Cùng', '封E: 'Tôn', '裁E: 'Tài',
    '呼': 'Hô', '企E: 'Hưu', '羨': 'Tiện', '緻': 'Trí', '抁E: 'Đầu', '司': 'Ty', '秩': 'Trật', '員': 'Viên', '忁E: 'Vong', '申': 'Thân',
    '緁E: 'Tuyến', '顁E: 'Ngạch', '寁E: 'Sát', '助': 'Trợ', '吁E: 'ThềE, '渁E: 'Sáp', '栁E: 'Vinh', '僁E: 'Động', '哀': 'Ai', '儁E: 'Mộng',
    '寁E: 'Kí', '凁E: 'Đông', '括': 'Quát', '弁E: 'ThềE, '喁E: 'HềE, '勁E: 'Khám', '試': 'Thí', '仁E: 'Phó', '薁E: 'Bạc', '康': 'Khang',
    '椁E: 'Kiểm', '縮': 'Súc', '群': 'Quần', '抁E: 'Chiết', '況E: 'Huống', '件': 'Kiện', '叁E: 'Thu', '氁E: 'Dân', '躁E: 'Dược', '追': 'Truy',
    '丁E: 'Trượng', '巧': 'Xảo', '粁E: 'Túc', '賭': 'ĐềE, '公': 'Công', '餁E: 'Bính', '封E: 'Xạ', '跨': 'Khóa', '緯': 'Vĩ', '惁E: 'Hoặc',
    '胁E: 'Đảm', '勤': 'Cần', '凶': 'Hung', '色': 'Sắc', '傷': 'Thương', '朁E: 'Lãng', '索': 'Sách', '干': 'Can', '磨': 'Ma', '葁E: 'Diệp',
    '覧': 'Lãm', '遥': 'Dao', '剤': 'TềE, '憤': 'Phẫn', '裁E: 'Liệt', '喧': 'Huyên', '奁E: 'Khiết', '恁E: 'Hằng', '极E: 'Tích', '除': 'Trừ',
    '洁E: 'Dương', '触': 'Xúc', '締': 'Đế', '茶': 'Trà', '施': 'Thi', '掁E: 'Quái', '急': 'Cấp', '探': 'Thám', '奁E: 'Kỳ', '局': 'Cục',
    '祁E: 'Chúc', '柁E: 'Nhu', '潮': 'Triều', '刁E: 'Thiết', '隁E: 'Ngung', '縁E: 'Phược', '映': 'Ánh', '跡': 'Tích', '渁E: 'Khát', '允E: 'MiềE',
    '況E: 'Bạc', '迷': 'Mê', '謁E: 'Giảng', '捁E: 'BềE, '捁E: 'BềE, '馴': 'Tuần', '厳': 'Nghiêm', '武': 'Võ', '父': 'Phụ', '難': 'Nan',
    '献': 'Hiến', '欠': 'Khiếm', '品E: 'Phẩm', '闁E: 'Đấu', '押': 'Áp', '握': 'Ác', '允E: 'Quang', '造': 'Tạo', '頁E: 'Ngoan', '診': 'Chẩn',
    '妨': 'Phương', '職': 'Chức', '拁E: 'Cự', '悁E: 'NgềE, '憁E: 'Ưu', '戁E: 'Giới', '替': 'Thế', '戻': 'LềE, '慮': 'Lự', '頁E: 'Thuận',
    '曲': 'Khúc', '木': 'Mộc', '夁E: 'Dạ', '常': 'Thường', '採': 'Thải', '簡': 'Giản', '屁E: 'Tý', '邁E: 'Hoàn', '罠': 'Mân', '固': 'CềE,
    '罰': 'Phạt', '允E: 'Sung', '周': 'Chu', '狁E: 'Thư', '破': 'Phá', '紁E: 'Thuần', '誁E: 'Khoa', '控': 'Khống', '遭': 'Tao', '讁E: 'Nhượng',
    '譲': 'Nhượng', '拡': 'Khuếch', '汁E: 'ÁE, '葁E: 'Trứ', '盁E: 'Thịnh'
}

def get_han_viet(text):
    if not isinstance(text, str):
        return ""
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        # Skip Hiragana/Katakana for Han Viet lookup
        if '\u4e00' <= char <= '\u9faf':
             result.append(HAN_VIET_MAP.get(char, char))
        i += 1
    return " ".join(result)

file_path = r"C:\Users\Admin\Downloads\[Tailieutiengnhat.net]_tu-vung-tieng-nhat-n1-day-du.xlsx"
sheet_name = "パターン語彙N1"

print(f"Opening workbook sheet: {sheet_name}...")
wb = openpyxl.load_workbook(file_path)
ws = wb[sheet_name]

print("Updating Hán Việt column (Col 4)...")
count = 0
skip_count = 0
for row in ws.iter_rows(min_row=2):
    vocab_cell = row[1]  # Col B
    han_viet_cell = row[3] # Col D
    
    if isinstance(han_viet_cell, MergedCell):
        continue

    vocab = vocab_cell.value
    current_han_viet = han_viet_cell.value
    
    if vocab and isinstance(vocab, str):
        new_han_viet = get_han_viet(vocab)
        if new_han_viet:
            # Only update if empty or different
            if not current_han_viet or current_han_viet.strip() == "":
                han_viet_cell.value = new_han_viet
                count += 1
            else:
                skip_count += 1

print(f"Updated {count} rows. Skipped {skip_count} already filled rows.")
wb.save(file_path)
print("Finished.")

