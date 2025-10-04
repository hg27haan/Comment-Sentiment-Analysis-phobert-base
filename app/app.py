import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  
from werkzeug.security import generate_password_hash, check_password_hash
from transformers import pipeline
import torch

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'f9b9a9f9c9b3e3e4a9b9c9d9e9f9a9b9'
app.config['ADMIN_SECRET_CODE'] = 'admin123'  # Mã bí mật để đăng ký tài khoản quản trị viên
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

print("Đang tải model...")
model_id = 'hghaan/Sentiment-Analysis-phobert-base'
device = 0 if torch.cuda.is_available() else -1
classifier = pipeline('sentiment-analysis', model=model_id, device=device)
print("Model đã sẵn sàng.")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)    
    is_admin = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)    

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    User_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sentiment = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        comment_text = request.form.get['content']
        if comment_text: 
            new_comment = Comment(text=comment_text, author=current_user)
            db.session.add(new_comment)
            db.session.commit()
            flash('Bình luận đã được gửi!', 'success')
            return redirect(url_for('index'))
        
    user_comments = Comment.query.filter_by(author=current_user).all()
    return render_template('index.html', comments=user_comments)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)

            if user.is_admin:
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        admin_code = request.form.get('admin_code')

        if password != password2:
            flash('Mật khẩu không khớp.', 'danger')
            return redirect(url_for('register'))
        
        existting_user = User.query.filter_by(username=username).first()
        if existting_user:
            flash('Tên đăng nhập đã tồn tại.', 'danger')
            return redirect(url_for('register'))
        
        is_admin_code == False
        if admin_code == app.config['ADMIN_SECRET_CODE']:
            is_admin_code = True
            flash('Bạn đã đăng ký với quyền quản trị viên.', 'success')
        elif admin_code:
            flash('Mã quản trị viên không đúng. Bạn sẽ được đăng ký với quyền người dùng thông thường.', 'warning')
        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('index'))
    
    all_comments = Comment.query.order_by(Comment.id.desc()).all()
    return render_template('admin.html', comments=all_comments)

@app.route('/predict/<int:comment_id>')
@login_required
def predict(comment_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    comment = Comment.query.get_or_404(comment_id)
    if comment.text: 
        result = classifier(comment.text[0])
        label_map = {
            'LABEL_0': 'Negative',
            'LABEL_1': 'Neutral',
            'LABEL_2': 'Positive'
        }
        sentiment = label_map.get(result['label'],'Không xác định')

        comment.sentiment = f"{sentiment} ({result['score']*100:.2f}%)"
        db.session.commit()
        flash(f'Đã phân tích bình luận #{comment.id}.', 'info')

    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)