#!/usr/bin/env python3
"""生成媒体档案画像 - 正确版本"""

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

# ========== 正确统计 ==========
# B站：用户说185是番剧总数，13是看过
anime = [b for b in bili if b['type'] == 'anime']
drama = [b for b in bili if b['type'] == 'drama']
anime_watched = sum(1 for a in anime if a['status'] == 'watched')
drama_watched = sum(1 for d in drama if d['status'] == 'watched')

# 网易云：去重按歌曲ID
song_ids = set()
unique_songs = []
for s in netease_liked:
    # 从URL提取歌曲ID
    url = s.get('url', '')
    if 'id=' in url:
        sid = url.split('id=')[1].split('&')[0]
        if sid not in song_ids:
            song_ids.add(sid)
            unique_songs.append(s)

print(f"网易云喜欢: {len(netease_liked)}条 -> 去重后: {len(unique_songs)}首")

# ========== 内容类型分析 ==========
# 豆瓣类型分析
douban_movies = [d for d in douban if '电影' in d['title'].split('/')[0]]
douban_tv = [d for d in douban if '剧' in d['title'] and '电影' not in d['title'].split('/')[0]]

# B站番剧类型分析
anime_genres = Counter()
for a in anime:
    title = a.get('title', '')
    subtitle = a.get('subtitle', '')
    text = title + ' ' + subtitle
    if '历史' in text: anime_genres['历史'] += 1
    if '侦探' in text or '柯南' in text or '怪盗' in text: anime_genres['推理/悬疑'] += 1
    if '莫里亚蒂' in text: anime_genres['推理/悬疑'] += 1
    if '科幻' in text or '机动' in text or '攻壳' in text: anime_genres['科幻'] += 1
    if '搞笑' in text or '日常' in text or '日常' in text: anime_genres['搞笑/日常'] += 1
    if '运动' in text: anime_genres['运动'] += 1
    if '音乐' in text or '歌手' in text: anime_genres['音乐'] += 1
    if '恋爱' in text or '爱情' in text: anime_genres['恋爱'] += 1
    if '冒险' in text: anime_genres['冒险'] += 1
    if '奇幻' in text: anime_genres['奇幻'] += 1

# 网易云风格分析
song_styles = Counter()
for s in unique_songs:
    artist = s.get('artists', '')
    title = s.get('title', '')
    text = artist + ' ' + title
    if '陶喆' in artist: song_styles['R&B/华语'] += 1
    elif '方大同' in artist: song_styles['R&B/华语'] += 1
    elif '林俊杰' in artist: song_styles['R&B/华语'] += 1
    elif '王力宏' in artist: song_styles['R&B/华语'] += 1
    elif '伍佰' in artist: song_styles['摇滚/华语'] += 1
    elif '陈奕迅' in artist: song_styles['流行/华语'] += 1
    elif '孙燕姿' in artist: song_styles['流行/华语'] += 1
    elif '莫文蔚' in artist: song_styles['流行/华语'] += 1
    elif 'Aimer' in artist: song_styles['日系动漫'] += 1
    elif any(x in artist for x in ['Leon', 'vietra', 'Lionzed']): song_styles['英文/独立'] += 1
    else: song_styles['其他'] += 1

# ========== 生成推荐 ==========
# 基于内容偏好推荐
def get_recommendations():
    recs = {
        'movies': [],
        'tv_shows': [],
        'anime': [],
        'songs': []
    }
    
    # 电影推荐：基于历史、推理、科幻偏好
    if anime_genres.get('历史', 0) > 5:
        recs['movies'].extend([
            {'title': '王的传说', 'reason': '历史题材，与你喜欢的历史动画匹配'},
            {'title': '长安三万里', 'reason': '中国历史动画电影'},
        ])
    if anime_genres.get('推理/悬疑', 0) > 5:
        recs['movies'].extend([
            {'title': '看不见的客人', 'reason': '悬疑推理，剧情反转'},
            {'title': '利刃出鞘', 'reason': '现代侦探故事'},
        ])
    if anime_genres.get('科幻', 0) > 0:
        recs['movies'].extend([
            {'title': '沙丘', 'reason': '科幻史诗'},
            {'title': '银翼杀手2049', 'reason': '赛博朋克美学'},
        ])
    
    # 番剧推荐：基于用户看过的
    if anime_genres.get('历史', 0) > 5:
        recs['anime'].extend([
            {'title': '帝王游戏攻略', 'reason': '历史策略类'},
            {'title': '战国BASARA', 'reason': '日本战国题材'},
        ])
    if anime_genres.get('推理/悬疑', 0) > 5:
        recs['anime'].extend([
            {'title': '怪盗基德1412', 'reason': '怪盗题材，与你的柯南收藏匹配'},
            {'title': '死亡笔记', 'reason': '经典推理对决'},
        ])
    # 排除用户不喜欢的
    # 紫罗兰永恒花园 - 用户说"一点都不喜欢"
    # 葬送的芙莉莲 - 用户说"看不进去"
    
    # 歌曲推荐：基于风格偏好
    if song_styles.get('R&B/华语', 0) > 50:
        recs['songs'].extend([
            {'artist': '李玖哲', 'song': '童话', 'reason': 'R&B抒情风格相似'},
            {'artist': '张敬轩', 'song': '断点', 'reason': '华语R&B经典'},
        ])
    if song_styles.get('日系动漫', 0) > 0:
        recs['songs'].extend([
            {'artist': 'RADWIMPS', 'song': '前前前世', 'reason': '动漫歌曲，与你喜欢的Aimer风格匹配'},
            {'artist': '米津玄师', 'song': 'Lemon', 'reason': '日系流行'},
        ])
    
    return recs

recommendations = get_recommendations()

# ========== 保存画像数据 ==========
profile = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'stats': {
        'total': len(douban) + len(bili) + len(unique_songs),
        'douban_movies': len(douban_movies),
        'douban_tv': len(douban_tv),
        'bilibili_anime_total': len(anime),
        'bilibili_anime_watched': anime_watched,
        'bilibili_drama_total': len(drama),
        'bilibili_drama_watched': drama_watched,
        'netease_songs': len(unique_songs),
    },
    'content_analysis': {
        'douban_types': {
            'movies': len(douban_movies),
            'tv_shows': len(douban_tv),
        },
        'anime_genres': dict(anime_genres.most_common(10)),
        'song_styles': dict(song_styles.most_common(10)),
    },
    'recommendations': recommendations,
}

with open('/tmp/media_profile_v4.json', 'w') as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)

print("\n画像数据已生成:")
print(f"  豆瓣: {len(douban)}条 (电影{len(douban_movies)}, 电视剧{len(douban_tv)})")
print(f"  B站: {len(bili)}条 (番剧{len(anime)}部, 剧集{len(drama)}部)")
print(f"  网易云: {len(unique_songs)}首 (去重后)")
print(f"\n内容类型偏好:")
print(f"  番剧类型: {dict(anime_genres.most_common(5))}")
print(f"  歌曲风格: {dict(song_styles.most_common(5))}")
print(f"\n推荐数量: 电影{len(recommendations['movies'])}, 番剧{len(recommendations['anime'])}, 歌曲{len(recommendations['songs'])}")
