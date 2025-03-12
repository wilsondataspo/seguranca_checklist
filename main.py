from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seguranca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class ItemSeguranca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    concluido = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
@login_required
def index():
    itens = ItemSeguranca.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', itens=itens)

@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    descricao = request.form.get('descricao')
    if descricao:
        novo_item = ItemSeguranca(descricao=descricao, user_id=current_user.id)
        db.session.add(novo_item)
        db.session.commit()
        flash('Item adicionado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/concluir/<int:item_id>')
@login_required
def concluir(item_id):
    item = ItemSeguranca.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        item.concluido = not item.concluido
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/exportar_pdf')
@login_required
def exportar_pdf():
    itens = ItemSeguranca.query.filter_by(user_id=current_user.id).all()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, "Checklist de Segurança")
    y = 700
    for item in itens:
        status = "Concluído" if item.concluido else "Pendente"
        pdf.drawString(100, y, f"{item.descricao} - {status}")
        y -= 20
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='checklist_seguranca.pdf', mimetype='application/pdf')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe!', 'danger')
        else:
            novo_user = User(username=username, password=password)
            db.session.add(novo_user)
            db.session.commit()
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)