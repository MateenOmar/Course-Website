import sqlite3
from flask import Flask, render_template, request, g, redirect, session, url_for, escape, flash

DATABASE = './assignment3.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args = (), one = False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

app = Flask(__name__)

app.secret_key = b'key'

user_position = ""
current_user = ""

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def loginPage():
    if 'userName' in session:
        return redirect(url_for('home'))

    return render_template("login.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    global user_position
    global current_user

    uname = request.form['username']
    password = request.form['pass']

    user = query_db('select * from students where userName=?', [uname], one = True)
    user2 = query_db('select * from instructors where userName=?', [uname], one = True)

    if request.method == 'POST':
        if(user is not None and user[0] == uname and user[1] == password):
            session['userName'] = uname
            user_position = "students"
            current_user = uname
            return redirect(url_for('home'))

        elif(user2 is not None and user2[0] == uname and user2[1] == password):
            session['userName'] = uname
            user_position = "instructors"
            current_user = uname
            return redirect(url_for('home'))

        flash("Incorrect login credentials")

    else:
        return redirect(url_for('login'))

    return redirect(url_for('loginPage'))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    global user_position
    global current_user

    uname = request.form['username']
    password = request.form['pass']
    email = request.form['email']
    position = request.form['positions']

    usernames = query_db("select userName from " + position, args=(), one=False)
    for name in usernames:
        if name[0] == uname:
            flash("This username is already taken")
            return redirect(url_for('registerPage'))

    if request.method == 'POST':

        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO " + position + " (userName, password, email) VALUES (?,?,?)",(uname, password, email))

            if(position == "students"):
                cur.execute("INSERT INTO marks (userName) VALUES (?)", [uname])

            con.commit()
            user_position = position
            current_user = uname
            session['userName'] = uname
            return render_template("home.html", name = user_position)

@app.route("/feedbackInput", methods=['POST'])
def feedbackInput():
    instructor = request.form['instructor']
    f1 = request.form['f1']
    f2 = request.form['f2']
    f3 = request.form['f3']
    f4 = request.form['f4']

    if request.method == 'POST':

        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO feedback (userName, f1, f2, f3, f4) VALUES (?,?,?,?,?)",(instructor, f1, f2, f3, f4))
            con.commit()
            flash("Your feedback has been submitted")

            return redirect(url_for('feedback'))


@app.route('/logout')
def logout():
    session.pop('userName', None)
    user_position = ""
    current_user = ""
    return redirect(url_for('loginPage'))

@app.route("/register")
def registerPage():
    return render_template("register.html")

@app.route("/home")
def home():
    if 'userName' in session:
        return render_template("home.html", name = user_position)

    return redirect(url_for('loginPage'))

@app.route("/courseTeam")
def courseTeam():
    if 'userName' in session:
        return render_template("courseTeam.html", name = user_position)

    return redirect(url_for('loginPage'))

@app.route("/syllabus")
def syllabus():
    if 'userName' in session:
        return render_template("syllabus.html", name = user_position)

    return redirect(url_for('loginPage'))

@app.route("/lectures")
def lectures():
    if 'userName' in session:
        return render_template("lectures.html", name = user_position)

    return redirect(url_for('loginPage'))

@app.route("/labs")
def labs():
    if 'userName' in session:
        return render_template("labs.html", name = user_position)

    return redirect(url_for('loginPage'))

@app.route("/assignments")
def assignments():
    if 'userName' in session:
        return render_template("assignments.html", name = user_position)

    return redirect(url_for('loginPage'))

@app.route("/mygrades")
def grades():
    userData = query_db('select * from marks where userName=?', [current_user], one = True)

    return render_template('grades.html', name = user_position,  user = current_user, studentGrades = userData)

@app.route("/gradesall")
def gradesall():
    studentList=[]
    for user in query_db('select * from marks'):
        studentList.append(user)

    return render_template("gradesall.html", name = user_position, students = studentList)

@app.route("/editgrades")
def editgrades():
    if 'userName' in session:
        return render_template("editgrades.html", name = user_position)
    return redirect(url_for('loginPage'))

@app.route("/remarkRequests")
def remarkRequests():
    remarksList=[]
    for user in query_db('select * from remarks'):
        remarksList.append(user)

    return render_template("remarkRequests.html", name = user_position, requests = remarksList)

@app.route("/feedback")
def feedback():
    if 'userName' in session:
        db=get_db()
        db.row_factory=make_dicts

        instructorsUsersIDs=[]
        for users in query_db('select * from instructors'):
            instructorsUsersIDs.append(users)
        return render_template("feedback.html", name = user_position, instructors=instructorsUsersIDs)

    return redirect(url_for('loginPage'))

@app.route("/myFeedback")
def myFeedback():
    if 'userName' in session:
        db=get_db()
        db.row_factory=make_dicts

        feedbacks=[]
        for feedback in query_db('select * from feedback where userName=?', [current_user]):
            feedbacks.append(feedback)
        return render_template("myFeedback.html", name = user_position, user = current_user ,feedbacks=feedbacks)

    return redirect(url_for('loginPage'))

@app.route("/remarkA1", methods=['GET', 'POST'])
def remarkA1():
    req = request.form['remark-a1']
    user = query_db('select * from remarks where userName=?', [current_user], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None and user[0] == current_user):
                cur.execute("UPDATE remarks SET a1=? where userName=?", [req, current_user])
                con.commit()
            else:
                cur.execute("INSERT INTO remarks (userName, a1) VALUES (?, ?)",(current_user, req))
                con.commit()
            flash("Your remark request for A1 has been submitted")

            return redirect(url_for('grades'))
    
@app.route("/remarkQ1", methods=['GET', 'POST'])
def remarkQ1():
    req = request.form['remark-q1']
    user = query_db('select * from remarks where userName=?', [current_user], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None and user[0] == current_user):
                cur.execute("UPDATE remarks SET q1=? where userName=?", [req, current_user])
                con.commit()
            else:
                cur.execute("INSERT INTO remarks (userName, q1) VALUES (?, ?)", (current_user, req))
                con.commit()
            flash("Your remark request for Q1 has been submitted")

            return redirect(url_for('grades'))

@app.route("/remarkA2", methods=['GET', 'POST'])
def remarkA2():
    req = request.form['remark-a2']
    user = query_db('select * from remarks where userName=?', [current_user], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None and user[0] == current_user):
                cur.execute("UPDATE remarks SET a2=? where userName=?", [req, current_user])
                con.commit()
            else:
                cur.execute("INSERT INTO remarks (userName, a2) VALUES (?, ?)",(current_user, req))
                con.commit()
            flash("Your remark request for A2 has been submitted")

            return redirect(url_for('grades'))

@app.route("/remarkQ2", methods=['GET', 'POST'])
def remarkQ2():
    req = request.form['remark-q2']
    user = query_db('select * from remarks where userName=?', [current_user], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None and user[0] == current_user):
                cur.execute("UPDATE remarks SET q2=? where userName=?", [req, current_user])
                con.commit()
            else:
                cur.execute("INSERT INTO remarks (userName, q2) VALUES (?, ?)",(current_user, req))
                con.commit()
            flash("Your remark request for Q2 has been submitted")

            return redirect(url_for('grades'))

@app.route("/remarkMidterm", methods=['GET', 'POST'])
def remarkMidterm():
    req = request.form['remark-midterm']
    user = query_db('select * from remarks where userName=?', [current_user], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None and user[0] == current_user):
                cur.execute("UPDATE remarks SET Midterm=? where userName=?", [req, current_user])
                con.commit()
            else:
                cur.execute("INSERT INTO remarks (userName, Midterm) VALUES (?, ?)",(current_user, req))
                con.commit()
            flash("Your remark request for Midterm has been submitted")

            return redirect(url_for('grades'))

@app.route("/remarkFinal", methods=['GET', 'POST'])
def remarkFinal():
    req = request.form['remark-final']
    user = query_db('select * from remarks where userName=?', [current_user], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None and user[0] == current_user):
                cur.execute("UPDATE remarks SET Final=? where userName=?", [req, current_user])
                con.commit()
            else:
                cur.execute("INSERT INTO remarks (userName, Final) VALUES (?, ?)",(current_user, req))
                con.commit()
            flash("Your remark request for Final has been submitted")

            return redirect(url_for('grades'))

@app.route("/editA1", methods=['GET', 'POST'])
def editA1():
    uname = request.form['username']
    mark = request.form['mark']
    user = query_db('select * from marks where userName=?', [uname], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None):
                cur.execute("UPDATE marks SET a1=? where userName=?", [mark, uname])
                con.commit()
                flash("A1 mark updated for " + uname)
            else:
                flash(uname + " does not exist, please enter a valid student username")

            return redirect(url_for('editgrades'))

@app.route("/editQ1", methods=['GET', 'POST'])
def editQ1():
    uname = request.form['username']
    mark = request.form['mark']
    user = query_db('select * from marks where userName=?', [uname], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None):
                cur.execute("UPDATE marks SET q1=? where userName=?", [mark, uname])
                con.commit()
                flash("Q1 mark updated for " + uname)
            else:
                flash(uname + " does not exist, please enter a valid student username")

            return redirect(url_for('editgrades'))

@app.route("/editA2", methods=['GET', 'POST'])
def editA2():
    uname = request.form['username']
    mark = request.form['mark']
    user = query_db('select * from marks where userName=?', [uname], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None):
                cur.execute("UPDATE marks SET a2=? where userName=?", [mark, uname])
                con.commit()
                flash("A2 mark updated for " + uname)
            else:
                flash(uname + " does not exist, please enter a valid student username")

            return redirect(url_for('editgrades'))

@app.route("/editQ2", methods=['GET', 'POST'])
def editQ2():
    uname = request.form['username']
    mark = request.form['mark']
    user = query_db('select * from marks where userName=?', [uname], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None):
                cur.execute("UPDATE marks SET q2=? where userName=?", [mark, uname])
                con.commit()
                flash("Q2 mark updated for " + uname)
            else:
                flash(uname + " does not exist, please enter a valid student username")

            return redirect(url_for('editgrades'))

@app.route("/editMidterm", methods=['GET', 'POST'])
def editMidterm():
    uname = request.form['username']
    mark = request.form['mark']
    user = query_db('select * from marks where userName=?', [uname], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None):
                cur.execute("UPDATE marks SET Midterm=? where userName=?", [mark, uname])
                con.commit()
                flash("Midterm mark updated for " + uname)
            else:
                flash(uname + " does not exist, please enter a valid student username")

            return redirect(url_for('editgrades'))

@app.route("/editFinal", methods=['GET', 'POST'])
def editFinal():
    uname = request.form['username']
    mark = request.form['mark']
    user = query_db('select * from marks where userName=?', [uname], one = True)

    if request.method == 'POST':
        with sqlite3.connect("assignment3.db") as con:
            cur = con.cursor()
            if(user is not None):
                cur.execute("UPDATE marks SET Final=? where userName=?", [mark, uname])
                con.commit()
                flash("Final mark updated for " + uname)
            else:
                flash(uname + " does not exist, please enter a valid student username")

            return redirect(url_for('editgrades'))

@app.route("/<name>")
def error(name):
    return "ERROR: Incorrect page COMPUTER SCIENCETEST"

if __name__ == "__main__":
    app.run(debug=True)