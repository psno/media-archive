#!/usr/bin/env python3
"""生成媒体档案画像 HTML - 修复版"""

import json
from pathlib import Path

OUTPUT_DIR = Path.home() / ".media_archive"
OUTPUT_DIR.mkdir(exist_ok=True)

with open('/tmp/media_profile_final.json') as f:
    p = json.load(f)

stats = p['stats']
content = p['content_analysis']
recs = p['recommendations']
top_songs = p['top_songs'][:10]

# 解析歌手类型
artist_analysis = {}
for s in top_songs:
    artist = s.get('artists', '')
    if artist:
        artist_analysis[artist] = artist_analysis.get(artist, 0) + 1

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
        h1 {{ text-align: center; font-size: 2.2em; margin-bottom: 5px; background: linear-gradient(90deg, #e94560, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 25px; font-size: 0.9em; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 30px; }}
        .stat-card {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }}
        .stat-card .number {{ font-size: 1.8em; font-weight: bold; color: #e94560; }}
        .stat-card .label {{ color: #888; margin-top: 3px; font-size: 0.8em; }}
        .section {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }}
        .section h2 {{ font-size: 1.2em; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
        .chart-container {{ position: relative; height: 220px; margin-bottom: 12px; }}
        .tag-cloud {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }}
        .tag {{ padding: 4px 10px; border-radius: 12px; font-size: 0.75em; }}
        .tag-history {{ background: rgba(255,193,7,0.3); color: #ffc107; }}
        .tag-mystery {{ background: rgba(156,39,176,0.3); color: #ce93d8; }}
        .tag-scifi {{ background: rgba(33,150,243,0.3); color: #64b5f6; }}
        .tag-comedy {{ background: rgba(76,175,80,0.3); color: #81c784; }}
        .tag-romance {{ background: rgba(233,69,96,0.3); color: #ef5350; }}
        .tag-rnb {{ background: rgba(156,39,176,0.3); color: #ce93d8; }}
        .tag-jpop {{ background: rgba(255,152,0,0.3); color: #ffb74d; }}
        .song-list {{ counter-reset: song; }}
        .song-item {{ display: flex; align-items: center; padding: 8px 10px; background: rgba(0,0,0,0.2); border-radius: 6px; margin-bottom: 4px; font-size: 0.85em; }}
        .song-item .rank {{ width: 18px; height: 18px; background: #e94560; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7em; font-weight: bold; margin-right: 10px; }}
        .song-item .info {{ flex: 1; }}
        .song-item .info .name {{ font-weight: 500; }}
        .song-item .info .artist {{ font-size: 0.75em; color: #888; }}
        .song-item .count {{ color: #e94560; font-weight: bold; font-size: 0.8em; }}
        .rec-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 8px; margin-top: 10px; }}
        .rec-card {{ background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; border-left: 3px solid #e94560; }}
        .rec-card .title {{ font-weight: 500; margin-bottom: 3px; font-size: 0.85em; }}
        .rec-card .reason {{ font-size: 0.7em; color: #888; }}
        .insight {{ background: rgba(233,69,96,0.1); border-left: 3px solid #e94560; padding: 10px 15px; border-radius: 0 6px 6px 0; margin: 10px 0; font-size: 0.9em; }}
        .footer {{ text-align: center; color: #666; padding: 15px; font-size: 0.75em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 我的媒体档案画像</h1>
        <p class="subtitle">生成时间: {p['generated_at']}</p>
        
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['total']}</div><div class="label">总记录</div></div>
            <div class="stat-card"><div class="number">{stats['douban_total']}</div><div class="label">影视</div></div>
            <div class="stat-card"><div class="number">{stats['bilibili_anime_total']}</div><div class="label">番剧</div></div>
            <div class="stat-card"><div class="number">{stats['netease_songs']}</div><div class="label">歌曲</div></div>
        </div>

        <div class="section">
            <h2>🎯 内容偏好分析</h2>
            <div class="insight">
                <strong>核心发现:</strong> 你偏爱<strong>历史、推理、科幻</strong>类内容，音乐上喜欢<strong>R&B和华语流行</strong>
            </div>
            <div class="tag-cloud">
"""

# 添加标签
for genre, count in content['anime_genres'].items():
    cls = 'tag-history' if '历史' in genre else 'tag-mystery' if '推理' in genre else 'tag-scifi' if '科幻' in genre else 'tag-comedy' if '搞笑' in genre else 'tag-romance'
    html += f'                <span class="tag {cls}">{genre} ×{count}</span>\n'

for style, count in content['song_styles'].items():
    if count > 10:
        cls = 'tag-rnb' if 'R&B' in style or '流行' in style else 'tag-jpop' if '日系' in style else ''
        if cls:
            html += f'                <span class="tag {cls}">{style} ×{count}</span>\n'

html += """            </div>
        </div>

        <div class="section">
            <h2>🎬 豆瓣影视 (""" + str(stats['douban_movies']) + """部电影, """ + str(stats['douban_tv']) + """部剧)</h2>
            <div class="chart-container"><canvas id="doubanChart"></canvas></div>
        </div>

        <div class="section">
            <h2>📺 B站追番/剧</h2>
            <div class="chart-container"><canvas id="bilibiliChart"></canvas></div>
            <p style="font-size:0.8em;color:#888;">番剧""" + str(stats['bilibili_anime_total']) + """部 | 剧集""" + str(stats['bilibili_drama_total']) + """部</p>
        </div>

        <div class="section">
            <h2>🎵 网易云音乐</h2>
            <div class="chart-container"><canvas id="styleChart"></canvas></div>
        </div>

        <div class="section">
            <h2>🎧 最常听歌曲 (Top 10)</h2>
            <div class="song-list">
"""

for i, s in enumerate(top_songs, 1):
    html += f'                <div class="song-item"><div class="rank">{i}</div><div class="info"><div class="name">{s["title"]}</div><div class="artist">{s.get("artists", "")}</div></div><div class="count">{s.get("play_count", 0)}次</div></div>\n'

html += """            </div>
        </div>

        <div class="section">
            <h2>💡 推荐内容</h2>
            <h3 style="margin:10px 0;color:#888;font-size:0.9em;">🎬 电影</h3>
            <div class="rec-grid">
"""

for r in recs['movies']:
    html += f'                <div class="rec-card"><div class="title">{r["title"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += """            </div>
            <h3 style="margin:15px 0 10px;color:#888;font-size:0.9em;">📺 番剧</h3>
            <div class="rec-grid">
"""

for r in recs['anime']:
    html += f'                <div class="rec-card"><div class="title">{r["title"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += """            </div>
            <h3 style="margin:15px 0 10px;color:#888;font-size:0.9em;">🎵 歌曲</h3>
            <div class="rec-grid">
"""

for r in recs['songs']:
    html += f'                <div class="rec-card"><div class="title">{r["artist"]} - {r["song"]}</div><div class="reason">{r["reason"]}</div></div>\n'

# 构建图表数据
douban_years = ['2018', '2019', '2020', '2021', '2022', '2023', '2025']
douban_counts = [2, 45, 8, 28, 30, 13, 9]
anime_genres_labels = list(content['anime_genres'].keys())[:6]
anime_genres_data = list(content['anime_genres'].values())[:6]
song_style_labels = ['R&B/华语', '流行/华语', '摇滚/华语', '日系动漫', '其他']
song_style_data = [135, 40, 38, 3, 784]

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
                labels: {json.dumps(douban_years)},
                datasets: [{{
                    label: '观看数量',
                    data: {json.dumps(douban_counts)},
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
                    data: [{stats['bilibili_anime_watched']}, {stats['bilibili_anime_total']-stats['bilibili_anime_watched']-1}, {stats['bilibili_drama_watched']}, {stats['bilibili_drama_total']-stats['bilibili_drama_watched']-1}],
                    backgroundColor: ['#4caf50', '#ff9800', '#2196f3', '#9c27b0']
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'right', labels: {{ color: '#eee', font: {{ size: 10 }} }} }} }}
            }}
        }});

        new Chart(document.getElementById('styleChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(song_style_labels)},
                datasets: [{{
                    label: '歌曲数',
                    data: {json.dumps(song_style_data)},
                    backgroundColor: ['rgba(156,39,176,0.7)', 'rgba(33,150,243,0.7)', 'rgba(255,152,0,0.7)', 'rgba(244,67,54,0.7)', 'rgba(158,158,158,0.7)'],
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
    </script>
</body>
</html>
"""

output_path = OUTPUT_DIR / "media_profile.html"
output_path.write_text(html, encoding="utf-8")
print(f"画像报表已生成: {output_path}")
print(f"  文件大小: {output_path.stat().st_size / 1024:.1f}KB")
