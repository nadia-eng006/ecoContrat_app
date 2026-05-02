from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Employe
from datetime import date, datetime
import os

app = Flask(__name__)
app.secret_key = 'eco_contrat_secret_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eco_contrat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Routes ──────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_authorized:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Email ou mot de passe incorrect.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        nom           = request.form.get('nom', '').strip()
        prenom        = request.form.get('prenom', '').strip()
        poste         = request.form.get('poste', '').strip()
        duree_contrat = request.form.get('duree_contrat', '').strip()
        date_debut_s  = request.form.get('date_debut', '')
        date_fin_s    = request.form.get('date_fin', '')

        errors = []
        if not nom:    errors.append("Le nom est requis.")
        if not prenom: errors.append("Le prénom est requis.")
        if not poste:  errors.append("Le poste est requis.")
        if not duree_contrat: errors.append("La durée du contrat est requise.")

        try:
            date_debut = datetime.strptime(date_debut_s, '%Y-%m-%d').date()
        except ValueError:
            errors.append("Date de début invalide.")
            date_debut = None
        try:
            date_fin = datetime.strptime(date_fin_s, '%Y-%m-%d').date()
        except ValueError:
            errors.append("Date de fin invalide.")
            date_fin = None

        if date_debut and date_fin and date_fin <= date_debut:
            errors.append("La date de fin doit être après la date de début.")

        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            emp = Employe(
                nom=nom, prenom=prenom, poste=poste,
                duree_contrat=duree_contrat,
                date_debut=date_debut, date_fin=date_fin,
                created_by=current_user.id
            )
            db.session.add(emp)
            db.session.commit()
            flash(f'{prenom} {nom} a été ajouté avec succès.', 'success')
            return redirect(url_for('dashboard'))

    employes = Employe.query.order_by(Employe.date_fin.asc()).all()
    alertes  = [e for e in employes if e.alerte_critique]
    actifs   = [e for e in employes if not e.alerte_critique]
    return render_template('dashboard.html',
                           employes=employes,
                           alertes=alertes,
                           actifs=actifs,
                           today=date.today())

@app.route('/employe/<int:emp_id>')
@login_required
def employe_detail(emp_id):
    emp = Employe.query.get_or_404(emp_id)
    return render_template('employe_detail.html', emp=emp, today=date.today())

@app.route('/employe/<int:emp_id>/supprimer', methods=['POST'])
@login_required
def supprimer_employe(emp_id):
    emp = Employe.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    flash(f'{emp.prenom} {emp.nom} a été supprimé.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/api/alertes')
@login_required
def api_alertes():
    alertes = Employe.query.filter(Employe.date_fin >= date.today()).all()
    return jsonify([{
        'id': e.id,
        'nom': e.nom,
        'prenom': e.prenom,
        'jours': e.jours_restants,
        'alerte': e.alerte_critique
    } for e in alertes if e.alerte_critique])

# ── Init DB ─────────────────────────────────────────────

def init_db():
    with app.app_context():
        db.create_all()
        # Créer utilisateurs par défaut
        users_default = [
            {'email': 'admin@ecotransfo.ma', 'password': 'Admin2026', 'nom': 'Administrateur'},
            {'email': 'rh@ecotransfo.ma',    'password': 'RH2026',    'nom': 'Ressources Humaines'},
        ]
        for u in users_default:
            if not User.query.filter_by(email=u['email']).first():
                user = User(email=u['email'], nom=u['nom'])
                user.set_password(u['password'])
                db.session.add(user)
        db.session.commit()
        print("✅ Base de données initialisée.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)