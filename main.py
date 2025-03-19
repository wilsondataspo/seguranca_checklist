from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, ItemSeguranca, SubItem
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seguranca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)  # Proteção CSRF
login_manager.login_view = 'login'


# Decorador para admin
def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acesso restrito a administradores!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/exportar_pdf')
@login_required
def exportar_pdf():
    try:
        # Consulta os itens
        if current_user.is_admin:
            itens = ItemSeguranca.query.all()
        else:
            itens = ItemSeguranca.query.filter_by(
                user_id=current_user.id).all()

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)

        # Configurar fonte e título
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(100, 750, "Checklist de Segurança")

        # Configurar posição inicial
        y_position = 730
        pdf.setFont("Helvetica", 12)

        # Adicionar conteúdo
        for item in itens:
            # Item principal
            status = "Concluído" if item.concluido else "Pendente"
            pdf.drawString(100, y_position, f"• {item.descricao} - {status}")
            y_position -= 20

            # Subitens
            for subitem in item.subitens:
                sub_status = "Concluído" if subitem.concluido else "Pendente"
                pdf.drawString(120, y_position,
                               f"  ◦ {subitem.descricao} - {sub_status}")
                y_position -= 15

            y_position -= 10  # Espaço entre itens

            # Quebra de página se necessário
            if y_position < 50:
                pdf.showPage()
                y_position = 750
                pdf.setFont("Helvetica", 12)

        pdf.save()
        buffer.seek(0)

        return send_file(buffer,
                         as_attachment=True,
                         download_name="checklist_seguranca.pdf",
                         mimetype="application/pdf")

    except Exception as e:
        flash(f"Erro ao gerar PDF: {str(e)}", "danger")
        app.logger.error(f"Erro no PDF: {str(e)}")  # Log detalhado
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas!', 'danger')
    return render_template('login.html')


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Usuário já existe!', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            novo_user = User(username=username, password=hashed_password)
            db.session.add(novo_user)
            db.session.commit()
            flash('Registro realizado! Faça login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/buscar')
@login_required
def buscar():
    termo = request.args.get('termo', '').strip()

    # Consulta base
    if current_user.is_admin:
        consulta = ItemSeguranca.query
    else:
        consulta = ItemSeguranca.query.filter_by(user_id=current_user.id)

    # Aplica filtro de pesquisa
    if termo:
        consulta = consulta.filter(ItemSeguranca.descricao.ilike(f'%{termo}%'))

    itens = consulta.all()

    return render_template('index.html', itens=itens, termo_pesquisa=termo)


@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        itens = ItemSeguranca.query.all()  # Admin vê todos os itens
    else:
        itens = ItemSeguranca.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', itens=itens)


@app.route('/adicionar_item', methods=['POST'])
@login_required
def adicionar_item():
    descricao = request.form.get('descricao', '').strip()
    if not descricao or len(descricao) > 200:
        flash('Descrição inválida (máx. 200 caracteres)!', 'danger')
        return redirect(url_for('index'))
    if descricao:
        novo_item = ItemSeguranca(descricao=descricao, user_id=current_user.id)
        db.session.add(novo_item)
        db.session.commit()
        flash('Item principal adicionado!', 'success')
    return redirect(url_for('index'))


@app.route('/adicionar_subitem/<int:item_id>', methods=['POST'])
@login_required
def adicionar_subitem(item_id):
    descricao = request.form.get('descricao_subitem')
    if descricao:
        novo_subitem = SubItem(descricao=descricao, item_id=item_id)
        db.session.add(novo_subitem)
        db.session.commit()
        flash('Subitem adicionado!', 'success')
    return redirect(url_for('index'))


@app.route('/concluir_item/<int:item_id>', methods=['POST'])
@login_required
def concluir_item(item_id):
    item = ItemSeguranca.query.get_or_404(item_id)

    # Verifica se o usuário tem permissão
    if not (current_user.is_admin or item.user_id == current_user.id):
        flash("Acesso negado!", "danger")
        return redirect(url_for('index'))

    # Atualiza o status do item
    item.concluido = not item.concluido
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/concluir_subitem/<int:subitem_id>', methods=['POST'])
@login_required
def concluir_subitem(subitem_id):
    subitem = SubItem.query.get_or_404(subitem_id)
    item_pai = subitem.item_pai
    if current_user.is_admin or item_pai.user_id == current_user.id:
        subitem.concluido = not subitem.concluido
        db.session.commit()
    return redirect(url_for('index'))


# Rota para admin visualizar todos os usuários
@app.route('/admin/usuarios')
@login_required
@admin_required  # Novo decorador
def admin_usuarios():
    usuarios = User.query.all()
    return render_template('admin_usuarios.html', usuarios=usuarios)


# Rota para admin ver detalhes de um usuário
@app.route('/admin/usuario/<int:user_id>')
@login_required
@admin_required  # Novo decorador
def admin_usuario(user_id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('index'))
    usuario = User.query.get_or_404(user_id)
    itens = ItemSeguranca.query.filter_by(user_id=user_id).all()
    return render_template('admin_usuario.html', usuario=usuario, itens=itens)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
