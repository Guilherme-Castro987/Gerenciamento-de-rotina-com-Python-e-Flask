from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "castro_arcano_ads_2025"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gerenciamento_rotina.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    periodo = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pendente')
    data = db.Column(db.String(10), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    recorrente = db.Column(db.Boolean, default=False) # Define se a tarefa é da rotina fixa

class AtividadeParalela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    data = db.Column(db.String(10), default=lambda: datetime.now().strftime('%Y-%m-%d'))

class AtividadeGlobal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    prazo = db.Column(db.String(10)) 
    status = db.Column(db.String(20), default='Pendente')

class Observacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    texto = db.Column(db.String(500), nullable=False)
    data = db.Column(db.String(10), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if senha != confirmar_senha:
            flash('As senhas não correspondem!', 'error')
            return redirect(url_for('register'))
        
        if Usuario.query.filter_by(username=username).first():
            flash('Usuário já existe!', 'error')
            return redirect(url_for('register'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado!', 'error')
            return redirect(url_for('register'))
        
        novo_usuario = Usuario(
            username=username,
            email=email,
            senha=generate_password_hash(senha)
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('login.html', modo='cadastro')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            flash(f'Bem-vindo, {usuario.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    
    return render_template('login.html', modo='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    data_sel = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    tarefas = Tarefa.query.filter_by(user_id=current_user.id, data=data_sel).all()
    paralelas = AtividadeParalela.query.filter_by(user_id=current_user.id, data=data_sel).all()
    globais = AtividadeGlobal.query.filter_by(user_id=current_user.id).all()
    obs = Observacao.query.filter_by(user_id=current_user.id, data=data_sel).all()
    
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
@login_required
def iniciar_turno(data):
    # Busca tarefas marcadas como recorrentes (de qualquer dia) e remove duplicatas por descrição
    modelos = Tarefa.query.filter_by(user_id=current_user.id, recorrente=True).all()
    adicionadas = 0
    
    # Lista de descrições para evitar duplicar o que já existe no dia
    existentes = [t.descricao for t in Tarefa.query.filter_by(user_id=current_user.id, data=data).all()]
    
    # Dicionário para pegar apenas uma versão de cada tarefa recorrente
    templates = {t.descricao: t.periodo for t in modelos}
    
    for desc, per in templates.items():
        if desc not in existentes:
            nova = Tarefa(descricao=desc, periodo=per, data=data, recorrente=True, status='Pendente', user_id=current_user.id)
            db.session.add(nova)
            adicionadas += 1
    
    db.session.commit()
    flash(f"Turno Iniciado! {adicionadas} tarefas da sua rotina foram carregadas.", "success")
    return redirect(url_for('index', data=data))

@app.route('/add/<tipo>', methods=['POST'])
@login_required
def add(tipo):
    data_atual = request.form.get('data')
    if tipo == 'tarefa':
        is_fixa = True if request.form.get('recorrente') else False
        db.session.add(Tarefa(descricao=request.form.get('descricao'), periodo=request.form.get('periodo'), data=data_atual, recorrente=is_fixa, user_id=current_user.id))
    elif tipo == 'global': 
        db.session.add(AtividadeGlobal(descricao=request.form.get('descricao'), prazo=request.form.get('prazo'), user_id=current_user.id))
    elif tipo == 'obs': 
        db.session.add(Observacao(texto=request.form.get('texto'), data=data_atual, user_id=current_user.id))
    elif tipo == 'paralela': 
        db.session.add(AtividadeParalela(descricao=request.form.get('descricao'), data=data_atual, user_id=current_user.id))
    db.session.commit()
    return redirect(url_for('index', data=data_atual))

@app.route('/update/<tipo>/<int:id>/<string:status>')
@login_required
def update_status(tipo, id, status):
    if tipo == 'global': item = AtividadeGlobal.query.filter_by(id=id, user_id=current_user.id).first()
    elif tipo == 'paralela': item = AtividadeParalela.query.filter_by(id=id, user_id=current_user.id).first()
    else: item = Tarefa.query.filter_by(id=id, user_id=current_user.id).first()
    if item:
        item.status = status
        db.session.commit()
    return redirect(request.referrer)

@app.route('/delete/<tipo>/<int:id>')
@login_required
def delete(tipo, id):
    if tipo == 'global': item = AtividadeGlobal.query.filter_by(id=id, user_id=current_user.id).first()
    elif tipo == 'obs': item = Observacao.query.filter_by(id=id, user_id=current_user.id).first()
    elif tipo == 'paralela': item = AtividadeParalela.query.filter_by(id=id, user_id=current_user.id).first()
    else: item = Tarefa.query.filter_by(id=id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/finalizar_turno/<data>')
@login_required
def finalizar_turno(data):
    bloqueios_t = Tarefa.query.filter(Tarefa.user_id == current_user.id, Tarefa.data == data, Tarefa.status.in_(['Pendente', 'Em andamento'])).all()
    bloqueios_p = AtividadeParalela.query.filter(AtividadeParalela.user_id == current_user.id, AtividadeParalela.data == data, AtividadeParalela.status.in_(['Pendente', 'Em andamento'])).all()
    if bloqueios_t or bloqueios_p:
        flash("Não é possível finalizar! Existem itens pendentes ou em andamento.", "error")
    else:
        flash("Turno finalizado com sucesso! Bom descanso.", "success")
    return redirect(url_for('index', data=data))

if __name__ == '__main__':
    app.run(debug=True)