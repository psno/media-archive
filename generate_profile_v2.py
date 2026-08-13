#!/usr/bin/env python3
"""生成媒体档案画像 - 用户偏好分析版"""

import sqlite3, json
from collections import Counter, defaultdict
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

# 去重
unique_songs = {}
for s in netease_liked:
    key = s['title']
    if key not in unique_songs:
        unique_songs[key] = s

unique_history = {}
for s in netease_history:
    key = s['title']
    if key not in unique_history or s.get('play_count', 0) > unique_history[key].get('play_count', 0):
        unique_history[key] = s

# ========== 用户画像分析 ==========
profile = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    
    # 基础统计
    'stats': {
        'total': len(douban) + len(bili) + len(unique_songs),
        'douban_movies': len(douban),
        'bilibili_anime': sum(1 for b in bili if b['type'] == 'anime'),
        'bilibili_drama': sum(1 for b in bili if b['type'] == 'drama'),
        'netease_songs': len(unique_songs),
    },
    
    # 豆瓣分析
    'douban': {
        'year_dist': dict(Counter(d['date'][:4] for d in douban if d.get('date')).most_common()),
        'recent': sorted([d['title'] for d in douban if d.get('date')], key=lambda x: next((d['date'] for d in douban if d['title']==x), ''), reverse=True)[:10],
    },
    
    # B站分析
    'bilibili': {
        'anime_watched': sum(1 for b in bili if b['type'] == 'anime' and b['status'] == 'watched'),
        'anime_total': sum(1 for b in bili if b['type'] == 'anime'),
        'drama_watched': sum(1 for b in bili if b['type'] == 'drama' and b['status'] == 'watched'),
        'drama_total': sum(1 for b in bili if b['type'] == 'drama'),
        'recent_anime': sorted([b['title'] for b in bili if b['type'] == 'anime'], reverse=True)[:10],
    },
    
    # 网易云分析
    'netease': {
        'top_artists': dict(Counter(s.get('artists', '').strip() for s in unique_songs.values() if s.get('artists')).most_common(15)),
        'top_songs': sorted(unique_history.values(), key=lambda x: x.get('play_count', 0), reverse=True)[:20],
        'total_duration_h': sum(s.get('duration_ms', 0) for s in unique_songs.values()) / 3600000,
    },
    
    # 用户画像标签
    'persona': {
        'movie_fan': len(douban) > 50,
        'anime_otaku': len([b for b in bili if b['type'] == 'anime']) > 100,
        'music_lover': len(unique_songs) > 500,
        'chinese_pop_fan': any(a in ['陶喆', '伍佰', '方大同', '林俊杰', '王力宏', '陈奕迅', '孙燕姿', '莫文蔚'] 
                              for a in list(Counter(s.get('artists', '').strip() for s in unique_songs.values() if s.get('artists')).keys())[:5]),
        'completionist': sum(1 for b in bili if b['status'] == 'watched') / max(sum(1 for b in bili if b['type'] == 'anime'), 1) > 0.8,
        'history_buff': any('历史' in t for t in [b['title'] for b in bili if b['type'] == 'anime']),
    },
    
    # 推荐列表
    'recommendations': {
        'movies': [],
        'anime': [],
        'music': [],
    }
}

# ========== 生成推荐 ==========
# 基于用户偏好的推荐逻辑
def generate_recommendations():
    # 豆瓣推荐：高分国产/亚洲电影
    profile['recommendations']['movies'] = [
        {'title': '我不是药神', 'reason': '高分国产剧情片'},
        {'title': '流浪地球', 'reason': '中国科幻代表作'},
        {'title': '蜘蛛侠：平行宇宙', 'reason': '动画创新'},
        {'title': '让子弹飞', 'reason': '姜文经典'},
        {'title': '少年派的奇幻漂流', 'reason': '视觉美学'},
    ]
    
    # B站推荐：历史/科普类动画
    profile['recommendations']['anime'] = [
        {'title': '历史的拐点', 'reason': '历史深度解析'},
        {'title': '如果历史是一群喵', 'reason': '你的收藏中已有'},
        {'title': '工作细胞', 'reason': '科普动画'},
        {'title': '紫罗兰永恒花园', 'reason': '画面精美'},
        {'title': '葬送的芙莉莲', 'reason': '近期热门'},
    ]
    
    # 网易云推荐：相似歌手
    top_artist = list(Counter(s.get('artists', '').strip() for s in unique_songs.values() if s.get('artists')).most_common())[0][0] if any(s.get('artists') for s in unique_songs.values()) else ''
    profile['recommendations']['music'] = [
        {'artist': '李健', 'reason': '与陶喆风格相似'},
        {'artist': '周深', 'reason': '抒情风格'},
        {'artist': '毛不易', 'reason': '民谣抒情'},
        {'artist': '周杰伦', 'reason': '华语流行经典'},
        {'artist': '薛之谦', 'reason': '流行抒情'},
    ]

generate_recommendations()

# 保存画像数据
with open('/tmp/media_profile_v2.json', 'w') as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)

print("画像数据已生成")
print(f"  总记录: {profile['stats']['total']}")
print(f"  豆瓣: {profile['stats']['douban_movies']}部")
print(f"  B站番剧: {profile['stats']['bilibili_anime']}部, 剧集: {profile['stats']['bilibili_drama']}部")
print(f"  网易云: {profile['stats']['netease_songs']}首")
print(f"  音乐时长: {profile['netease']['total_duration_h']:.1f}小时")
print(f"\n用户画像:")
print(f"  电影爱好者: {'是' if profile['persona']['movie_fan'] else '否'}")
print(f"  动漫爱好者: {'是' if profile['persona']['anime_otaku'] else '否'}")
print(f"  音乐爱好者: {'是' if profile['persona']['music_lover'] else '否'}")
print(f"  华语流行: {'是' if profile['persona']['chinese_pop_fan'] else '否'}")
print(f"  完成率>80%: {'是' if profile['persona']['completionist'] else '否'}")
print(f"  历史爱好者: {'是' if profile['persona']['history_buff'] else '否'}")
PYEOF