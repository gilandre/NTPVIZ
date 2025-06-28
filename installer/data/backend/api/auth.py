"""
API Auth - Authentification et gestion des sessions
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from backend.models.user import User
from backend.app import db
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page et traitement de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username or not password:
            error_msg = 'Nom d\'utilisateur et mot de passe requis'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        # Rechercher l'utilisateur
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            error_msg = 'Nom d\'utilisateur ou mot de passe incorrect'
            logger.warning(f"Tentative de connexion échouée pour: {username}")
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            error_msg = 'Compte utilisateur désactivé'
            logger.warning(f"Tentative de connexion avec compte désactivé: {username}")
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        # Connexion réussie
        login_user(user, remember=remember)
        user.update_login()
        
        logger.info(f"Connexion réussie pour: {username}")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Connexion réussie',
                'user': user.to_dict(),
                'redirect_url': url_for('main.dashboard')
            })
        
        # Redirection après connexion
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}")
        error_msg = 'Erreur interne du serveur'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Déconnexion"""
    try:
        username = current_user.username
        logout_user()
        
        logger.info(f"Déconnexion de: {username}")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Déconnexion réussie',
                'redirect_url': url_for('auth.login')
            })
        
        flash('Vous avez été déconnecté avec succès', 'info')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {e}")
        if request.is_json:
            return jsonify({'error': 'Erreur lors de la déconnexion'}), 500
        return redirect(url_for('auth.login'))

@auth_bp.route('/api/session/check')
@login_required
def check_session():
    """Vérifier la session actuelle"""
    try:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict(),
            'session_valid': True,
            'timestamp': current_user.last_login.isoformat() if current_user.last_login else None
        })
        
    except Exception as e:
        logger.error(f"Erreur vérification session: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/user/profile')
@login_required
def get_profile():
    """Récupérer le profil utilisateur"""
    try:
        return jsonify(current_user.to_dict())
        
    except Exception as e:
        logger.error(f"Erreur récupération profil: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Mettre à jour le profil utilisateur"""
    try:
        data = request.get_json()
        
        # Champs modifiables
        updatable_fields = ['first_name', 'last_name', 'email', 'preferences']
        
        for field in updatable_fields:
            if field in data:
                if field == 'email':
                    # Vérifier l'unicité de l'email
                    existing_user = User.query.filter(
                        User.email == data[field],
                        User.id != current_user.id
                    ).first()
                    if existing_user:
                        return jsonify({'error': 'Cette adresse email est déjà utilisée'}), 400
                
                setattr(current_user, field, data[field])
        
        db.session.commit()
        
        logger.info(f"Profil mis à jour pour: {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Profil mis à jour avec succès',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour profil: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/user/change-password', methods=['POST'])
@login_required
def change_password():
    """Changer le mot de passe"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Les nouveaux mots de passe ne correspondent pas'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        
        # Changer le mot de passe
        current_user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Mot de passe changé pour: {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Mot de passe changé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/user/permissions')
@login_required
def get_user_permissions():
    """Récupérer les permissions de l'utilisateur actuel"""
    try:
        permissions = {
            'is_admin': current_user.is_admin,
            'can_configure': current_user.can_configure,
            'can_manage_users': current_user.is_admin,
            'can_manage_servers': current_user.can_configure,
            'can_manage_alerts': current_user.can_configure,
            'can_view_logs': True,
            'can_view_stats': True,
            'role': current_user.role
        }
        
        return jsonify(permissions)
        
    except Exception as e:
        logger.error(f"Erreur récupération permissions: {e}")
        return jsonify({'error': str(e)}), 500 