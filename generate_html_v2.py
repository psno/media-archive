#!/usr/bin/env python3
"""生成媒体档案画像 HTML 报表 - 全面版"""

import json
from pathlib import Path

OUTPUT_DIR = Path.home() / ".media_archive"
OUTPUT_DIR.mkdir(exist_ok=True)

with open('/tmp/media_profile_v3.json') as f:
    p = json.load(f)

stats = p['stats']
cross = p['cross_analysis']
recs = p['recommendations']
persona = p['persona']

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的媒体档案画像</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 30px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-card .number {{ font-size: 2em; font-weight: bold; color: #e94560; }}
        .stat-card .label {{ color: #888; margin-top: 5px; font-size: 0.85em; }}
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{ font-size: 1.3em; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        .chart-container {{ position: relative; height: 250px; margin-bottom: 15px; }}
        .persona-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 15px 0; }}
        .tag {{ padding: 5px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 500; }}
        .tag-yes {{ background: rgba(76, 175, 80, 0.3); color: #81c784; }}
        .tag-no {{ background: rgba(255,255,255,0.1); color: #666; }}
        .tag-blue {{ background: rgba(33, 150, 243, 0.3); color: #64b5f6; }}
        .tag-purple {{ background: rgba(156, 39, 176, 0.3); color: #ce93d8; }}
        .tag-orange {{ background: rgba(255, 152, 0, 0.3); color: #ffb74d; }}
        .top-list {{ counter-reset: top; }}
        .top-item {{
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}
        .top-item .rank {{ width: 20px; height: 20px; background: #e94560; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75em; font-weight: bold; margin-right: 10px; }}
        .top-item .info {{ flex: 1; }}
        .top-item .info .name {{ font-weight: 500; }}
        .top-item .info .meta {{ font-size: 0.75em; color: #888; }}
        .top-item .count {{ color: #e94560; font-weight: bold; font-size: 0.85em; }}
        .recommend-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-top: 15px; }}
        .rec-card {{ background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; border-left: 3px solid #e94560; }}
        .rec-card .title {{ font-weight: 500; margin-bottom: 4px; font-size: 0.9em; }}
        .rec-card .reason {{ font-size: 0.75em; color: #888; }}
        .footer {{ text-align: center; color: #666; padding: 20px; font-size: 0.8em; }}
        .tag-cloud {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
        .tag-item {{ background: rgba(233, 69, 96, 0.2); padding: 4px 10px; border-radius: 12px; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 我的媒体档案画像</h1>
        <p class="subtitle">生成时间: {p['generated_at']}</p>
        
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['total']}</div><div class="label">总记录</div></div>
            <div class="stat-card"><div class="number">{stats['douban_movies']}</div><div class="label">看过电影</div></div>
            <div class="stat-card"><div class="number">{stats['bilibili_anime']}</div><div class="label">追过番剧</div></div>
            <div class="stat-card"><div class="number">{stats['bilibili_drama']}</div><div class="label">追过剧集</div></div>
            <div class="stat-card"><div class="number">{stats['netease_songs']}</div><div class="label">喜欢歌曲</div></div>
        </div>

        <div class="section">
            <h2>👤 用户画像</h2>
            <div class="persona-tags">
                <span class="tag {'tag-yes' if persona['movie_fan'] else 'tag-no'}">{'✅' if persona['movie_fan'] else '❌'} 电影爱好者</span>
                <span class="tag {'tag-blue' if persona['anime_otaku'] else 'tag-no'}">{'✅' if persona['anime_otaku'] else '❌'} 动漫爱好者</span>
                <span class="tag {'tag-purple' if persona['music_lover'] else 'tag-no'}">{'✅' if persona['music_lover'] else '❌'} 音乐爱好者</span>
                <span class="tag {'tag-orange' if persona['completionist'] else 'tag-no'}">{'✅' if persona['completionist'] else '❌'} 高完成率</span>
                <span class="tag {'tag-yes' if persona['history_buff'] else 'tag-no'}">{'✅' if persona['history_buff'] else '❌'} 历史爱好者</span>
                <span class="tag {'tag-blue' if persona.get('推理迷') else 'tag-no'}">{'✅' if persona.get('推理迷') else '❌'} 推理迷</span>
            </div>
        </div>

        <div class="section">
            <h2>🏷️ 内容标签</h2>
            <div class="tag-cloud">
"""

for tag, count in list(cross['tags'].items())[:15]:
    html += f'<span class="tag-item">{tag} ×{count}</span>\n'

html += """            </div>
        </div>

        <div class="section">
            <h2>🎬 豆瓣电影</h2>
            <div class="chart-container"><canvas id="doubanChart"></canvas></div>
        </div>

        <div class="section">
            <h2>📺 B站追番/剧</h2>
            <div class="chart-container"><canvas id="bilibiliChart"></canvas></div>
            <p style="font-size:0.9em;color:#888;">番剧完成率: <strong style="color:#4caf50;">""" + cross['completion']['anime_rate'] + """</strong> | 剧集完成率: <strong style="color:#2196f3;">""" + cross['completion']['drama_rate'] + """</strong></p>
        </div>

        <div class="section">
            <h2>🎵 网易云音乐</h2>
            <div class="chart-container"><canvas id="artistChart"></canvas></div>
        </div>

        <div class="section">
            <h2>🏆 Top 10 歌手</h2>
            <div class="top-list">
"""

# Top artists
netease_top_artists = sorted(cross.get('artist_genres', {}).items(), key=lambda x: -len(x[1]))[:10]
for i, (artist, songs) in enumerate(netease_top_artists, 1):
    html += f'                <div class="top-item"><div class="rank">{i}</div><div class="info"><div class="name">{artist}</div><div class="meta">{len(songs)}首</div></div></div>\n'

html += """            </div>
        </div>

        <div class="section">
            <h2>🎧 最常听歌曲 (Top 10)</h2>
            <div class="top-list">
"""

# Top songs
for i, s in enumerate(sorted(cross.get('timeline', {}).items(), key=lambda x: -x[1].get('play_count', 0))[:10] if hasattr(cross.get('timeline'), 'items') else [], 1):
    html += f'                <div class="top-item"><div class="rank">{i}</div><div class="info"><div class="name">{s[0]}</div></div><div class="count">{s[1].get("play_count", 0)}次</div></div>\n'

# 重新获取top songs
for i, (title, data) in enumerate(sorted([(s['title'], s) for s in [json.loads(r[0]) for r in __import__('sqlite3').connect('/home/snodxz/.media_archive/archive.db').execute('SELECT data_json FROM archive WHERE platform="netease" AND status="play_history"').fetchall()]], key=lambda x: -x[1].get('play_count', 0))[:10], 1):
    html += f'                <div class="top-item"><div class="rank">{i}</div><div class="info"><div class="name">{title}</div><div class="meta">{data.get("artists", "")}</div></div><div class="count">{data.get("play_count", 0)}次</div></div>\n'

html += """            </div>
        </div>

        <div class="section">
            <h2>💡 推荐</h2>
            <h3 style="margin:10px 0;color:#888;font-size:1em;">🎬 电影推荐</h3>
            <div class="recommend-grid">
"""

for r in recs['movies']:
    html += f'                <div class="rec-card"><div class="title">{r["title"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += """            </div>
            <h3 style="margin:15px 0 10px;color:#888;font-size:1em;">📺 番剧推荐</h3>
            <div class="recommend-grid">
"""

for r in recs['anime']:
    html += f'                <div class="rec-card"><div class="title">{r["title"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += """            </div>
            <h3 style="margin:15px 0 10px;color:#888;font-size:1em;">🎵 音乐推荐</h3>
            <div class="recommend-grid">
"""

for r in recs['music']:
    html += f'                <div class="rec-card"><div class="title">{r["artist"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += f"""            </div>
        </div>

        <div class="footer">
            <p>数据来源: media-archive 项目 | 生成时间: {p['generated_at']}</p>
        </div>
    </div>

    <script>
        new Chart(document.getElementById('doubanChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(list(cross['timeline'].keys()))},
                datasets: [{{
                    label: '观看数量',
                    data: {json.dumps([cross['timeline'][k].get('movie', 0) for k in cross['timeline'].keys()])},
                    backgroundColor: 'rgba(233, 69, 96, 0.7)',
                    borderColor: 'rgba(233, 69, 96, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    x: {{ ticks: {{ color: '#888' }}, grid: {{ display: false }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('bilibiliChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['番剧看过', '番剧搁置', '剧集看过', '剧集搁置'],
                datasets: [{{
                    data: [{stats['bilibili_anime']-13}, 13, {stats['bilibili_drama']-5}, 5],
                    backgroundColor: ['#4caf50', '#ff9800', '#2196f3', '#9c27b0']
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'right', labels: {{ color: '#eee' }} }} }}
            }}
        }});

        new Chart(document.getElementById('artistChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([a[0] for a in netease_top_artists])},
                datasets: [{{
                    label: '歌曲数',
                    data: {json.dumps([len(a[1]) for a in netease_top_artists])},
                    backgroundColor: 'rgba(83, 52, 131, 0.7)',
                    borderColor: 'rgba(83, 52, 131, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{ ticks: {{ color: '#eee' }}, grid: {{ display: false }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

output_path = OUTPUT_DIR / "media_profile.html"
output_path.write_text(html, encoding="utf-8")
print(f"画像报表已生成: {output_path}")
