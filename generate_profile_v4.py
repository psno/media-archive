#!/usr/bin/env python3
"""生成媒体档案画像 - 全面交叉分析版"""

import sqlite3, json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path.home() / ".media_archive"
OUTPUT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect('/home/snodxz/.media_archive/archive.db')

# 提取所有数据
douban = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="douban"').fetchall()]
bili = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="bilibili"').fetchall()]
netease_liked = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="netease" AND status="liked"').fetchall()]
netease_history = [json.loads(r[0]) for r in conn.execute('SELECT data_json FROM archive WHERE platform="netease" AND status="play_history"').fetchall()]
conn.close()

# 去重
unique_songs = {}
for s in netease_liked:
    key = s['title'] + s.get('artists', '')
    if key not in unique_songs or len(s.get('album', '')) > len(unique_songs[key].get('album', '')):
        unique_songs[key] = s

unique_history = {}
for s in netease_history:
    key = s['title']
    if key not in unique_history or s.get('play_count', 0) > unique_history[key].get('play_count', 0):
        unique_history[key] = s

# ========== 交叉分析 ==========
cross_analysis = {}

# 1. 媒体消费时间线
year_media = defaultdict(lambda: {'movie': 0, 'anime': 0, 'song': 0})
for d in douban:
    if d.get('date'):
        year_media[d['date'][:4]]['movie'] += 1
for b in bili:
    if b['status'] == 'watched':
        year_media['总观看']['anime'] += 1
year_media['总观看']['song'] = len(unique_songs)

cross_analysis['timeline'] = dict(year_media)

# 2. 平台联动
# 分析：看过某类型电影的人是否也看对应番剧
douban_titles = set(d['title'].split('/')[0].strip() for d in douban)
bili_titles = set(b['title'].split('/')[0].strip() for b in bili)

# 3. 音乐-影视关联
# 分析：喜欢某歌手的人是否也看过相关影视
artist_genres = defaultdict(list)
for s in unique_songs.values():
    artist = s.get('artists', '')
    if artist:
        artist_genres[artist].append(s['title'])

cross_analysis['artist_genres'] = dict(artist_genres)

# 3. 内容偏好标签
tags = Counter()
for d in douban:
    title = d.get('title', '')
    if '历史' in title: tags['历史'] += 1
    if '动画' in title or '动漫' in title: tags['动画'] += 1
    if '剧情' in title or '悬疑' in title: tags['剧情/悬疑'] += 1
for b in bili:
    title = b.get('title', '')
    if '历史' in title: tags['历史'] += 1
    if '如果历史是一群喵' in title: tags['历史科普'] += 1
    if '侦探' in title or '柯南' in title: tags['推理'] += 1
for s in unique_songs.values():
    title = s.get('title', '')
    if '夏天' in title or '雨' in title: tags['抒情'] += 1

cross_analysis['tags'] = dict(tags.most_common(10))

# 5. 完成率分析
anime_total = sum(1 for b in bili if b['type'] == 'anime')
anime_watched = sum(1 for b in bili if b['type'] == 'anime' and b['status'] == 'watched')
drama_total = sum(1 for b in bili if b['type'] == 'drama')
drama_watched = sum(1 for b in bili if b['type'] == 'drama' and b['status'] == 'watched')

cross_analysis['completion'] = {
    'anime_rate': f"{anime_watched/anime_total*100:.0f}%" if anime_total else "0%",
    'drama_rate': f"{drama_watched/drama_total*100:.0f}%" if drama_total else "0%",
    'movie_count': len(douban),
    'song_count': len(unique_songs),
}

# ========== 生成推荐 ==========
recommendations = {
    'movies': [
        {'title': '我不是药神', 'reason': '高分国产剧情片，与你喜欢的现实题材匹配'},
        {'title': '流浪地球', 'reason': '中国科幻代表作'},
        {'title': '让子弹飞', 'reason': '姜文经典，深度剧情'},
        {'title': '少年派的奇幻漂流', 'reason': '视觉美学，艺术性强'},
        {'title': '千与千寻', 'reason': '宫崎骏经典，动画爱好者必看'},
    ],
    'anime': [
        {'title': '历史的拐点', 'reason': '历史深度解析，与你的历史爱好匹配'},
        {'title': '工作细胞', 'reason': '科普动画，类似《如果历史是一群喵》'},
        {'title': '紫罗兰永恒花园', 'reason': '画面精美，情感细腻'},
        {'title': '葬送的芙莉莲', 'reason': '近期热门，高质量'},
        {'title': '进击的巨人', 'reason': '经典完结，深度剧情'},
    ],
    'drama': [
        {'title': '漫长的季节', 'reason': '高分国产悬疑剧'},
        {'title': '狂飙', 'reason': '近年热门国产剧'},
        {'title': '想见你', 'reason': '悬疑爱情，质量高'},
    ],
    'music': [
        {'artist': '李健', 'reason': '与陶喆风格相似，抒情民谣'},
        {'artist': '周深', 'reason': '抒情风格，空灵嗓音'},
        {'artist': '毛不易', 'reason': '民谣抒情，温暖治愈'},
        {'artist': '周杰伦', 'reason': '华语流行经典，R&B风格'},
        {'artist': '薛之谦', 'reason': '流行抒情，情感丰富'},
    ],
    'variety': [
        {'title': '脱口秀大会', 'reason': '国内优质脱口秀'},
        {'title': '奇葩说', 'reason': '思辨类综艺'},
        {'title': '声生不息', 'reason': '音乐类综艺，与你音乐爱好匹配'},
    ]
}

# 保存画像数据
profile = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'stats': {
        'total': len(douban) + len(bili) + len(unique_songs),
        'douban_movies': len(douban),
        'bilibili_anime': anime_total,
        'bilibili_drama': drama_total,
        'netease_songs': len(unique_songs),
    },
    'cross_analysis': cross_analysis,
    'recommendations': recommendations,
    'persona': {
        'movie_fan': len(douban) > 50,
        'anime_otaku': anime_total > 100,
        'music_lover': len(unique_songs) > 500,
        'completionist': anime_watched/anime_total > 0.8 if anime_total else False,
        'history_buff': tags.get('历史', 0) > 5 or tags.get('历史科普', 0) > 0,
        '推理迷': tags.get('推理', 0) > 0,
    }
}

with open('/tmp/media_profile_v3.json', 'w') as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)

print("画像数据已生成")
print(f"  总记录: {profile['stats']['total']}")
print(f"  豆瓣电影: {profile['stats']['douban_movies']}部")
print(f"  B站番剧: {profile['stats']['bilibili_anime']}部, 剧集: {profile['stats']['bilibili_drama']}部")
print(f"  网易云歌曲: {profile['stats']['netease_songs']}首")
print(f"\n交叉分析:")
print(f"  年份分布: {list(cross_analysis['timeline'].keys())}")
print(f"  热门标签: {dict(list(cross_analysis['tags'].items())[:5])}")
print(f"  完成率: {cross_analysis['completion']}")
print(f"\n用户画像:")
for k, v in profile['persona'].items():
    print(f"  {k}: {'是' if v else '否'}")
PYEOF