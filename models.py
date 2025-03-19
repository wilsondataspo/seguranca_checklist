from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),
                         unique=True,
                         nullable=False,
                         index=True)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Novo campo para admin
    itens_seguranca = db.relationship('ItemSeguranca',
                                      backref='user',
                                      lazy=True)


class ItemSeguranca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False,
                          index=True)  # Índice adicionado
    concluido = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subitens = db.relationship('SubItem', backref='item_pai',
                               lazy=True)  # Relação com subitens


class SubItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    concluido = db.Column(db.Boolean, default=False)
    item_id = db.Column(db.Integer,
                        db.ForeignKey('item_seguranca.id'),
                        nullable=False)
