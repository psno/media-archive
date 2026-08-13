#!/usr/bin/env python3
"""生成媒体档案画像 - 正确版"""

import sqlite3, json
from collections import Counter
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path.home() / ".media_archive"
OUTPUT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect('/home/snodxz/.media_archive/archive.db')

# 提取数据
douban = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="douban"').fetchall()]
bili = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="bilibili"').fetchall()]
netease_liked = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="netease" AND status="liked"').fetchall()]
netease_history = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="netease" AND status="play_history"').fetchall()]
conn.close()

# ========== 正确统计（按用户说的）==========
# B站
anime = [b for b in bili if b['type'] == 'anime']
drama = [b for b in bili if b['type'] == 'drama']
# 用户说番剧看过13部，剧集看过5部
anime_total = len(anime)  # 185
drama_total = len(drama)  # 29
anime_watched = 13  # 用户说的
drama_watched = 5   # 用户说的

# 网易云：保持1423首
netease_total = len(netease_liked)  # 1423

# 豆瓣：分析类型
douban_movies = []
douban_tv = []
for d in douban:
    title = d.get('title', '')
    main = title.split('/')[0].strip()
    # 根据标题判断
    if '剧' in main and '电影' not in main and '动画' not in main and '动漫' not in main:
        douban_tv.append(d)
    else:
        douban_movies.append(d)

# ========== 内容类型分析 ==========
# B站番剧类型
anime_genres = Counter()
for a in anime:
    title = a.get('title', '')
    subtitle = a.get('subtitle', '')
    text = title + ' ' + subtitle
    if '历史' in text: anime_genres['历史'] += 1
    if '侦探' in text or '柯南' in text or '怪盗' in text or '莫里亚蒂' in text: anime_genres['推理/悬疑'] += 1
    if '科幻' in text or '机动' in text or '攻壳' in text: anime_genres['科幻'] += 1
    if '搞笑' in text or '日常' in text: anime_genres['搞笑/日常'] += 1
    if '运动' in text: anime_genres['运动'] += 1
    if '音乐' in text or '歌手' in text: anime_genres['音乐'] += 1
    if '恋爱' in text or '爱情' in text: anime_genres['恋爱'] += 1

# 网易云风格
song_styles = Counter()
for s in netease_liked:
    artist = s.get('artists', '')
    if '陶喆' in artist or '方大同' in artist or '林俊杰' in artist or '王力宏' in artist:
        song_styles['R&B/华语'] += 1
    elif '伍佰' in artist:
        song_styles['摇滚/华语'] += 1
    elif '陈奕迅' in artist or '孙燕姿' in artist or '莫文蔚' in artist:
        song_styles['流行/华语'] += 1
    elif 'Aimer' in artist or 'LiSA' in artist:
        song_styles['日系动漫'] += 1
    else:
        song_styles['其他'] += 1

# ========== 推荐逻辑 ==========
recommendations = {
    'movies': [],
    'anime': [],
    'songs': []
}

# 基于类型推荐
if anime_genres.get('历史', 0) > 5:
    recommendations['movies'].extend([
        {'title': '长安三万里', 'reason': '中国历史动画电影'},
        {'title': '龙王战士', 'reason': '历史题材'},
    ])
    recommendations['anime'].extend([
        {'title': '帝王游戏攻略', 'reason': '历史策略类'},
    ])

if anime_genres.get('推理/悬疑', 0) > 5:
    recommendations['movies'].extend([
        {'title': '看不见的客人', 'reason': '悬疑推理'},
        {'title': '利刃出鞘', 'reason': '现代侦探故事'},
    ])
    recommendations['anime'].extend([
        {'title': '怪盗基德1412', 'reason': '怪盗题材'},
        {'title': '死亡笔记', 'reason': '经典推理对决'},
    ])

if song_styles.get('R&B/华语', 0) > 50:
    recommendations['songs'].extend([
        {'artist': '李玖哲', 'song': '童话', 'reason': 'R&B抒情风格'},
        {'artist': '张敬轩', 'song': '断点', 'reason': '华语R&B经典'},
    ])

if song_styles.get('日系动漫', 0) > 0:
    recommendations['songs'].extend([
        {'artist': 'RADWIMPS', 'song': '前前前世', 'reason': '动漫歌曲'},
        {'artist': '米津玄师', 'song': 'Lemon', 'reason': '日系流行'},
    ])

# ========== 生成画像数据 ==========
profile = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'stats': {
        'total': len(douban) + len(bili) + netease_total,
        'douban_movies': len(douban_movies),
        'douban_tv': len(douban_tv),
        'bilibili_anime_total': anime_total,
        'bilibili_anime_watched': anime_watched,
        'bilibili_drama_total': drama_total,
        'bilibili_drama_watched': drama_watched,
        'netease_songs': netease_total,
    },
    'content_analysis': {
        'anime_genres': dict(anime_genres.most_common(10)),
        'song_styles': dict(song_styles.most_common(10)),
    },
    'recommendations': recommendations,
    'top_songs': sorted(netease_history, key=lambda x: x.get('play_count', 0), reverse=True)[:20],
}

with open('/tmp/media_profile_v5.json', 'w') as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)

print("画像数据已生成:")
print(f"  豆瓣: {len(douban)}条 (电影{len(douban_movies)}, 电视剧{len(douban_tv)})")
print(f"  B站: 番剧{anime_total}部(看过{anime_watched}), 剧集{drama_total}部(看过{drama_watched})")
print(f"  网易云: {netease_total}首")
print(f"  番剧类型: {dict(anime_genres.most_common(5))}")
print(f"  歌曲风格: {dict(song_styles.most_common(5))}")
