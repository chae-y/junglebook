from pymongo import MongoClient
import bcrypt
from flask import Flask, request, render_template, jsonify, url_for, redirect, session
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

            if bcrypt.checkpw(pw.encode('utf-8'), pw_check):
                session["id"] = id_val
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
        return render_template('main.html', userid=id)
    else:
        return redirect(url_for("/"))


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
