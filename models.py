from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    nom           = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_authorized = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Employe(db.Model):
    __tablename__ = 'employes'
    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(100), nullable=False)
    prenom        = db.Column(db.String(100), nullable=False)
    poste         = db.Column(db.String(100), nullable=False)
    duree_contrat = db.Column(db.String(50),  nullable=False)   # ex: "6 mois", "1 an"
    date_debut    = db.Column(db.Date,         nullable=False)
    date_fin      = db.Column(db.Date,         nullable=False)
    date_creation = db.Column(db.DateTime,     default=datetime.utcnow)
    created_by    = db.Column(db.Integer,      db.ForeignKey('users.id'))

    @property
    def jours_restants(self):
        delta = self.date_fin - date.today()
        return delta.days

    @property
    def duree_restante_label(self):
        j = self.jours_restants
        if j < 0:
            return "Expiré"
        if j == 0:
            return "Expire aujourd'hui"
        if j == 1:
            return "1 jour"
        if j < 7:
            return f"{j} jours"
        if j < 14:
            return "1 semaine"
        if j < 30:
            return f"{j // 7} semaines"
        if j < 60:
            return "1 mois"
        mois = j // 30
        if mois < 12:
            return f"{mois} mois"
        ans = mois // 12
        reste_mois = mois % 12
        if reste_mois == 0:
            return f"{ans} an{'s' if ans > 1 else ''}"
        return f"{ans} an{'s' if ans > 1 else ''} et {reste_mois} mois"

    @property
    def alerte_critique(self):
        """True si ≤ 7 jours restants et contrat pas encore expiré"""
        return 0 <= self.jours_restants <= 7

    @property
    def statut(self):
        j = self.jours_restants
        if j < 0:   return "expire"
        if j <= 7:  return "critique"
        if j <= 30: return "attention"
        return "actif"

    def __repr__(self):
        return f'<Employe {self.nom} {self.prenom}>'