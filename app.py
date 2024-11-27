from flask import Flask, render_template, request, redirect, session, flash, jsonify
from dbhelper import *

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

uploadfolder = 'static/img'
app.secret_key = '!@#$%^'
app.config['UPLOAD_FOLDER'] = uploadfolder

def get_connection():
    conn = sqlite3.connect('studentinfo.db')
    conn.row_factory = sqlite3.Row  
    return conn

@app.route("/savestudent", methods=['POST'])
def savestudent():
    idno = request.form.get('idno')
    lastname = request.form.get('lastname')
    firstname = request.form.get('firstname')
    course = request.form.get('course')
    level = request.form.get('level')
    image_file = request.files.get('imagePrev') 

    imagename = ''
    if image_file:
        filename = f'{idno}.png'
        imagename = os.path.join(uploadfolder, filename)

        try:
            image_file.save(imagename)
        except Exception as e:
            flash(f"Error saving image: {str(e)}", "error")
            return jsonify({"status": "error", "message": f"Error saving image: {str(e)}"}), 400
        
    edit_flag = request.form.get('editFlag') == 'true'

    if edit_flag:
        # Update existing student record
        ok = update_record('students', idno=idno, lastname=lastname, firstname=firstname, course=course, level=level, image=imagename)
    else:
        ok = add_record('students', idno=idno, lastname=lastname, firstname=firstname, course=course, level=level, image=imagename)

    if ok:
        flash("Student " + ("Updated" if edit_flag else "Added") + " Successfully", "success")
        return jsonify({"status": "success", "message": "Student " + ("Updated" if edit_flag else "Added")})
    else:
        flash("Error Saving Student", "error")
        return jsonify({"status": "error", "message": "Error Saving Student"}), 400

    
@app.route('/getStudentData')  #Kani nga route ako gi gamitan og jsonify para maka fetch og data sa client side katong loadStudentData nga function para ang modal mo show ang information sa gi click nga idno. pwede rasad ka mo gamit og lain nga method unsaon nimo ikaw bahal AHAHAHA
def get_student_data():
    idno = request.args.get('idno')  
    if not idno:
        return jsonify({"error": "IDNO is required"}), 400

    try:
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("SELECT idno, lastname, firstname, course, level, image FROM students WHERE idno = ?", (idno,))
        student = cursor.fetchone()

        if student:
            return jsonify({
                'idno': student['idno'],       
                'lastname': student['lastname'],
                'firstname': student['firstname'], 
                'course': student['course'],     
                'level': student['level'],       
                'image': student['image']   
            })
        else:
            return jsonify({'error': 'Student not found'}), 404

    except Exception as e:
        print(f"Error retrieving student data: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    finally:
        cursor.close()
        db.close()

@app.route("/deletestudent", methods=['GET'])
def delete_student():
    idno = request.args.get("idno")
    if idno:
        student = get_student_by_id(idno)
        if student:
            imagename = student['image'] 
            if imagename and os.path.exists(imagename): 
                try:
                    os.remove(imagename)   #kani mao ni ang mo remove sa picture sa imong staic/img/ sample.png 
                except Exception as e:
                    flash(f"Error deleting image: {str(e)}", 'error')

            if delete_student_record(idno):
                flash("Student successfully deleted!", "success")
            else:
                flash("Failed to delete student or student not found.", "error")
        else:
            flash("Student not found or image missing.", "error")
    else:
        flash("Student ID is missing.", "error")
    
    return redirect("/studentlist") 

@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache,no-store,must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/userlogin", methods=['POST'])
def user_login_view() -> None:
    username: str = request.form['username']
    password: str = request.form['password']
    print(f"Login attempt - Username: {username}, Password: {password}")

    if user_login(username, password): 
        session['name'] = username
        print(f"User {username} logged in successfully.")
        return redirect('/studentlist')
    else:
        print(f"Login failed for username: {username}")
        return redirect('/')

@app.route("/logout")
def logout():
    print("User logged out.")
    session.pop("name", None) 
    return redirect("/")

@app.route("/studentlist")
def student_list() -> None:
    if not session.get("name"):
        print("No user session found, redirecting to login.")
        return redirect("/")
    else:
        print("Displaying student list.")
        return render_template("index.html", data=get_all_students(), pagetitle="STUDENT LIST")

@app.route("/")
def index() -> None:
    print("Rendering login page.")
    return render_template("login.html", pagetitle="USER LOGIN")

if __name__ == "__main__":
    app.run(debug=True) 
