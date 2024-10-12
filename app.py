from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
from math import ceil

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于flash消息

class MusicLibrary:
    def __init__(self):
        self.library = []
        self.playlists = []
        self.filename = "music_library.json"
        self.playlist_filename = "playlists.json"
        self.load_library()
        self.load_playlists()

    def load_library(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as file:
                self.library = json.load(file)
        else:
            self.library = [
                {"title": "春天里", "download_link": "#", "downloads": 10000},
                {"title": "夜空中最亮的星", "download_link": "#", "downloads": 9500},
                {"title": "天空之城", "download_link": "#", "downloads": 9000},
                {"title": "红豆", "download_link": "#", "downloads": 8500},
                {"title": "青花瓷", "download_link": "#", "downloads": 8000},
            ]
            self.save_library()

    def load_playlists(self):
        if os.path.exists(self.playlist_filename):
            with open(self.playlist_filename, 'r', encoding='utf-8') as file:
                self.playlists = json.load(file)
        else:
            self.playlists = [
                {
                    "id": 1,
                    "title": "经典华语",
                    "cover": "/static/images/playlist1.jpg",
                    "songs": ["春天里", "夜空中最亮的星", "红豆"],
                    "download_link": "https://example.com/download/playlist1"
                },
                {
                    "id": 2,
                    "title": "轻音乐",
                    "cover": "/static/images/playlist2.jpg",
                    "songs": ["天空之城"],
                    "download_link": "https://example.com/download/playlist2"
                },
                {
                    "id": 3,
                    "title": "流行金曲",
                    "cover": "/static/images/playlist3.jpg",
                    "songs": ["青花瓷"],
                    "download_link": "https://example.com/download/playlist3"
                }
            ]
            self.save_playlists()

    def save_library(self):
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.library, file, ensure_ascii=False, indent=4)

    def save_playlists(self):
        with open(self.playlist_filename, 'w', encoding='utf-8') as file:
            json.dump(self.playlists, file, ensure_ascii=False, indent=4)

    def add_song(self, title, download_link):
        song = {"title": title, "download_link": download_link, "downloads": 0}
        self.library.append(song)
        self.save_library()

    def search_songs(self, keyword):
        return [song for song in self.library if keyword.lower() in song['title'].lower()]

    def get_hot_songs(self, limit=5):
        return sorted(self.library, key=lambda x: x['downloads'], reverse=True)[:limit]

    def get_playlist(self, playlist_id):
        return next((playlist for playlist in self.playlists if playlist['id'] == playlist_id), None)

    def get_playlist_songs(self, playlist, search_term=''):
        if search_term:
            return [song for song in playlist['songs'] if search_term.lower() in song.lower()]
        return playlist['songs']

    def increment_downloads(self, title):
        for song in self.library:
            if song['title'] == title:
                song['downloads'] += 1
                self.save_library()
                return True
        return False

    def get_top_songs(self, limit=10):
        return sorted(self.library, key=lambda x: x['downloads'], reverse=True)[:limit]

library = MusicLibrary()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    total_songs = len(library.library)
    total_pages = ceil(total_songs / per_page)
    songs = library.library[(page-1)*per_page:page*per_page]
    hot_songs = library.get_hot_songs()
    playlists = library.playlists
    return render_template('index.html', songs=songs, hot_songs=hot_songs, page=page, total_pages=total_pages, playlists=playlists)

@app.route('/add', methods=['POST'])
def add_song():
    title = request.form['title']
    download_link = request.form['download_link']
    library.add_song(title, download_link)
    flash(f'已成功添加歌曲: {title}')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_results = library.search_songs(keyword)
    total_results = len(search_results)
    total_pages = ceil(total_results / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = search_results[start:end]
    hot_songs = library.get_hot_songs()
    playlists = library.playlists
    return render_template('search_results.html', songs=paginated_results, keyword=keyword, 
                           page=page, total_pages=total_pages, hot_songs=hot_songs, 
                           playlists=playlists)

@app.route('/playlist/<int:playlist_id>')
def playlist(playlist_id):
    playlist = library.get_playlist(playlist_id)
    if playlist:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        per_page = 10
        all_songs = library.get_playlist_songs(playlist, search)
        total_songs = len(all_songs)
        total_pages = ceil(total_songs / per_page)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_songs = all_songs[start:end]
        hot_songs = library.get_hot_songs()
        playlists = library.playlists
        return render_template('playlist.html', playlist=playlist, paginated_songs=paginated_songs, 
                               hot_songs=hot_songs, playlists=playlists, page=page, 
                               total_pages=total_pages, search=search)
    return "歌单不存在", 404

@app.route('/download_playlist/<int:playlist_id>')
def download_playlist(playlist_id):
    playlist = library.get_playlist(playlist_id)
    if playlist:
        return redirect(playlist['download_link'])
    return "歌单不存在", 404

@app.route('/increment_downloads', methods=['POST'])
def increment_downloads():
    data = request.json
    title = data.get('title')
    if library.increment_downloads(title):
        return jsonify({"success": True, "message": f"Incremented downloads for {title}"})
    return jsonify({"success": False, "message": "Song not found"}), 404

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

@app.route('/get_chart_data')
def get_chart_data():
    top_songs = library.get_top_songs(10)  # 获取前10首热门歌曲
    chart_data = [{"value": song['downloads'], "name": song['title']} for song in top_songs]
    return jsonify(chart_data)

if __name__ == '__main__':
    app.run(debug=True)