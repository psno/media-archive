#!/usr/bin/env python3
"""生成媒体档案画像 HTML 报表"""

import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path.home() / ".media_archive"
OUTPUT_DIR.mkdir(exist_ok=True)

# 加载画像数据
with open('/tmp/media_profile.json') as f:
    p = json.load(f)

summary = p['summary']
douban = p['douban']
bili = p['bilibili']
netease = p['netease']

# 计算统计数据
douban_years = list(douban['year_distribution'].items())
bili_anime = [b for b in bili['status_summary'].keys() if b.startswith('anime')]
bili_drama = [b for b in bili['status_summary'].keys() if b.startswith('drama')]

# 状态统计
status_map = {'watched': '看过', 'watching': '在看', 'on_hold': '搁置'}
anime_watched = sum(1 for t, s in [(t, s) for t, s in status_map if f"anime_{s}" in bili['status_summary']])
anime_total = summary['bilibili_anime']
anime_rate = f"{anime_watched/anime_total*100:.0f}%" if anime_total else "0%"

# 歌手统计
top_artists = list(netease['top_artists'].items())[:10]
top_songs = netease['top_songs'][:10]

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的媒体档案画像</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(90deg, #0f3460, #e94560);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-card .label {{
            color: #888;
            margin-top: 5px;
        }}
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{
            font-size: 1.5em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
            margin-bottom: 20px;
        }}
        .list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
        }}
        .list-item {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            font-size: 0.9em;
        }}
        .list-item .count {{
            color: #e94560;
            font-weight: bold;
        }}
        .top-list {{
            counter-reset: top;
        }}
        .top-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        .top-item .rank {{
            width: 30px;
            height: 30px;
            background: #e94560;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }}
        .top-item .info {{
            flex: 1;
        }}
        .top-item .info .name {{
            font-weight: 500;
        }}
        .top-item .info .meta {{
            font-size: 0.8em;
            color: #888;
        }}
        .top-item .count {{
            color: #e94560;
            font-weight: bold;
        }}
        .tag {{
            display: inline-block;
            padding: 4px 12px;
            background: rgba(233, 69, 96, 0.2);
            border-radius: 20px;
            font-size: 0.85em;
            margin: 4px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            padding: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 我的媒体档案画像</h1>
        <p class="subtitle">生成时间: {p['generated_at']}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{summary['total_records']}</div>
                <div class="label">总记录数</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['douban_movies']}</div>
                <div class="label">看过电影</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['bilibili_anime']}</div>
                <div class="label">追过番剧</div>
            </div>
            <div class="stat-card">
                <div class="number">{summary['netease_liked']}</div>
                <div class="label">喜欢歌曲</div>
            </div>
        </div>

        <div class="section">
            <h2>🎬 豆瓣电影偏好</h2>
            <div class="chart-container">
                <canvas id="doubanChart"></canvas>
            </div>
            <p><strong>观影活跃年份:</strong> {douban['year_distribution'].get('2019', 0)}部 (2019年)</p>
        </div>

        <div class="section">
            <h2>📺 B站追番/剧状态</h2>
            <div class="chart-container">
                <canvas id="bilibiliChart"></canvas>
            </div>
            <div style="margin-top: 20px;">
                <span class="tag">番剧完成率: {anime_rate}</span>
                <span class="tag">剧集: {summary['bilibili_drama']}部</span>
            </div>
        </div>

        <div class="section">
            <h2>🎵 网易云音乐偏好</h2>
            <div class="chart-container">
                <canvas id="artistChart"></canvas>
            </div>
            <div style="margin-top: 20px;">
                <span class="tag">音乐总时长: {netease['total_duration_hours']:.1f}小时</span>
                <span class="tag">歌手数: {len(netease['top_artists'])}位</span>
            </div>
        </div>

        <div class="section">
            <h2>🏆 Top 10 歌手</h2>
            <div class="top-list">
"""

for i, (artist, count) in enumerate(top_artists, 1):
    html += f"""                <div class="top-item">
                    <div class="rank">{i}</div>
                    <div class="info">
                        <div class="name">{artist}</div>
                    </div>
                    <div class="count">{count}首</div>
                </div>
"""

html += """            </div>
        </div>

        <div class="section">
            <h2>🎧 最常听歌曲 (Top 10)</h2>
            <div class="top-list">
"""

for i, song in enumerate(top_songs, 1):
    html += f"""                <div class="top-item">
                    <div class="rank">{i}</div>
                    <div class="info">
                        <div class="name">{song['title']}</div>
                        <div class="meta">{song.get('artists', '')}</div>
                    </div>
                    <div class="count">{song.get('play_count', 0)}次</div>
                </div>
"""

html += """            </div>
        </div>

        <div class="section">
            <h2>📋 最近观看</h2>
            <div class="list">
"""

for movie in douban['recent_movies'][:10]:
    html += f"""                <div class="list-item">{movie['title']}<br><small>{movie['date']}</small></div>
"""

html += """            </div>
        </div>

        <div class="footer">
            <p>数据来源: media-archive 项目 | 仅供个人使用</p>
        </div>
    </div>

    <script>
        // 豆瓣年份分布
        new Chart(document.getElementById('doubanChart'), {
            type: 'bar',
            data: {
                labels: {json.dumps(list(douban['year_distribution'].keys()))},
                datasets: [{
                    label: '观看数量',
                    data: {json.dumps(list(douban['year_distribution'].values()))},
                    backgroundColor: 'rgba(233, 69, 96, 0.7)',
                    borderColor: 'rgba(233, 69, 96, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    x: { ticks: { color: '#888' }, grid: { display: false } }
                }
            }
        });

        // B站状态分布
        new Chart(document.getElementById('bilibiliChart'), {
            type: 'doughnut',
            data: {
                labels: {json.dumps(list(bili['status_summary'].keys()))},
                datasets: [{
                    data: {json.dumps(list(bili['status_summary'].values()))},
                    backgroundColor: ['#e94560', '#0f3460', '#533483', '#16213e', '#e94560', '#0f3460']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right', labels: { color: '#eee' } } }
            }
        });

        // 歌手分布
        new Chart(document.getElementById('artistChart'), {
            type: 'bar',
            data: {
                labels: {json.dumps(list(netease['top_artists'].keys())[:10])},
                datasets: [{
                    label: '歌曲数',
                    data: {json.dumps(list(netease['top_artists'].values())[:10])},
                    backgroundColor: 'rgba(83, 52, 131, 0.7)',
                    borderColor: 'rgba(83, 52, 131, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#eee' }, grid: { display: false } }
                }
            }
        });
    </script>
</body>
</html>
"""

# 保存 HTML
output_path = OUTPUT_DIR / "media_profile.html"
output_path.write_text(html, encoding="utf-8")
print(f"画像报表已生成: {output_path}")
print(f"  总记录: {summary['total_records']}")
print(f"  豆瓣电影: {summary['douban_movies']}部")
print(f"  B站番剧: {summary['bilibili_anime']}部")
print(f"  网易云歌曲: {summary['netease_liked']}首")
