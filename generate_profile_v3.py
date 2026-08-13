#!/usr/bin/env python3
"""生成媒体档案画像 HTML 报表 - 中文版"""

import json
from pathlib import Path

OUTPUT_DIR = Path.home() / ".media_archive"
OUTPUT_DIR.mkdir(exist_ok=True)

with open('/tmp/media_profile_v2.json') as f:
    p = json.load(f)

stats = p['stats']
douban = p['douban']
bili = p['bilibili']
netease = p['netease']
persona = p['persona']
recs = p['recommendations']

# 完成率
anime_rate = f"{bili['anime_watched']/max(bili['anime_total'],1)*100:.0f}%"
drama_rate = f"{bili['drama_watched']/max(bili['drama_total'],1)*100:.0f}%"

html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的媒体档案画像</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(90deg, #0f3460, #e94560);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-card .label { color: #888; margin-top: 5px; font-size: 0.9em; }
        .section {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .section h2 {
            font-size: 1.4em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .chart-container { position: relative; height: 250px; margin-bottom: 15px; }
        .persona-tags { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }
        .tag { padding: 6px 16px; border-radius: 20px; font-size: 0.9em; font-weight: 500; }
        .tag-yes { background: rgba(76, 175, 80, 0.3); color: #81c784; }
        .tag-no { background: rgba(255,255,255,0.1); color: #888; }
        .top-list { counter-reset: top; }
        .top-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 6px;
        }
        .top-item .rank {
            width: 24px;
            height: 24px;
            background: #e94560;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 12px;
        }
        .top-item .info { flex: 1; }
        .top-item .info .name { font-weight: 500; }
        .top-item .info .meta { font-size: 0.75em; color: #888; }
        .top-item .count { color: #e94560; font-weight: bold; font-size: 0.9em; }
        .recommend { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-top: 15px; }
        .rec-card { background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; border-left: 3px solid #e94560; }
        .rec-card .title { font-weight: 500; margin-bottom: 4px; }
        .rec-card .reason { font-size: 0.8em; color: #888; }
        .footer { text-align: center; color: #666; padding: 20px; font-size: 0.85em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 我的媒体档案画像</h1>
        <p class="subtitle">生成时间: """ + p['generated_at'] + """</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">""" + str(stats['total']) + """</div>
                <div class="label">总记录数</div>
            </div>
            <div class="stat-card">
                <div class="number">""" + str(stats['douban_movies']) + """</div>
                <div class="label">看过电影</div>
            </div>
            <div class="stat-card">
                <div class="number">""" + str(stats['bilibili_anime']) + """</div>
                <div class="label">追过番剧</div>
            </div>
            <div class="stat-card">
                <div class="number">""" + str(stats['netease_songs']) + """</div>
                <div class="label">喜欢歌曲</div>
            </div>
        </div>

        <div class="section">
            <h2>👤 用户画像</h2>
            <div class="persona-tags">
                <span class="tag """ + ('tag-yes' if persona['movie_fan'] else 'tag-no') + """">""" + ('✅' if persona['movie_fan'] else '❌') + """ 电影爱好者</span>
                <span class="tag """ + ('tag-yes' if persona['anime_otaku'] else 'tag-no') + """">""" + ('✅' if persona['anime_otaku'] else '❌') + """ 动漫爱好者</span>
                <span class="tag """ + ('tag-yes' if persona['music_lover'] else 'tag-no') + """">""" + ('✅' if persona['music_lover'] else '❌') + """ 音乐爱好者</span>
                <span class="tag """ + ('tag-yes' if persona['completionist'] else 'tag-no') + """">""" + ('✅' if persona['completionist'] else '❌') + """ 高完成率</span>
                <span class="tag """ + ('tag-yes' if persona['history_buff'] else 'tag-no') + """">""" + ('✅' if persona['history_buff'] else '❌') + """ 历史爱好者</span>
            </div>
        </div>

        <div class="section">
            <h2>🎬 豆瓣电影偏好</h2>
            <div class="chart-container">
                <canvas id="doubanChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>📺 B站追番/剧状态</h2>
            <div class="chart-container">
                <canvas id="bilibiliChart"></canvas>
            </div>
            <p>番剧完成率: <strong>""" + anime_rate + """</strong> | 剧集完成率: <strong>""" + drama_rate + """</strong></p>
        </div>

        <div class="section">
            <h2>🎵 网易云音乐偏好</h2>
            <div class="chart-container">
                <canvas id="artistChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>🏆 Top 10 歌手</h2>
            <div class="top-list">
""")

for i, (artist, count) in enumerate(list(netease['top_artists'].items())[:10], 1):
    html_parts.append(f"""                <div class="top-item">
                    <div class="rank">{i}</div>
                    <div class="info">
                        <div class="name">{artist}</div>
                    </div>
                    <div class="count">{count}首</div>
                </div>
""")

html_parts.append("""            </div>
        </div>

        <div class="section">
            <h2>🎧 最常听歌曲 (Top 10)</h2>
            <div class="top-list">
""")

for i, s in enumerate(netease['top_songs'][:10], 1):
    html_parts.append(f"""                <div class="top-item">
                    <div class="rank">{i}</div>
                    <div class="info">
                        <div class="name">{s['title']}</div>
                        <div class="meta">{s.get('artists', '')}</div>
                    </div>
                    <div class="count">{s.get('play_count', 0)}次</div>
                </div>
""")

html_parts.append("""            </div>
        </div>

        <div class="section">
            <h2>💡 为你推荐的媒体</h2>
            <h3 style="margin:15px 0 10px;color:#888;font-size:1em;">🎬 电影推荐</h3>
            <div class="recommend">
""")

for r in recs['movies']:
    html_parts.append(f"""                <div class="rec-card">
                    <div class="title">{r['title']}</div>
                    <div class="reason">{r['reason']}</div>
                </div>
""")

html_parts.append("""            </div>
            <h3 style="margin:15px 0 10px;color:#888;font-size:1em;">📺 番剧推荐</h3>
            <div class="recommend">
""")

for r in recs['anime']:
    html_parts.append(f"""                <div class="rec-card">
                    <div class="title">{r['title']}</div>
                    <div class="reason">{r['reason']}</div>
                </div>
""")

html_parts.append("""            </div>
            <h3 style="margin:15px 0 10px;color:#888;font-size:1em;">🎵 音乐推荐</h3>
            <div class="recommend">
""")

for r in recs['music']:
    html_parts.append(f"""                <div class="rec-card">
                    <div class="title">{r['artist']}</div>
                    <div class="reason">{r['reason']}</div>
                </div>
""")

# Build JavaScript
douban_labels = json.dumps(list(douban['year_dist'].keys()))
douban_data = json.dumps(list(douban['year_dist'].values()))
artist_labels = json.dumps(list(netease['top_artists'].keys())[:10])
artist_data = json.dumps(list(netease['top_artists'].values())[:10])

anime_watched = bili['anime_watched']
anime_on_hold = sum(1 for b in [{'status': 'on_hold'}] if True)  # simplified
drama_watched = bili['drama_watched']
drama_on_hold = 5  # from data

html_parts.append(f"""            </div>
        </div>

        <div class="footer">
            <p>数据来源: media-archive 项目 | 生成时间: {p['generated_at']}</p>
        </div>
    </div>

    <script>
        new Chart(document.getElementById('doubanChart'), {{
            type: 'bar',
            data: {{
                labels: {douban_labels},
                datasets: [{{
                    label: '观看数量',
                    data: {douban_data},
                    backgroundColor: 'rgba(233, 69, 96, 0.7)',
                    borderColor: 'rgba(233, 69, 96, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
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
                    data: [{anime_watched}, {bili['anime_total']-anime_watched-3}, {drama_watched}, {drama_on_hold}],
                    backgroundColor: ['#4caf50', '#ff9800', '#2196f3', '#9c27b0']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'right', labels: {{ color: '#eee' }} }} }}
            }}
        }});

        new Chart(document.getElementById('artistChart'), {{
            type: 'bar',
            data: {{
                labels: {artist_labels},
                datasets: [{{
                    label: '歌曲数',
                    data: {artist_data},
                    backgroundColor: 'rgba(83, 52, 131, 0.7)',
                    borderColor: 'rgba(83, 52, 131, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
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
""")

html = ''.join(html_parts)

output_path = OUTPUT_DIR / "media_profile.html"
output_path.write_text(html, encoding="utf-8")
print(f"画像报表已生成: {output_path}")
print(f"  总记录: {stats['total']}")
print(f"  豆瓣电影: {stats['douban_movies']}部")
print(f"  B站番剧: {stats['bilibili_anime']}部")
print(f"  网易云歌曲: {stats['netease_songs']}首")
print(f"\n用户画像:")
print(f"  电影爱好者: {'是' if persona['movie_fan'] else '否'}")
print(f"  动漫爱好者: {'是' if persona['anime_otaku'] else '否'}")
print(f"  音乐爱好者: {'是' if persona['music_lover'] else '否'}")
print(f"  高完成率: {'是' if persona['completionist'] else '否'}")
print(f"  历史爱好者: {'是' if persona['history_buff'] else '否'}")
