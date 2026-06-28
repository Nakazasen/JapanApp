import json
import os
from urllib.parse import quote

def update_kana_json(filename, type_name):
    """
    Script để cập nhật dữ liệu bảng chữ cái Hiragana/Katakana.
    Bao gồm: Mẹo nhớ (Mnemonics) đầy đủ và link ảnh động cách viết.
    """
    path = os.path.join('frontend', 'data', 'content', 'intro', filename)
    if not os.path.exists(path):
        print(f'Lỗi: Không tìm thấy file {path}')
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # --- BỘ MẸO NHỚ HIRAGANA (Đầy đủ) ---
    mnemonics_h = {
        # Seion
        'あ': 'Chữ A với cái An-ten trên đầu.', 
        'い': 'Hai nét song song như hai số 1 (i).', 
        'う': 'Uốn éo như người đang tập cơ bụng.',
        'え': 'Con Êch đang nhảy qua rào.', 
        'お': 'Ông cụ đang ngồi câu cá bên hồ.',
        'か': 'Vung tay múa võ Ka-ra-te.', 
        'き': 'Cái chìa khóa (Key) để mở cửa.', 
        'く': 'Cái mỏ chim Cúc-ku đang mở.',
        'け': 'Thùng gỗ đựng rượu Sa-ke.', 
        'こ': 'Hai cái rổ (Ko) úp vào nhau.',
        'さ': 'Quai của cái túi xách (Sack).', 
        'し': 'Cái móc câu cá (Shinh).', 
        'す': 'Gương mặt đang cười (Smile) hạnh phúc.',
        'せ': 'Dòng sông Sen chảy hiền hòa.', 
        'そ': 'Con Sóc đang leo trên cành cây.',
        'た': 'Chữ T và chữ A ghép lại thành Ta.', 
        'chi': 'Số 5 bị viết ngược hoặc người Chị gái.', 'ち': 'Số 5 bị viết ngược hoặc người Chị gái.',
        'つ': 'Ngọn sóng thần (Tsu-na-mi) đang dâng cao.',
        'て': 'Cái Tai (Te) để lắng nghe.', 
        'と': 'Ngón chân (Toe) bị vấp vào cạnh bàn.',
        'な': 'Người đang Quỳ (Nan) xin lỗi.', 
        'に': 'Hai (Ni) nét gạch ngang.', 
        'ぬ': 'Sợi mì Nu-dle xoắn vào nhau.',
        'ね': 'Con Mèo (Neko) đang cuộn tròn đuôi.', 
        'の': 'Biển báo cấm (No) hình tròn.',
        'は': 'Cái thang (Ha-tta) dựng cạnh tường.', 
        'ひ': 'Cái Miệng đang cười tươi (Hi-hi).', 
        'ふ': 'Ngọn núi Phú (Fu) Sĩ hùng vĩ.',
        'へ': 'Đỉnh núi cao (Hay) chót vót.', 
        'ほ': 'Người cầm gậy đang đứng Ho.',
        'ま': 'Gương mặt con Ma (Ma) đáng sợ.', 
        'み': 'Số 21 (Mi) viết cách điệu.', 
        'む': 'Con bò kêu Moo Moo (Mu).',
        'め': 'Con Mắt (Me) có tròng tròn.', 
        'も': 'Lưỡi câu (Mo) móc dưới nước.',
        'や': 'Con thuyền Yak (Ya) trên sông.', 
        'ゆ': 'Con cá (Yu) đang tung tăng bơi.', 
        'よ': 'Người đang ngồi tập Yoga (Yo).',
        'ら': 'Con thỏ (Ra-bbit) có đôi tai dài.', 
        'り': 'Cánh hoa (Ri) rơi nhẹ nhàng.', 
        'る': 'Con đường (Route) có vòng xoay.',
        'れ': 'Người đang chạy (Re) rất nhanh.', 
        'ろ': 'Số 3 (Ro) nhưng không có vòng xoáy.',
        'わ': 'Con thiên nga (Wa) duyên dáng.', 
        'を': 'Người nhảy qua (Wo) vũng nước.', 
        'ん': 'Chữ n (N) viết thảo.',

        # Dakuon (Mẹo: Giống chữ cái gốc nhưng âm phát ra nặng hơn)
        'が': 'Múa Karate mạnh mẽ (Ga).', 'ぎ': 'Chìa khóa bạc (Gi).', 'ぐ': 'Mỏ chim lớn (Gu).', 'げ': 'Thùng rượu to (Ge).', 'ご': 'Lõi táo to (Go).',
        'ざ': 'Túi xách nặng (Za).', 'じ': 'Móc câu lớn (Ji).', 'ず': 'Cười lớn (Zu).', 'ぜ': 'Sông Sen rộng (Ze).', 'ぞ': 'Sóc lớn (Zo).',
        'だ': 'Ta biến thành Da nặng nề.', 'ぢ': 'Chị (Chi) biến âm thành Di.', 'づ': 'Sóng lớn Dzu.', 'で': 'Cái tai to (De).', 'ど': 'Ngón chân đau (Do).',
        'ば': 'Cái thang gỗ (Ba).', 'び': 'Cười hi hi (Bi).', 'ぶ': 'Núi Phú Sĩ mờ (Bu).', 'べ': 'Đỉnh núi dốc (Be).', 'ぼ': 'Ông già ho (Bo).',
        'ぱ': 'Cái thang nổ (Pa).', 'ぴ': 'Cười giòn tan (Pi).', 'ぷ': 'Phun bong bóng (Pu).', 'ぺ': 'Đỉnh núi phẳng (Pe).', 'ぽ': 'Ông già thổi sáo (Po).'
    }

    # --- BỘ MẸO NHỚ KATAKANA (Đầy đủ) ---
    mnemonics_k = {
        'ア': 'Cái Áo choàng của siêu nhân.', 
        'イ': 'Người đang đứng thẳng (I).', 
        'ウ': 'Cái U trên đầu Ang-ten.', 
        'エ': 'Cái kệ (E) sách gọn gàng.', 
        'オ': 'Người đang chạy bộ (O).',
        'カ': 'Vung kiếm Karate (Ka) mạnh mẽ.', 
        'キ': 'Cái chìa khóa (Ki) bằng sắt.', 
        'ク': 'Cái mũ (Ku) lưỡi trai.', 
        'ケ': 'Kẻ một đường ngang qua (Ke).', 
        'コ': 'Cái góc (Ko) vuông của bàn.',
        'サ': 'Cái sào (Sa) dùng để phơi đồ.', 
        'シ': 'Nụ cười (Shi) với đôi mắt híp.', 
        'ス': 'Người trượt tuyết (Su) đổ đèo.', 
        'セ': 'Dòng xe (Se) cộ đông đúc.', 
        'ソ': 'Kim châm (So) nhọn hoắt.',
        'タ': 'Số 7 (Ta) viết hơi nghiêng.', 
        'チ': 'Con chim (Chi) đang đậu trên cành.', 
        'ツ': 'Ba giọt nước (Tsu) bắn tung tóe.', 
        'テ': 'Cái Ang-ten (Te) thu sóng.', 
        'ト': 'Cái cột Totem (To) linh thiêng.',
        'ナ': 'Cái nơ (Na) xinh xắn.', 
        'ニ': 'Hai (Ni) nét nằm ngang.', 
        'ヌ': 'Đôi đũa (Nu) dùng để ăn mì.', 
        'ネ': 'Cái nệm (Ne) êm ái để ngủ.', 
        'ノ': 'Dấu gạch chéo (No) ngăn cấm.',
        'ハ': 'Hai nét (Ha) đối xứng nhau.', 
        'ヒ': 'Cái gót chân (Heel - Hi).', 
        'フ': 'Lá cờ (Flag - Fu) bay trong gió.', 
        'ヘ': 'Đỉnh núi (He) hình tam giác.', 
        'ホ': 'Cây thánh giá (Holy - Ho).',
        'マ': 'Mã (Ma) - Cái đầu ngựa.', 
        'ミ': 'Ba miếng mì (Mi) song song.', 
        'ム': 'Cái mu (Mu) của rùa.', 
        'メ': 'Cây gươm (Me) chém chéo.', 
        'モ': 'Lưỡi câu (Mo) móc ngược.',
        'ヤ': 'Con thuyền (Ya) nhỏ trên biển.', 
        'ユ': 'Trái tim yêu (Yu) nồng cháy.', 
        'ヨ': 'Người tập Yoga (Yo) uốn dẻo.',
        'ラ': 'Cái rá (Ra) để vo gạo.', 
        'リ': 'Hai nét (Ri) thanh mảnh.', 
        'ル': 'Cái rễ (Ru) cây đâm xuống đất.', 
        'レ': 'Tiếng reo hò (Re) sướng vui.', 
        'ロ': 'Cái hộp (Ro) hình vuông.',
        'ワ': 'Tiếng khóc Oa (Wa) của em bé.', 
        'ヲ': 'Chữ O (Wo) viết cách điệu.', 
        'ン': 'Chữ n (N) trong Katakana.',
        
        # Dakuon (Katakanas)
        'ガ': 'Karate mạnh (Ga).', 'ギ': 'Khóa sắt (Gi).', 'グ': 'Mũ to (Gu).', 'ゲ': 'Kẻ mạnh (Ge).', 'ゴ': 'Góc lớn (Go).',
        'ザ': 'Sào sắt (Za).', 'ジ': 'Nụ cười lớn (Ji).', 'ズ': 'Trượt nhanh (Zu).', 'ぜ': 'Xe to (Ze).', 'ぞ': 'Kim nhọn (Zo).',
        'ダ': 'Số 7 nặng (Da).', 'ぢ': 'Chim kêu (Di).', 'づ': 'Giọt nước lớn (Dzu).', 'で': 'Angten mạnh (De).', 'ど': 'Cột cao (Do).',
        'バ': 'Hai gậy (Ba).', 'ビ': 'Gót chân đau (Bi).', 'ブ': 'Lá cờ lớn (Bu).', 'ベ': 'Núi dốc (Be).', 'ボ': 'Thánh giá sáng (Bo).',
        'パ': 'Hai nét nổ (Pa).', 'ピ': 'Gót chân nảy (Pi).', 'プ': 'Cờ nổ (Pu).', 'ペ': 'Núi phẳng (Pe).', 'ポ': 'Thánh giá vàng (Po).'
    }

    mnemonics = mnemonics_h if type_name == 'Hiragana' else mnemonics_k

    def transform(item):
        if not item: return {'char': '', 'romaji': '', 'mnemonic': '', 'gif': ''}
        
        if isinstance(item, list):
            if len(item) < 2: return {'char': '', 'romaji': '', 'mnemonic': '', 'gif': ''}
            char, romaji = item
        elif isinstance(item, dict):
            char = item.get('char', '')
            romaji = item.get('romaji', '')
        else:
            return {'char': '', 'romaji': '', 'mnemonic': '', 'gif': ''}
            
        if not char: return {'char': '', 'romaji': '', 'mnemonic': '', 'gif': ''}
        
        # Lấy mẹo nhớ, nếu là âm ghép (Yoon) thì ghép mẹo của các chữ thành phần
        if len(char) > 1:
            m_parts = [mnemonics.get(c, c) for c in char]
            m = "Kết hợp của: " + " và ".join(m_parts)
        else:
            m = mnemonics.get(char, f'Mẹo nhớ cho {char}.')
        
        # Nguồn ảnh GIF từ GitHub jcsirot/kanji.gif
        base_type = type_name.lower()
        gif_url = f'https://raw.githubusercontent.com/jcsirot/kanji.gif/master/{base_type}/gif/150x150/{quote(char)}.gif'
        
        return {'char': char, 'romaji': romaji, 'mnemonic': m, 'gif': gif_url}

    new_data = {
        'seion': [transform(item) for item in data['seion']],
        'dakuon': [transform(item) for item in data.get('dakuon', [])],
        'yoon': [transform(item) for item in data.get('yoon', [])]
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    print(f'Đã cập nhật xong bộ mẹo nhớ cho: {filename}')

if __name__ == "__main__":
    update_kana_json('hiragana.json', 'Hiragana')
    update_kana_json('katakana.json', 'Katakana')
