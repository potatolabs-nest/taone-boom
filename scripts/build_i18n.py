#!/usr/bin/env python3
"""Build the i18n table for the client, then wire it in.

The client's labels are the real strings extracted from the game, so Korean is
kept as an authentic option. English is the default and Vietnamese is provided.

Writes app/public/i18n.json (the table) and patches client.html to use it.

Usage: python3 -I build_i18n.py [--apply]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(ROOT, "app/public/client.html")
OUT = os.path.join(ROOT, "app/public/i18n.json")

# key: [english, vietnamese]   (Korean stays as the key, so the original is never lost)
T = {
 # --- shell / nav ---
 "로비": ["Lobby", "Sảnh chờ"],
 "내정보": ["Profile", "Thông tin"],
 "내아이템": ["My Items", "Vật phẩm"],
 "상점": ["Shop", "Cửa hàng"],
 "마이페이지": ["My Page", "Trang của tôi"],
 "옵션": ["Options", "Tùy chọn"],
 "에셋 브라우저": ["Asset browser", "Trình duyệt tài nguyên"],
 "나가기": ["Exit", "Thoát"],
 "연결됨": ["Connected", "Đã kết nối"],

 # --- login ---
 "로그인": ["Sign in", "Đăng nhập"],
 "원본 클라이언트에서 추출한 UI와 문자열로 구성한 웹 클라이언트입니다.": [
   "A web client built from UI and strings extracted from the original client.",
   "Ứng dụng web dựng từ giao diện và chuỗi ký tự trích xuất từ client gốc."],
 "닉네임": ["Nickname", "Biệt danh"],
 "이름": ["Name", "Tên"],
 "채널": ["Channel", "Kênh"],
 "접속": ["Connect", "Kết nối"],
 "이 게임은": ["This game has", "Trò chơi này"],
 "서버가 없습니다": ["no server", "không có máy chủ"],
 "원본은 서버 권한형 온라인 게임이며 서버가\n        아카이브에 포함되어 있지 않습니다. 따라서 로비·방·플레이는 모두 로컬에서\n        동작하고, 곡과 UI는 추출한 실제 에셋을 사용합니다.": [
   "The original is a server-authoritative online game and its server is not in the archive. "
   "So the lobby, rooms and play all run locally, while songs and UI use the real extracted assets.",
   "Bản gốc là game online do máy chủ quyết định và máy chủ không có trong kho lưu trữ. "
   "Nên sảnh, phòng và phần chơi đều chạy cục bộ, còn bài hát và giao diện dùng tài nguyên thật đã trích xuất."],
 "이름을 입력하세요.": ["Enter a name.", "Hãy nhập tên."],
 "곡": ["song", "bài"],
 "개 준비됨": ["ready", "sẵn sàng"],

 # --- lobby ---
 "안녕하세요": ["Hello", "Xin chào"],
 "님": ["", ""],
 "채널을 선택하고 게임을 시작하세요.": ["Pick a channel and start a game.", "Chọn kênh và bắt đầu chơi."],
 "게임 모드": ["Game modes", "Chế độ chơi"],
 "채널 선택": ["Channels", "Kênh"],
 "곡 목록": ["Songs", "Bài hát"],
 "초보 채널": ["Beginner", "Kênh mới"],
 "자유 채널": ["Free", "Kênh tự do"],
 "고수 채널": ["Expert", "Kênh cao thủ"],
 "이벤트 채널": ["Event", "Kênh sự kiện"],
 "일반": ["Normal", "Thường"],
 "대결": ["Battle", "Đối kháng"],
 "몬스터": ["Monster", "Quái vật"],
 "빠른시작": ["Quick start", "Bắt đầu nhanh"],
 "래더": ["Ladder", "Xếp hạng"],
 "연습": ["Practice", "Luyện tập"],
 "방향 노트": ["4-direction notes", "Nốt 4 hướng"],
 "승부": ["Head to head", "Đối đầu"],
 "보스 스테이지": ["Boss stage", "Màn trùm"],
 "바로 입장": ["Jump straight in", "Vào ngay"],
 "랭크전": ["Ranked", "Đấu xếp hạng"],
 "자유 연습": ["Free practice", "Luyện tự do"],

 # --- matching / room list ---
 "방 목록": ["Room list", "Danh sách phòng"],
 "방": ["Rooms", "Phòng"],
 "전체방": ["All rooms", "Tất cả phòng"],
 "방만들기": ["Create room", "Tạo phòng"],
 "빠른 시작": ["Quick start", "Bắt đầu nhanh"],
 "내 정보": ["My info", "Thông tin"],
 "갱신": ["refreshed", "đã làm mới"],
 "개 방": ["rooms", "phòng"],
 "비밀번호가 걸린 방입니다": ["That room is locked.", "Phòng này có mật khẩu."],
 "방이 가득 찼습니다": ["That room is full.", "Phòng đã đầy."],
 "방을 찾는 중…": ["Looking for a room…", "Đang tìm phòng…"],
 "빈 방이 없습니다": ["No open rooms.", "Không có phòng trống."],
 "즐거운 방": ["Happy room", "Phòng vui vẻ"],
 "노래방": ["Karaoke", "Karaoke"],
 "초보 환영": ["Beginners welcome", "Chào mừng người mới"],
 "고수만": ["Experts only", "Chỉ cao thủ"],
 "자유": ["Free", "Tự do"],
 "커플": ["Couple", "Cặp đôi"],
 "연습방": ["Practice", "Phòng luyện"],
 "대결!": ["Battle!", "Đối kháng!"],

 # --- room ---
 "대기방": ["Waiting room", "Phòng chờ"],
 "준비": ["Ready", "Sẵn sàng"],
 "준비 취소": ["Cancel ready", "Hủy sẵn sàng"],
 "준비 완료": ["Ready", "Đã sẵn sàng"],
 "시작": ["Start", "Bắt đầu"],
 "음악": ["Music", "Nhạc"],
 "검색": ["Search", "Tìm"],
 "미리듣기": ["Preview", "Nghe thử"],
 "정지": ["Stop", "Dừng"],
 "곡을 선택하세요": ["Pick a song", "Chọn một bài"],
 "선택됨": ["selected", "đã chọn"],
 "스테이지": ["Stage", "Màn"],
 "난이도": ["Difficulty", "Độ khó"],
 "쉬움": ["Easy", "Dễ"],
 "보통": ["Normal", "Thường"],
 "어려움": ["Hard", "Khó"],
 "댄서A": ["DancerA", "DancerA"],
 "댄서B": ["DancerB", "DancerB"],
 "나)": ["you)", "bạn)"],
 "레벨": ["Lv", "Cấp"],
 "모든 플레이어가 준비 상태이어야 합니다.": ["Everyone must be ready.", "Mọi người phải sẵn sàng."],
 "방을 만들 수 없습니다. 잠시 후 다시 시도하세요.": ["Could not create the room. Try again shortly.", "Không tạo được phòng. Thử lại sau."],

 # --- play ---
 "일시정지": ["Pause", "Tạm dừng"],
 "재개": ["Resume", "Tiếp tục"],
 "일시정지됨": ["Paused", "Đã tạm dừng"],
 "재개됨": ["Resumed", "Đã tiếp tục"],
 "로딩…": ["Loading…", "Đang tải…"],
 "잘못된 경로": ["Bad path", "Đường dẫn sai"],
 "개 (오디오에서 검출)": ["notes, detected from the audio", "nốt, nhận từ âm thanh"],
 "개 (고정 그리드)": ["notes, fixed grid", "nốt, lưới cố định"],
 "노트": ["notes", "nốt"],
 "재생 실패": ["Playback failed", "Phát thất bại"],
 "이 브라우저가 Ogg Vorbis를 지원하지 않을 수 있습니다.": [
   "This browser may not support Ogg Vorbis.", "Trình duyệt này có thể không hỗ trợ Ogg Vorbis."],
 "점수": ["Score", "Điểm"],
 "콤보": ["Combo", "Chuỗi"],

 # --- result ---
 "다시하기": ["Play again", "Chơi lại"],
 "대기방으로": ["Back to room", "Về phòng chờ"],
 "정확도": ["accuracy", "độ chính xác"],
 "실패": ["failed", "thất bại"],
 "최고 콤보": ["MAX COMBO", "CHUỖI MAX"],

 # --- content tabs ---
 "프로필": ["Profile", "Hồ sơ"],
 "보유 곡": ["Songs owned", "Bài hát có"],
 "스프라이트": ["Sprites", "Hình"],
 "추출된 스프라이트가 없습니다.": ["No extracted sprites.", "Không có hình nào."],
 "이벤트 이미지": ["Event art", "Ảnh sự kiện"],
 "에셋 카탈로그": ["Asset catalog", "Danh mục tài nguyên"],
 "아이템": ["Items", "Vật phẩm"],
 "로컬 통계": ["Local stats", "Thống kê cục bộ"],
 "볼륨": ["Volume", "Âm lượng"],
 "마이페이지는 서버가 필요한 화면입니다. 원본 서버가 아카이브에 없으므로 로컬 데이터만 표시합니다.": [
   "My Page needs a server. The original server is not in the archive, so only local data is shown.",
   "Trang của tôi cần máy chủ. Máy chủ gốc không có trong kho lưu trữ nên chỉ hiển thị dữ liệu cục bộ."],
 "해상도, 사운드, 키 설정은 원본 클라이언트의 옵션입니다. 웹에서는 오디오 볼륨과 난이도만 제공합니다.": [
   "Resolution, sound and key bindings were options in the original client. The web version offers volume and difficulty only.",
   "Độ phân giải, âm thanh và phím là tùy chọn của client gốc. Bản web chỉ có âm lượng và độ khó."],
 "인덱스에서 복호화한 실제 에셋 이름": ["Real asset names decrypted from the index", "Tên tài nguyên thật đã giải mã"],
 "개 (무손실 검증": ["entries (lossless verify", "mục (kiểm chứng không mất dữ liệu"],
 "왕복 일치": ["round trip matches", "khớp vòng lặp"],
 "팝업": ["Popup", "Popup"],
 "퀘스트 번들에서 실제 이름으로 복구한 이미지": ["images recovered by real name from the quest bundles", "ảnh phục hồi theo tên thật"],
 "개 (검증됨": ["entries (verified", "mục (đã kiểm"],
 "세그먼트 체인이 EOI에서 정확히 끝남)": ["segment chains ending exactly at EOI)", "chuỗi segment kết thúc đúng tại EOI)"],
 "이미지를 찾지 못했습니다.": ["No images found.", "Không tìm thấy ảnh."],
 "이름 검색 (예": ["Search names (e.g.", "Tìm tên (vd"],
 "이전": ["‹ Prev", "‹ Trước"],
 "다음": ["Next ›", "Sau ›"],
 "(이전)": ["(prev)", "(trước)"],

 # --- errors / misc ---
 "로그인 서버 접속에 실패했습니다. (%d) DEF1": ["Could not reach the login server.", "Không kết nối được máy chủ đăng nhập."],
 "채널 접속이 끊어졌습니다.": ["The channel connection dropped.", "Kết nối kênh đã ngắt."],
 "뒤로가기": ["Back", "Quay lại"],
 "도움말": ["Help", "Trợ giúp"],
 "유저장터": ["Market", "Chợ"],
 "퀘스트": ["Quest", "Nhiệm vụ"],
 "메신저": ["Messenger", "Tin nhắn"],
 "로비 가기": ["Go to lobby", "Về sảnh"],
 "개 · 스프라이트": ["· sprites", "· hình"],
 "개 · 문자열": ["· strings", "· chuỗi"],
 "곡 ·": ["songs ·", "bài ·"],
 "에셋을 찾지 못했습니다": ["No assets found", "Không tìm thấy tài nguyên"],
 "이벤트 이미지 게시판": ["Event art board", "Bảng ảnh sự kiện"],
}


# --- keys discovered after the first pass ---
T.update({
 "닉네임": ["Nickname", "Biệt danh"],
 "난이도": ["Difficulty", "Độ khó"],
 "4방향 노트": ["4-direction notes", "Nốt 4 hướng"],
 "곡을 선택하세요": ["Pick a song", "Chọn một bài"],
 "이름": ["Name", "Tên"],
 "노트": ["notes", "nốt"],
 "스프라이트": ["sprites", "hình"],
 "채널": ["Channel", "Kênh"],
 "준비": ["Ready", "Sẵn sàng"],
 "방": ["Rooms", "Phòng"],
 "곡": ["songs", "bài"],
 "개": ["", ""],
 "님": ["", ""],
 "서버": ["server", "máy chủ"],
})


def main():
    json.dump(T, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"i18n table: {len(T)} keys -> {OUT}")
    print(f"  english + vietnamese, keyed by the original Korean so it is never lost")
    if "--apply" not in sys.argv:
        print("\n(re-run with --apply to patch client.html)")
        return

    h = open(CLIENT).read()
    # inject the table + helpers just after "use strict";
    if "window.__I18N__" in h:
        print("already patched")
        return
    inject = "\n".join([
        'window.__I18N__ = ' + json.dumps(T, ensure_ascii=False) + ';',
        'var LANG = (function(){ try { return localStorage.getItem("lang") || "en"; }'
        ' catch(e){ return "en"; } })();',
        'function t(s){',
        '  if (LANG === "ko") return s;',
        '  var e = window.__I18N__[s];',
        '  if (!e) return s;',
        '  return LANG === "vi" ? e[1] : e[0];',
        '}',
        'function setLang(l){',
        '  LANG = l;',
        '  try { localStorage.setItem("lang", l); } catch(e){}',
        '  document.documentElement.lang = l;',
        '  localizeStatic();',
        '  location.reload();',
        '}',
        '/* swap text nodes in the static markup, keyed by their Korean source */',
        'function localizeStatic(){',
        '  if (LANG === "ko") return;',
        '  var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);',
        '  var n, todo = [];',
        '  while ((n = w.nextNode())) {',
        '    var raw = n.nodeValue, k = raw.replace(/\\s+/g, " ").trim();',
        '    if (!k) continue;',
        '    var e = window.__I18N__[k];',
        '    if (!e) continue;',
        '    var tr = (LANG === "vi") ? e[1] : e[0];',
        '    if (!tr) { todo.push([n, ""]); continue; }',
        '    todo.push([n, raw.replace(/\\s+/g, " ") && raw.trim() === k ? tr : raw.replace(k, tr)]);',
        '  }',
        '  todo.forEach(function(p){ p[0].nodeValue = p[1]; });',
        '  // attributes: placeholders, titles and aria-labels carry Korean too',
        '  ["placeholder", "title", "aria-label"].forEach(function(attr){',
        '    Array.prototype.forEach.call(document.querySelectorAll("[" + attr + "]"), function(e2){',
        '      var v = e2.getAttribute(attr);',
        '      var e3 = window.__I18N__[String(v).replace(/\\s+/g, " ").trim()];',
        '      if (e3) e2.setAttribute(attr, (LANG === "vi") ? e3[1] : e3[0]);',
        '    });',
        '  });',
        '}',
    ])
    h = h.replace('"use strict";', '"use strict";\n' + inject, 1)

    # language switcher in the title bar, before the nav
    old_nav = '    <nav class="topnav" id="nav">'
    new_nav = ('    <span class="langsw" role="group" aria-label="Language">'
               '<button data-lang="en">EN</button>'
               '<button data-lang="vi">VI</button>'
               '<button data-lang="ko">KO</button></span>\n'
               '    <nav class="topnav" id="nav">')
    if old_nav in h:
        h = h.replace(old_nav, new_nav, 1)

    # style for the switcher
    h = h.replace("  .grow{flex:1;min-width:0}",
        "  .grow{flex:1;min-width:0}\n"
        "  .langsw{display:inline-flex;gap:2px;border:1px solid var(--line2);border-radius:9px;overflow:hidden}\n"
        "  .langsw button{border:0;border-radius:0;background:transparent;padding:6px 9px;font-size:12px;color:var(--muted)}\n"
        "  .langsw button[aria-pressed=\"true\"]{background:var(--accent);color:#fff;font-weight:700}\n", 1)

    # wire it up on boot
    h = h.replace("boot();\nloadCatalog();",
        "Array.prototype.forEach.call(document.querySelectorAll('[data-lang]'), function(b){\n"
        "  b.setAttribute('aria-pressed', b.getAttribute('data-lang') === LANG ? 'true' : 'false');\n"
        "  b.addEventListener('click', function(){ setLang(b.getAttribute('data-lang')); });\n"
        "});\n"
        "localizeStatic();\n"
        "boot();\nloadCatalog();", 1)

    open(CLIENT, "w").write(h)
    print("patched client.html with the i18n layer and a language switcher")


if __name__ == "__main__":
    main()
