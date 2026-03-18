from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "castro_arcano_ads_2025"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gerenciamento_rotina.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS ---
class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    periodo = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pendente')
    data = db.Column(db.String(10), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    recorrente = db.Column(db.Boolean, default=False)

class AtividadeParalela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    data = db.Column(db.String(10), default=lambda: datetime.now().strftime('%Y-%m-%d'))

class AtividadeGlobal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    prazo = db.Column(db.String(10)) 
    status = db.Column(db.String(20), default='Pendente')

class Observacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(500), nullable=False)
    data = db.Column(db.String(10), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    data_sel = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    tarefas = Tarefa.query.filter_by(data=data_sel).all()
    paralelas = AtividadeParalela.query.filter_by(data=data_sel).all()
    globais = AtividadeGlobal.query.all()
    obs = Observacao.query.filter_by(data=data_sel).all()
    
    def calc_prog(lista):
        if not lista: return 0
        concluidas = len([i for i in lista if i.status == 'Concluído'])
        return int((concluidas / len(lista)) * 100)

    return render_template('index.html', 
                           tarefas=tarefas, paralelas=paralelas, globais=globais, obs=obs,
                           data_hoje=data_sel,
                           p_inicio=calc_prog([t for t in tarefas if t.periodo == 'Início']),
                           p_meio=calc_prog([t for t in tarefas if t.periodo == 'Meio']),
                           p_final=calc_prog([t for t in tarefas if t.periodo == 'Final']),
                           p_geral=calc_prog(tarefas + paralelas))

@app.route('/iniciar_turno/<data>')
def iniciar_turno(data):
    
    modelos = Tarefa.query.filter_by(recorrente=True).all()
    adicionadas = 0
    
    
    existentes = [t.descricao for t in Tarefa.query.filter_by(data=data).all()]
    
    
    templates = {t.descricao: t.periodo for t in modelos}
    
    for desc, per in templates.items():
        if desc not in existentes:
            nova = Tarefa(descricao=desc, periodo=per, data=data, recorrente=True, status='Pendente')
            db.session.add(nova)
            adicionadas += 1
    
    db.session.commit()
    flash(f"Turno Iniciado! {adicionadas} tarefas da sua rotina foram carregadas.", "success")
    return redirect(url_for('index', data=data))

@app.route('/add/<tipo>', methods=['POST'])
def add(tipo):
    data_atual = request.form.get('data')
    if tipo == 'tarefa':
        is_fixa = True if request.form.get('recorrente') else False
        db.session.add(Tarefa(descricao=request.form.get('descricao'), periodo=request.form.get('periodo'), data=data_atual, recorrente=is_fixa))
    elif tipo == 'global': 
        db.session.add(AtividadeGlobal(descricao=request.form.get('descricao'), prazo=request.form.get('prazo')))
    elif tipo == 'obs': 
        db.session.add(Observacao(texto=request.form.get('texto'), data=data_atual))
    elif tipo == 'paralela': 
        db.session.add(AtividadeParalela(descricao=request.form.get('descricao'), data=data_atual))
    db.session.commit()
    return redirect(url_for('index', data=data_atual))

@app.route('/update/<tipo>/<int:id>/<string:status>')
def update_status(tipo, id, status):
    if tipo == 'global': item = AtividadeGlobal.query.get(id)
    elif tipo == 'paralela': item = AtividadeParalela.query.get(id)
    else: item = Tarefa.query.get(id)
    if item:
        item.status = status
        db.session.commit()
    return redirect(request.referrer)

@app.route('/delete/<tipo>/<int:id>')
def delete(tipo, id):
    if tipo == 'global': item = AtividadeGlobal.query.get(id)
    elif tipo == 'obs': item = Observacao.query.get(id)
    elif tipo == 'paralela': item = AtividadeParalela.query.get(id)
    else: item = Tarefa.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/finalizar_turno/<data>')
def finalizar_turno(data):
    bloqueios_t = Tarefa.query.filter(Tarefa.data == data, Tarefa.status.in_(['Pendente', 'Em andamento'])).all()
    bloqueios_p = AtividadeParalela.query.filter(AtividadeParalela.data == data, AtividadeParalela.status.in_(['Pendente', 'Em andamento'])).all()
    if bloqueios_t or bloqueios_p:
        flash("Não é possível finalizar! Existem itens pendentes ou em andamento.", "error")
    else:
        flash("Turno finalizado com sucesso! Bom descanso.", "success")
    return redirect(url_for('index', data=data))

if __name__ == '__main__':
    app.run(debug=True)