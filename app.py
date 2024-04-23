from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from flask_bcrypt import Bcrypt 
from werkzeug.utils import secure_filename
import os,random,string,re,smtplib
from functools import wraps
from sqlalchemy import func
from models import db, Users, Books
from email.mime.text import MIMEText


app = Flask(__name__)



#DB Configuration

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flaskdb.db'
# Databse configuration mysql       Username:password@hostname/databasename

app.config['SECRET_KEY'] = 'abcdefgs-12@12'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/library-system'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True
   

bcrypt = Bcrypt(app) 
  
db.init_app(app)
         
with app.app_context():
    db.create_all()
 
 
app.config['UPLOAD_FOLDER'] = 'static\images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    
def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





def get_random_concerts(num_concerts):

    random_concerts = Books.query.order_by(func.rand()).limit(num_concerts).all()
  
    recommended_concerts = [
        {
            'name': concert.name,
            'image_url': concert.picture,  
           
        }
        for concert in random_concerts
    ]

    return recommended_concerts




def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if 'loggedin' in session and session['role'] == role:
                return func(*args, **kwargs)
            else:
                return redirect(url_for('home'))  
        return wrapped
    return decorator



def send_confirmation_email_registering(recipient_email, concert_name):
    try:
    
        
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_username = 'karthikalluri01@gmail.com' 
        smtp_password = 'frdtcsljvtycdaih'  


        email_body = f'Thanks for registering for the concert {concert_name}. Hope to see you there!'
        message = MIMEText(email_body)

      
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient_email, message.as_string())

        
        print(f"Confirmation email sent to {recipient_email}")

    except Exception as e:
  
        print(f"Error sending confirmation email: {str(e)}")
        


def send_email(name, sender_email, subject, message_content):
   
    user = Users.query.filter_by(name=name).first()

    if user:
        recipient_email = user.email
    else:
        recipient_email = 'nagabadda@gmail.com' 

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'karthikalluri01@gmail.com' 
    smtp_password = 'frdtcsljvtycdaih'  

  
    email_body = f"Name: {name}\nEmail: {sender_email}\nSubject: {subject}\n\nMessage:\n{message_content}"
    message = MIMEText(email_body)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipient_email, message.as_string())
        server.quit()




def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def send_password_reset_email(recipient_email, new_password):
    try:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_username = 'karthikalluri01@gmail.com'  # Replace with your Gmail username
        smtp_password = 'frdtcsljvtycdaih'  # Replace with your Gmail app password

        # Create the email message
        email_body = f'Your new password is: {new_password}'
        message = MIMEText(email_body)

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient_email, message.as_string())

        # Log the success (optional)
        print(f"Password reset email sent to {recipient_email}")

    except Exception as e:
        # Log the error (optional)
        print(f"Error sending password reset email: {str(e)}")




#Routes 


@app.route('/')
def home():
    recommended_concerts = get_random_concerts(3)

    return render_template('home.html', recommended_concerts=recommended_concerts)


@app.route('/register', methods =['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form :
        fullname = request.form['name']
        password = request.form['password']
        email = request.form['email']
         
        user_exists = Users.query.filter_by(email=email).first() is not None
       
        if user_exists:
            mesage = 'Email already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = 'Invalid email address !'
        elif not fullname or not password or not email:
            mesage = 'Please fill out the form !'
        else:
            hashed_password = bcrypt.generate_password_hash(password)
            new_user = Users(name=fullname, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            mesage = 'You have successfully registered !'
    elif request.method == 'POST':
        mesage = 'Please fill out the form !'
    return render_template('register.html', mesage = mesage)


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['loggedin'] = True
            session['userid'] = user.id
            session['name'] = user.name
            session['email'] = user.email
            session['role'] = user.role

            if user.role == 'admin':
                session['admin_loggedin'] = True
                return redirect(url_for('dashboard'))
            
            elif user.role == 'user':
                return redirect(url_for('home'))
            
        else:
            message = 'Invalid email and password'

    return render_template('login.html', message=message)




@app.route('/dashboard', methods=['GET', 'POST'])
@role_required('admin')  
def dashboard():
    
    total_concerts = Books.query.count()
    available_concerts = 100 

    return render_template("dashboard.html", total_concerts=total_concerts, available_concerts=available_concerts)


@app.route('/logout', methods=['POST'])
def logout():
    # Clear the user session
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('name', None)
    # Redirect to the main page
    return redirect(url_for('home'))


 
@app.route("/books", methods =['GET', 'POST'])
def books():
    if 'admin_loggedin' in session:
        books = Books.query.all()
        return render_template("books.html", books=books)
    return redirect(url_for('login'))



@app.route('/save_book',methods=['POST'])
def save_book():
    msg = ''    
    if 'loggedin' in session:
        if request.method == 'POST':
            name = request.form['name'] 
            isbn = request.form['isbn']  
            action = request.form['action']
 
            if action == 'updateBook':
                bookid = request.form['bookid']
                book = Books.query.get(bookid)
             
                book.name = name
                book.isbn = isbn
 
                db.session.commit()
                print("UPDATE book") 
            else:
                file = request.files['uploadFile']
                filename = secure_filename(file.filename)
                print(filename)
                if file and allowed_file(file.filename):
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filenameimage = file.filename
                    
                    book = Books(name=name, picture=filenameimage, isbn=isbn)
                    db.session.add(book)
                    db.session.commit()
 

                    print("INSERT INTO book")  
                else:
                    msg  = 'Invalid Uplaod only png, jpg, jpeg, gif'
            return redirect(url_for('books'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form !'       
        return render_template("books.html", msg = msg)
    return redirect(url_for('login'))


 
@app.route("/edit_book", methods =['GET', 'POST'])
def edit_book():
    msg = ''    
    if 'loggedin' in session:
        bookid = request.args.get('bookid')
        print(bookid)
        books = Books.query.get(bookid)
         
        return render_template("edit_books.html", books = books)
    return redirect(url_for('login'))


 
@app.route("/delete_book", methods =['GET'])
def delete_book():
    if 'loggedin' in session:
        bookid = request.args.get('bookid')
        book = Books.query.get(bookid)
        if book:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], book.picture)
            
            if os.path.exists(image_path):
                os.unlink(image_path)

            db.session.delete(book)
            db.session.commit()
        
        return redirect(url_for('books'))
    return redirect(url_for('login'))  




@app.route('/concerts')
def concerts():
    books = Books.query.all() 
    return render_template('concerts.html', books=books)




    
    
@app.route('/get_available_tickets', methods=['GET'])
def get_available_tickets():
    try:
        # Get the ISBN from the query parameters
        isbn = request.args.get('isbn')

        # Get the book based on the ISBN
        book = Books.query.filter_by(isbn=isbn).first()

        if book:

            return jsonify({'available_tickets': book.available_tickets})
        else:
           
            return jsonify({'error': 'Book not found.'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_content = request.form.get('message')

   
        send_email(name, email, subject, message_content)

        return render_template('contact-us.html', message_sent=True)
    else:
        return render_template('contact-us.html', message_sent=False)




@app.route('/submit_registration', methods=['POST'])
def submit_registration():
    try:
       
        isbn = request.form.get('isbn')

        # Get the book based on the ISBN
        book = Books.query.filter_by(isbn=isbn).first()

        if book:
            
            if book.available_tickets > 0:
               
                book.available_tickets -= 1
                db.session.commit()

               
                updated_ticket_count = book.available_tickets

                
                send_confirmation_email_registering(request.form.get('email'), book.name)

                return jsonify({'success': True, 'updated_ticket_count': updated_ticket_count})
            else:
                
                return jsonify({'success': False, 'error': 'No available tickets for this event.'})
        else:
       
            return jsonify({'success': False, 'error': 'Book not found.'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})





@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        user = Users.query.filter_by(email=email).first()

        if user:

            new_password = generate_random_password()


            send_password_reset_email(email, new_password)

       
            hashed_password = bcrypt.generate_password_hash(new_password)
            user.password = hashed_password
            db.session.commit()


    return render_template('forgot_password.html')

if __name__=='__main__':
    app.run(debug=True)