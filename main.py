from flask import Flask, session, redirect, url_for, escape, request, render_template, url_for, send_from_directory
import hashlib, time, json, datetime, pycurl, os
from hashlib import md5
import MySQLdb
from nutritionix import Nutritionix
from clarifai.client import ClarifaiApi
from werkzeug import secure_filename
from imgurpython import ImgurClient
from datetime import date, timedelta
import pprint
from io import BytesIO
from cStringIO import StringIO
import sys
from colour import Color


nix = Nutritionix(app_id="", api_key="")

app = Flask(__name__)


#######################
#   DATABASE CONFIG   #
#######################

db = MySQLdb.connect(host="", user="", passwd="", db="")
cur = db.cursor()


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
    
    

@app.route('/')
def index():
    if 'username' in session:
        
        #testing api
        
        
        
        date = (time.strftime("%Y-%m-%d"))
        userx = session['username']
        eaten = {'red': '', 'orange': '', 'yellow':'', 'white':'', 'green':'','blue':'','purple':''};
        #eaten["red"] = "eaten"
        #print eaten
        cur.execute("SELECT color FROM eats WHERE time = %s AND email = %s", [date, userx])
        for row in cur.fetchall():
            if row[0] == "red":
                eaten["red"] = "eaten"
            if row[0] == "orange":
                eaten["orange"] = "eaten"
            if row[0] == "yellow":
                eaten["yellow"] = "eaten"
            if row[0] == "white":
                eaten["white"] = "eaten"
            if row[0] == "green":
                eaten["green"] = "eaten"
            if row[0] == "blue":
                eaten["blue"] = "eaten"
            if row[0] == "purple":
                eaten["purple"] = "eaten"  
        print eaten
        
        check = True
        count = 0
        count2 = 1
        
        while check:
            todayx = datetime.datetime.now()
            DDx = datetime.timedelta(days=count2)
            earlierx = todayx - DDx
	    print earlierx
            earlier_strx = earlierx.strftime("%Y-%m-%d")
            sdatex = str(earlier_strx)
            count2 = count2 + 1
            
   
            cur.execute('SELECT time, COUNT(time) FROM eats WHERE email = %s AND time = %s GROUP BY time;',[session['username'],sdatex])
            if cur.rowcount != 0:
                for row in cur.fetchall():
                    if(row[1] == 7):
                        count = count +1
                    else:
                        check = False
            else:
		check = False 
                        
        print count
        
        username_session = escape(session['username']).capitalize()
        return render_template('index.html', session_user_name=username_session, eaten = eaten, count = count)
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form['submit'] == "Login":
            print request.form['submit']
            username_form  = request.form['username']
            password_form  = request.form['password']
            cur.execute("SELECT COUNT(1) FROM users WHERE email = %s;", [username_form]) # CHECKS IF USERNAME EXSIST
            if cur.fetchone()[0]:
                cur.execute("SELECT password FROM users WHERE email = %s;", [username_form]) # FETCH THE HASHED PASSWORD
                for row in cur.fetchall():
                    if md5(password_form).hexdigest() == row[0]:
                        session['username'] = request.form['username']
                        return redirect(url_for('index'))
                    else:
                        error = "Invalid Credential"
            else:
                error = "Invalid Credential"
        elif request.form['submit'] == "SignUp":
            print request.form['submit']
            username_form  = request.form['username']
            fname_form  = request.form['fname']
            password_form  = request.form['password']
            cur.execute("SELECT COUNT(1) FROM users WHERE email = %s;", [username_form]) # CHECKS IF USERNAME EXSIST
            if cur.fetchone()[0]:
                error = "Username exists"
            else:
                #key_string = raw_input()
                passwrd = hashlib.md5( password_form ).hexdigest()
                print username_form
                cur.execute('''INSERT into users (email, password, fname) values (%s, %s, %s)''',(username_form, passwrd, fname_form))
                db.commit()
                error = "Sign up successful"
    return render_template('login.html', error=error)

@app.route('/nutrition')
def nutrition():
    food = request.args.get('myndata')
    print food
    results = nix.search(food, results="0:1").json()
    r1 = results['hits'][0]['_id']   
    r2 = nix.item(id=r1).json()   
    print json.dumps(r2)
    return json.dumps(r2)


@app.route('/history')
def history():
    

    
    today = datetime.datetime.now()
    DD = datetime.timedelta(days=7)
    earlier = today - DD
    earlier_str = earlier.strftime("%Y-%m-%d")
    
    tdate = (time.strftime("%Y-%m-%d"))
    
    #print str(earlier_str)
    
    sdate = str(earlier_str)
    
   
   
    
    cur.execute('SELECT time, COUNT(time) FROM eats WHERE email = %s AND time between %s and %s GROUP BY time;',[session['username'],sdate, tdate])
    #cur1.execute('SELECT time FROM eats WHERE email = %s AND time between %s and %s;',[session['username'],sdate, tdate])
    
    streak = {}
    for row in cur.fetchall():
        #print row
        streak[str(row[0])] = str(row[1])
    #print streak
    
    streak2 = {}
    for x in range (0,7):
        #streak2={}
        todayx = datetime.datetime.now()
        DDx = datetime.timedelta(days=x)
        earlierx = todayx - DDx
        earlier_strx = earlierx.strftime("%Y-%m-%d")
        sdatex = str(earlier_strx)
        cur.execute('SELECT time, color FROM eats WHERE email = %s AND time = %s;',[session['username'],sdatex])
        if cur.rowcount != 0:
            colorlist = []
            for row1 in cur.fetchall():
                if str(row1[0]) == sdatex:
                    colorlist.append(row1[1])
            streak2[sdatex] = colorlist
    streakab =  {'1': streak, '2': streak2}       
    #streaka = json.dumps(streak)
    #streakb = json.dumps(streak2)
    #streakab {'1': streaka, '2': streakb}
           
    return json.dumps(streakab)



# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        
            
        
        return redirect(url_for('uploaded_file',
                                filename=filename))
    
    
@app.route('/share')
def share():
     date = (time.strftime("%Y-%m-%d"))
     userx = session['username']
     cur.execute("SELECT color FROM eats WHERE time = %s AND email = %s", [date, userx])
     num = 0 
     for row in cur.fetchall():
         if row[0] == "red":
                num = num + 1
         if row[0] == "orange":
                num = num + 1
         if row[0] == "yellow":
                num = num + 1
         if row[0] == "white":
                num = num + 1
         if row[0] == "green":
                num = num + 1
         if row[0] == "blue":
                num = num + 1
         if row[0] == "purple":
                num = num + 1
     return json.dumps(num)
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    send_from_directory(app.config['UPLOAD_FOLDER'],filename)
    client_id = ''
    client_secret = ''
    client = ImgurClient(client_id, client_secret)
    path = 'uploads/' + str(filename)
    piclink = client.upload_from_path(path, config=None, anon=True)
    piclinkx = piclink['link']
    #print piclinkx
    
    clarifai_api = ClarifaiApi()  # assumes environment variables are set.
        #result = clarifai_api.tag_image_urls('https://api.clarifai.com/v1/color/?url=https://samples.clarifai.com/metro-north.jpg')
        
        #print json.dumps(result)
        
    storage = StringIO()
    github_url = 'https://api.clarifai.com/v1/color'
    c = pycurl.Curl()
    c.setopt(pycurl.URL, github_url)
    c.setopt(pycurl.HTTPHEADER, ['Authorization: Bearer '])
    c.setopt(pycurl.POST, 1)
    
    data = "url=" + str(piclinkx)
    c.setopt(pycurl.POSTFIELDS, data)
    c.setopt(c.WRITEFUNCTION, storage.write)
    #c.setopt(pycurl.WRITEDATA, buffer)
    #c.setopt(pycurl.WRITEFUNCTION, data.write)
    c.perform()
    content = storage.getvalue()
    a = eval(content)
    print a
    colname = a['results'][0]['colors'][0]['w3c']['name']
    
    colname = colname.lower()
    color = ""
    
    if "green" in colname or "olive" in colname:
        color = "green"
    elif "red" in colname or "maroon" in colname or "fire" in colname or "tomato" in colname or "pink" in colname or "brown" in colname:
         color = "red"
    elif "blue" in colname or "turquoise" in colname:
         color = "blue"
    elif "yellow" in colname or "khaki" in colname:
         color = "yellow"
    elif "orange" in colname or "chocolate" in colname or "salmon" in colname:
         color = "orange"
    elif "purple" in colname or "violet" in colname or "chid" in colname or "magenta" in colname:
        color = "purple"
    elif "white" in colname or "beige" in colname:
         color = "orange"
    else:
        color = "FALSE"
        
    print color
    
    if 'username' in session:
        userx = session['username']
        date = (time.strftime("%Y-%m-%d"))
        print date
        cur.execute("SELECT color FROM eats WHERE time = %s AND email = %s AND color = %s", [date, userx, color])
        if cur.rowcount == 0:    
            cur.execute('''INSERT into eats (email, color, time) values (%s, %s, %s)''',(userx, color,date))
            db.commit()
            return redirect(url_for('index'))
        else:
            return "False"

    
    #print type(mystdout)
    #print mystdout
    
   
    
    
    #print data
    #dictionary = json.loads(c.getvalue())
    #pprint.pprint(dictionary["colors"])
    #print c
    #print json.dumps(c['colors'][0]['w3c']['hex'])
    
    
                                                   
@app.route('/deletex')
def deletex():
    if 'username' in session:
        userx = session['username']
        date = (time.strftime("%Y-%m-%d"))
        color = request.args.get('myxdata')
        cur.execute("DELETE FROM eats WHERE time = %s AND email = %s AND color = %s", [date, userx, color])
        db.commit()
        
    state = "deleted" + color
    return state
    
        

@app.route('/insertcolor')
def insertcolor():
    if 'username' in session:
        color = request.args.get('myfdata')
	 
        userx = session['username']
        date = (time.strftime("%Y-%m-%d"))
        print date
        cur.execute("SELECT color FROM eats WHERE time = %s AND email = %s AND color = %s", [date, userx, color])
        if cur.rowcount == 0:    
            cur.execute('''INSERT into eats (email, color, time) values (%s, %s, %s)''',(userx, color,date))
            db.commit()
            cur.execute("SELECT color FROM eats WHERE time = %s AND email = %s", [date, userx])
            eaten2 = {"red": "", "orange": "", "yellow":"", "white":"", "green":"","blue":"","purple":""};
            for row in cur.fetchall():
                if row[0] == "red":
                    eaten2["red"] = "eaten"
                if row[0] == "orange":
                    eaten2["orange"] = "eaten"
                if row[0] == "yellow":
                    eaten2["yellow"] = "eaten"
                if row[0] == "white":
                    eaten2["white"] = "eaten"
                if row[0] == "green":
                    eaten2["green"] = "eaten"
                if row[0] == "blue":
                    eaten2["blue"] = "eaten"
                if row[0] == "purple":
                    eaten2["purple"] = "eaten" 
            return json.dumps(eaten2)   
        else:
            return "False"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

app.secret_key = ''

if __name__ == '__main__':
    app.run(host='0.0.0.0')
