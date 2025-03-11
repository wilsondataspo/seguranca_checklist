from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Lista de itens de segurança
itens_seguranca = [
    {
        "id": 1,
        "descricao": "Verificar extintores",
        "concluido": False
    },
    {
        "id": 2,
        "descricao": "Inspecionar saídas de emergência",
        "concluido": False
    },
    {
        "id": 3,
        "descricao": "Testar alarmes de incêndio",
        "concluido": False
    },
    {
        "id": 4,
        "descricao": "Escada rolante",
        "concluido": False
    },
    {
        "id": 5,
        "descricao": "Elevadores",
        "concluido": False
    },
]


@app.route('/')
def index():
    return render_template('index.html', itens=itens_seguranca)


@app.route('/concluir/<int:item_id>')
def concluir(item_id):
    for item in itens_seguranca:
        if item['id'] == item_id:
            item['concluido'] = not item['concluido']
            break
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
