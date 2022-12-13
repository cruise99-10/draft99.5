## 아래 주석 처리한 공간에서 본인이 필요한 기능의 코드를 작성해주시면 됩니다.
## HTML 파일은 작업 중간중간 아무 때나 커밋하셔도 상관 없습니다.
## Python 파일은 추후 정해진 시간에 각각 순차적으로 업로드할 예정입니다.


# Packages
## 이 곳에서'만' 패키지를 받아옵니다.
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)

from pymongo import MongoClient
import certifi
import jwt
from bs4 import BeautifulSoup
import datetime
import hashlib
import requests
ca = certifi.where()
# client = MongoClient("mongodb+srv://sparta:test@cluster0.xskerwx.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
client = MongoClient("mongodb+srv://test:sparta@cluster0.jxtcbsj.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = client.dbdraft99
SECRET_KEY = 'SPARTA'

# login (상휘)


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=20)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# join (상휘)


@app.route('/join')
def join():
    return render_template('join.html')


# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/join', methods=['POST'])
def api_join():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success'})

# main (상휘)


@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')

    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        return jsonify({'result': 'success','id':userinfo['id'], 'nickname': userinfo['nick']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        # print('nono')
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
        # print('nono?')
    except jwt.exceptions.DecodeError:
        # print("nonono")
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})


@app.route('/')
def home():
    # print("hi")
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        # print("hi again")
        return render_template('main.html', nickname=user_info["nick"])

    except jwt.ExpiredSignatureError:
        # print("hihihihihihi")
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# review (정기)


@app.route('/write')
def writing():
    return render_template('review.html')


@app.route("/write", methods=["POST"])
def posting():
    url_receive = request.form['url_give']
    reviewcomment_receive = request.form['reviewcomment_give']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    title = soup.select_one('meta[property="og:title"]')['content']
    image = soup.select_one('meta[property="og:image"]')['content']
    desc = soup.select_one('meta[property="og:description"]')['content']

    doc ={
        'title':title,
        'image':image,
        'desc':desc,
        'reviewcomment':reviewcomment_receive
    }
    # print('Hi')
    print(headers)
    db.reviews.insert_one(doc)

    return jsonify({'msg':'저장 완료!'})


# commentList (지영)
@app.route("/")
def comment():
    return render_template('community.html')

@app.route("/comment/show", methods=["GET"])
def comment_show():
    comment_list = list(db.comment.find({},{'_id':False}))
    return jsonify({'comments':comment_list})


@app.route("/ddd/write", methods=["POST"]) # id, comment
def comment_save():
    comment_receive = request.form["comment_give"]

    # count = db.bucket.insert_one({}, {'_id': False})
    # num = len(count) + 1

    doc = {
        # 'num': num,
        'comment': comment_receive,
       # 'like': 0
    }

    db.comment.insert_one(doc)
    return jsonify({'msg': '댓글 등록 완료!'})


# myPage (경은)


@app.route('/myPage')
def mypage():
    return render_template('myPage.html')


@app.route("/a/myPage", methods=["GET"])
def mypage_get():
    mypagelist = list(db.reviews.find({}, {'_id': False}))
    return jsonify({'mypage': mypagelist})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)