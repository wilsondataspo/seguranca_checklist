from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, ItemSeguranca, SubItem

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seguranca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ... (rotas existentes: login, registrar, logout, exportar_pdf)


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
    descricao = request.form.get('descricao')
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


@app.route('/concluir_item/<int:item_id>')
@login_required
def concluir_item(item_id):
    item = ItemSeguranca.query.get_or_404(item_id)
    if current_user.is_admin or item.user_id == current_user.id:
        item.concluido = not item.concluido
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/concluir_subitem/<int:subitem_id>')
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
def admin_usuarios():
    if not current_user.is_admin:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('index'))
    usuarios = User.query.all()
    return render_template('admin_usuarios.html', usuarios=usuarios)


# Rota para admin ver detalhes de um usuário
@app.route('/admin/usuario/<int:user_id>')
@login_required
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
