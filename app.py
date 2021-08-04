from pymongo import MongoClient
import bcrypt
from flask import Flask, request, render_template, jsonify, url_for, redirect, session

from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from requests.exceptions import MissingSchema, InvalidURL

app = Flask(__name__)
app.secret_key = 'jungle_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'


# MongoDB 세팅
client = MongoClient('localhost', 27017)
db = client.dbtest1


# 로그인 화면
@app.route('/', methods=['POST', 'GET'])
def signin():

    if "id" in session:
        return redirect(url_for("main"))

    if request.method == "POST":
        id = request.form['id_give']
        pw = request.form['pw_give']

        id_found = db.user_info.find_one({'id': id})

        if id_found:
            id_val = id_found['id']
            pw_check = id_found['password']
            nickname = id_found['nickname']

            if bcrypt.checkpw(pw.encode('utf-8'), pw_check):
                session["id"] = id_val
                session["nickname"] = nickname

                return jsonify({'status': 'signedin'})
            else:
                if "id" in session:
                    return redirect(url_for("main"))

                # 비밀번호가 안 맞는 경우
                return jsonify({'status': 'pwwrong'})
        else:
            return jsonify({'status': 'idnotfound'})

    return render_template("signin.html")


# 메인 화면
@app.route('/main')
def main():
    if "id" in session:
        id = session["id"]
        nickname = session["nickname"]
        
        now = datetime.now()
        bookmarks= list(db.bookmarks.find( {'id':id} , {'_id':False}))
        day=timedelta(hours=24)
        bookmarks.sort(key=lambda bm: ((now-bm['now'])> day ,bm['star']==False, -bm['click']))
        
        return render_template('main.html', user_id=id, user_nickname=nickname, bookmarks_list=bookmarks)
    else:
        return redirect(url_for("signin"))

# 북마크 추가


@app.route('/main/post', methods=['POST'])
def post_bookmark():

    # id, 등록시간, url, 메타태그 타이틀, 메타태그 이미지, 클릭수, 중요
    url_receive = request.form['url_give']
    id_receive = request.form['id_give']

    if db.bookmarks.find_one({'id': id_receive, 'url': url_receive}):
        return jsonify({'result': 'same'})

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    try:
        data = requests.get(url_receive, headers=headers)
    except MissingSchema:
        return jsonify({'result': 'none'})
    except InvalidURL:
        return jsonify({'result': 'none'})
    soup = BeautifulSoup(data.text, 'html.parser')

    og_image = soup.select_one('meta[property="og:image"]')
    og_title = soup.select_one('meta[property="og:title"]')

    if og_title is None:
        url_title = soup.select_one('head>title').text
    else:
        url_title = og_title['content']

    if og_image is None:
        url_image = "https://img.icons8.com/glyph-neue/64/000000/internet.png"
    else:
        url_image = og_image['content']

    now = datetime.now()

    bookmark = {
        'id': id_receive,
        'url': url_receive,
        'title': url_title,
        'image': url_image,
        'click': 0,
        'now': now,
        'star': False
    }

    db.bookmarks.insert_one(bookmark)

    return jsonify({'result': 'success'})

# 북마크 불러오기


@app.route('/main/list', methods=['GET'])
def show_bookmark():
    now = datetime.now()
    user_id = session["id"]
    bookmarks = list(db.bookmarks.find({'id': user_id}, {'_id': False}))

    day = timedelta(hours=24)

    bookmarks = sorted(bookmarks, key=lambda bm: (
        (now-bm['now']) > day, bm['star'] == False, -bm['click']))
    return jsonify({'result': 'success', 'bookmarks': bookmarks})

# 즐겨찾기의 즐겨찾기


@app.route('/main/star', methods=["POST"])
def star_bm():
    url_receive = request.form['url_give']
    id_receive = request.form['id_give']

    bookmark = db.bookmarks.find_one({'id': id_receive, 'url': url_receive})
    if not bookmark['star']:
        if len(list(db.bookmarks.find({'star': True, 'id': id_receive}, {'_id': False}))) >= 5:
            return jsonify({'result': "over"})
        else:
            new_star = True
    else:
        new_star = False

    db.bookmarks.update_one({'id': id_receive, 'url': url_receive}, {
                            '$set': {'star': new_star}})

    return jsonify({'result': 'success'})


@app.route('/main/click', methods=["POST"])
def click_bm():
    url_receive = request.form['url_give']
    id_receive = request.form['id_give']

    bookmark = db.bookmarks.find_one({'url': url_receive})
    new_click = bookmark['click']+1

    db.bookmarks.update_one({'id': id_receive, 'url': url_receive}, {
                            '$set': {'click': new_click}})

    return jsonify({'result': 'success'})


@app.route('/main/delete', methods=['POST'])
def delete_bm():
    url_receive = request.form['url_give']
    id_receive = request.form['id_give']
    db.bookmarks.delete_one({'id': id_receive, 'url': url_receive})
    return jsonify({'result': 'success'})

# 검색


@app.route('/main/list', methods=['POST'])
def find_bookmark():
    now = datetime.now()
    user_id = session["id"]
    url_receive = request.form['url_give']
    bookmarks = list(db.bookmarks.find(
        {'id': user_id, 'url': {'$regex': url_receive}}, {'_id': False}))
    day = timedelta(hours=24)

    bookmarks = sorted(bookmarks, key=lambda bm: (
        (now-bm['now']) > day, bm['star'] == False, -bm['click']))
    return jsonify({'result': 'success', 'bookmarks': bookmarks})

# 회원가입 화면


@app.route('/signup', methods=['POST', 'GET'])
def signup():

    if "id" in session:
        return redirect(url_for("main"))

    if request.method == "POST":
        userid_receive = request.form['userid_give']
        password_receive = request.form['password_give']
        nickname_receive = request.form['nickname_give']

        user_found = db.user_info.find_one({'id': userid_receive})

        if user_found:
            return jsonify({'status': '0'})
        else:
            password_hashed = bcrypt.hashpw(
                password_receive.encode('utf-8'), bcrypt.gensalt())
            userinfo = {
                'id': userid_receive,
                'password': password_hashed,
                'nickname': nickname_receive
            }
            db.user_info.insert_one(userinfo)

            return jsonify({'status': '1'})

    return render_template("signup.html")


# 로그아웃
@app.route("/signout", methods=["GET"])
def signout():
    session.pop("id", None)
    return redirect("/")


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
