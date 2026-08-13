#!/usr/bin/env python3
"""生成媒体档案画像 HTML - 正确版"""

import json
from pathlib import Path

with open('/tmp/media_profile_v5.json') as f:
    p = json.load(f)

stats = p['stats']
content = p['content_analysis']
recs = p['recommendations']
top_songs = p['top_songs'][:10]

OUTPUT_DIR = Path.home() / ".media_archive"

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的媒体档案画像</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #eee; padding: 20px; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{ text-align: center; font-size: 2em; margin-bottom: 5px; background: linear-gradient(90deg, #e94560, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 20px; font-size: 0.85em; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 25px; }}
        .stat-card {{ background: rgba(255,255,255,0.05); border-radius: 10px; padding: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }}
        .stat-card .number {{ font-size: 1.6em; font-weight: bold; color: #e94560; }}
        .stat-card .label {{ color: #888; margin-top: 2px; font-size: 0.75em; }}
        .section {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 18px; margin-bottom: 18px; border: 1px solid rgba(255,255,255,0.1); }}
        .section h2 {{ font-size: 1.1em; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .chart-container {{ position: relative; height: 200px; margin-bottom: 10px; }}
        .tag-cloud {{ display: flex; flex-wrap: wrap; gap: 5px; margin: 8px 0; }}
        .tag {{ padding: 3px 8px; border-radius: 10px; font-size: 0.7em; }}
        .tag-history {{ background: rgba(255,193,7,0.3); color: #ffc107; }}
        .tag-mystery {{ background: rgba(156,39,176,0.3); color: #ce93d8; }}
        .tag-scifi {{ background: rgba(33,150,243,0.3); color: #64b5f6; }}
        .tag-comedy {{ background: rgba(76,175,80,0.3); color: #81c784; }}
        .tag-rnb {{ background: rgba(156,39,176,0.3); color: #ce93d8; }}
        .tag-jpop {{ background: rgba(255,152,0,0.3); color: #ffb74d; }}
        .song-item {{ display: flex; align-items: center; padding: 6px 10px; background: rgba(0,0,0,0.2); border-radius: 5px; margin-bottom: 3px; font-size: 0.8em; }}
        .song-item .rank {{ width: 16px; height: 16px; background: #e94560; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.65em; font-weight: bold; margin-right: 8px; }}
        .song-item .info {{ flex: 1; }}
        .song-item .info .name {{ font-weight: 500; }}
        .song-item .info .artist {{ font-size: 0.7em; color: #888; }}
        .song-item .count {{ color: #e94560; font-weight: bold; font-size: 0.75em; }}
        .rec-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 6px; margin-top: 8px; }}
        .rec-card {{ background: rgba(0,0,0,0.2); padding: 8px; border-radius: 5px; border-left: 2px solid #e94560; }}
        .rec-card .title {{ font-weight: 500; margin-bottom: 2px; font-size: 0.8em; }}
        .rec-card .reason {{ font-size: 0.65em; color: #888; }}
        .insight {{ background: rgba(233,69,96,0.1); border-left: 2px solid #e94560; padding: 8px 12px; border-radius: 0 5px 5px 0; margin: 8px 0; font-size: 0.85em; }}
        .note {{ font-size: 0.75em; color: #666; margin-top: 5px; font-style: italic; }}
        .footer {{ text-align: center; color: #666; padding: 15px; font-size: 0.7em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 我的媒体档案画像</h1>
        <p class="subtitle">生成时间: {p['generated_at']}</p>
        
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['total']}</div><div class="label">总记录</div></div>
            <div class="stat-card"><div class="number">{stats['douban_movies']}</div><div class="label">电影</div></div>
            <div class="stat-card"><div class="number">{stats['douban_tv']}</div><div class="label">电视剧</div></div>
            <div class="stat-card"><div class="number">{stats['bilibili_anime_total']}</div><div class="label">番剧</div></div>
            <div class="stat-card"><div class="number">{stats['bilibili_drama_total']}</div><div class="label">剧集</div></div>
            <div class="stat-card"><div class="number">{stats['netease_songs']}</div><div class="label">歌曲</div></div>
        </div>

        <div class="section">
            <h2>🎯 内容偏好分析</h2>
            <div class="insight">
                <strong>核心发现:</strong> 你偏爱<strong>历史、推理、科幻</strong>类番剧，音乐上喜欢<strong>R&B和华语流行</strong>
            </div>
            <div class="tag-cloud">
"""

# 添加标签
for genre, count in content['anime_genres'].items():
    cls = 'tag-history' if '历史' in genre else 'tag-mystery' if '推理' in genre else 'tag-scifi' if '科幻' in genre else 'tag-comedy' if '搞笑' in genre else ''
    if cls:
        html += f'                <span class="tag {cls}">{genre} ×{count}</span>\n'

for style, count in content['song_styles'].items():
    if count > 20:
        cls = 'tag-rnb' if 'R&B' in style or '流行' in style else 'tag-jpop' if '日系' in style else ''
        if cls:
            html += f'                <span class="tag {cls}">{style} ×{count}</span>\n'

html += f"""            </div>
            <p class="note">注：番剧收藏{stats['bilibili_anime_total']}部，其中标记看过{stats['bilibili_anime_watched']}部；剧集收藏{stats['bilibili_drama_total']}部，其中标记看过{stats['bilibili_drama_watched']}部</p>
        </div>

        <div class="section">
            <h2>🎬 豆瓣影视 ({stats['douban_movies']}部电影, {stats['douban_tv']}部剧)</h2>
            <div class="chart-container"><canvas id="doubanChart"></canvas></div>
        </div>

        <div class="section">
            <h2>📺 B站追番/剧</h2>
            <div class="chart-container"><canvas id="bilibiliChart"></canvas></div>
        </div>

        <div class="section">
            <h2>🎵 网易云音乐 ({stats['netease_songs']}首)</h2>
            <div class="chart-container"><canvas id="styleChart"></canvas></div>
        </div>

        <div class="section">
            <h2>🎧 最常听歌曲 (Top 10)</h2>
"""

for i, s in enumerate(top_songs, 1):
    html += f'                <div class="song-item"><div class="rank">{i}</div><div class="info"><div class="name">{s["title"]}</div><div class="artist">{s.get("artists", "")}</div></div><div class="count">{s.get("play_count", 0)}次</div></div>\n'

html += """            </div>
        </div>

        <div class="section">
            <h2>💡 推荐内容</h2>
            <h3 style="margin:8px 0;color:#888;font-size:0.85em;">🎬 电影</h3>
            <div class="rec-grid">
"""

for r in recs['movies']:
    html += f'                <div class="rec-card"><div class="title">{r["title"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += """            </div>
            <h3 style="margin:12px 0 8px;color:#888;font-size:0.85em;">📺 番剧</h3>
            <div class="rec-grid">
"""

for r in recs['anime']:
    html += f'                <div class="rec-card"><div class="title">{r["title"]}</div><div class="reason">{r["reason"]}</div></div>\n'

html += """            </div>
            <h3 style="margin:12px 0 8px;color:#888;font-size:0.85em;">🎵 歌曲</h3>
            <div class="rec-grid">
"""

for r in recs['songs']:
    html += f'                <div class="rec-card"><div class="title">{r["artist"]} - {r["song"]}</div><div class="reason">{r["reason"]}</div></div>\n'

# 图表数据
douban_years = ['2018', '2019', '2020', '2021', '2022', '2023', '2025']
douban_counts = [2, 45, 8, 28, 30, 13, 9]
anime_genres_labels = list(content['anime_genres'].keys())[:6]
anime_genres_data = list(content['anime_genres'].values())[:6]
song_style_labels = ['R&B/华语', '流行/华语', '摇滚/华语', '日系动漫', '其他']
song_style_data = [185, 54, 70, 3, 1111]

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
                labels: ['番剧', '剧集'],
                datasets: [{{
                    data: [{stats['bilibili_anime_total']}, {stats['bilibili_drama_total']}],
                    backgroundColor: ['#e94560', '#0f3460']
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
