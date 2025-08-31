"""
Service d'audit - NTP Monitor
Logging dédié pour toutes les actions CRUD, connexions et opérations sensibles
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from flask_login import current_user
from flask import request
import json
from backend.database_manager import get_db_session_with_context
from backend.models import AuditLog

class AuditService:
    """Service de logging d'audit pour traçabilité complète"""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialiser le service d'audit"""
        self.log_dir = log_dir
        self.ensure_log_directory()
        
        # Configuration des loggers spécialisés
        self.setup_loggers()
    
    def ensure_log_directory(self):
        """S'assurer que le répertoire de logs existe"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_loggers(self):
        """Configurer les loggers spécialisés"""
        
        # Logger pour les authentifications
        self.auth_logger = logging.getLogger('audit.auth')
        self.auth_logger.setLevel(logging.INFO)
        
        # Logger pour les opérations CRUD
        self.crud_logger = logging.getLogger('audit.crud')
        self.crud_logger.setLevel(logging.INFO)
        
        # Logger pour les actions administratives
        self.admin_logger = logging.getLogger('audit.admin')
        self.admin_logger.setLevel(logging.INFO)
        
        # Configuration des handlers si pas déjà fait
        if not self.auth_logger.handlers:
            self._setup_file_handler(self.auth_logger, 'auth_audit.log')
        
        if not self.crud_logger.handlers:
            self._setup_file_handler(self.crud_logger, 'crud_audit.log')
            
        if not self.admin_logger.handlers:
            self._setup_file_handler(self.admin_logger, 'admin_audit.log')
    
    def _setup_file_handler(self, logger, filename):
        """Configurer un handler de fichier pour un logger"""
        log_file = os.path.join(self.log_dir, filename)
        
        # Handler avec rotation quotidienne
        from logging.handlers import TimedRotatingFileHandler
        handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Garder 30 jours
            encoding='utf-8'
        )
        
        # Format détaillé pour l'audit
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Empêcher la propagation vers le logger racine
        logger.propagate = False
    
    def get_user_info(self) -> Dict[str, Any]:
        """Obtenir les informations de l'utilisateur actuel"""
        try:
            if current_user and current_user.is_authenticated:
                return {
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'role': current_user.role,
                    'email': current_user.email
                }
        except Exception:
            pass
        
        return {
            'user_id': None,
            'username': 'Anonymous',
            'role': 'guest',
            'email': None
        }
    
    def get_request_info(self) -> Dict[str, Any]:
        """Obtenir les informations de la requête"""
        try:
            if request:
                return {
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    'method': request.method,
                    'endpoint': request.endpoint,
                    'url': request.url
                }
        except Exception:
            pass
        
        return {
            'ip_address': 'Unknown',
            'user_agent': 'Unknown',
            'method': 'Unknown',
            'endpoint': 'Unknown',
            'url': 'Unknown'
        }
    
    def format_audit_message(self, action: str, details: Dict[str, Any] = None) -> str:
        """Formater un message d'audit complet"""
        user_info = self.get_user_info()
        request_info = self.get_request_info()
        
        audit_data = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'user': user_info,
            'request': request_info
        }
        
        if details:
            audit_data['details'] = details
        
        return json.dumps(audit_data, ensure_ascii=False, separators=(',', ':'))

    def persist(self, action: str, details: Dict[str, Any] = None, resource: str = None, resource_id: Any = None):
        """Persister le log d'audit en base, erreurs silencieuses pour ne pas bloquer le flux"""
        try:
            user = self.get_user_info()
            req = self.get_request_info()
            with get_db_session_with_context() as session:
                log = AuditLog(
                    user_id=user.get('user_id'),
                    username=user.get('username'),
                    role=user.get('role'),
                    action=action,
                    resource=resource,
                    resource_id=str(resource_id) if resource_id is not None else None,
                    details=json.dumps(details, ensure_ascii=False) if details else None,
                    ip_address=req.get('ip_address'),
                    user_agent=req.get('user_agent'),
                    method=req.get('method'),
                    endpoint=req.get('endpoint'),
                    url=req.get('url')
                )
                session.add(log)
                session.commit()
        except Exception:
            pass
    
    # =============================================================================
    # MÉTHODES D'AUDIT POUR AUTHENTIFICATION
    # =============================================================================
    
    def log_login_attempt(self, username: str, success: bool, reason: str = None):
        """Logger une tentative de connexion"""
        details = {
            'username': username,
            'success': success,
            'reason': reason or ('Login successful' if success else 'Login failed')
        }
        
        action = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
        message = self.format_audit_message(action, details)
        
        if success:
            self.auth_logger.info(message)
        else:
            self.auth_logger.warning(message)
        self.persist(action, details, resource='auth')
    
    def log_logout(self, username: str):
        """Logger une déconnexion"""
        details = {'username': username}
        message = self.format_audit_message('LOGOUT', details)
        self.auth_logger.info(message)
        self.persist('LOGOUT', details, resource='auth')
    
    def log_session_expired(self, username: str):
        """Logger l'expiration d'une session"""
        details = {'username': username}
        message = self.format_audit_message('SESSION_EXPIRED', details)
        self.auth_logger.info(message)
        self.persist('SESSION_EXPIRED', details, resource='auth')
    
    def log_password_change(self, username: str, by_admin: bool = False):
        """Logger un changement de mot de passe"""
        details = {
            'target_username': username,
            'changed_by_admin': by_admin
        }
        message = self.format_audit_message('PASSWORD_CHANGED', details)
        self.auth_logger.info(message)
        self.persist('PASSWORD_CHANGED', details, resource='user')
    
    # =============================================================================
    # MÉTHODES D'AUDIT POUR OPÉRATIONS CRUD
    # =============================================================================
    
    def log_user_created(self, user_data: Dict[str, Any], auto_generated_password: bool = False):
        """Logger la création d'un utilisateur"""
        details = {
            'created_user': {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'role': user_data.get('role')
            },
            'auto_generated_password': auto_generated_password
        }
        message = self.format_audit_message('USER_CREATED', details)
        self.crud_logger.info(message)
        self.persist('USER_CREATED', details, resource='user', resource_id=user_data.get('id'))
    
    def log_user_updated(self, user_id: int, old_data: Dict[str, Any], new_data: Dict[str, Any]):
        """Logger la modification d'un utilisateur"""
        # Identifier les champs modifiés
        changes = {}
        for key in new_data:
            if key in old_data and old_data[key] != new_data[key]:
                changes[key] = {
                    'old': old_data[key],
                    'new': new_data[key]
                }
        
        details = {
            'user_id': user_id,
            'username': old_data.get('username'),
            'changes': changes
        }
        message = self.format_audit_message('USER_UPDATED', details)
        self.crud_logger.info(message)
        self.persist('USER_UPDATED', details, resource='user', resource_id=user_id)
    
    def log_user_deleted(self, user_data: Dict[str, Any]):
        """Logger la suppression d'un utilisateur"""
        details = {
            'deleted_user': {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'role': user_data.get('role')
            }
        }
        message = self.format_audit_message('USER_DELETED', details)
        self.crud_logger.warning(message)
        self.persist('USER_DELETED', details, resource='user', resource_id=user_data.get('id'))
    
    def log_user_status_changed(self, user_id: int, username: str, old_status: bool, new_status: bool):
        """Logger le changement de statut d'un utilisateur"""
        details = {
            'user_id': user_id,
            'username': username,
            'old_status': 'active' if old_status else 'inactive',
            'new_status': 'active' if new_status else 'inactive'
        }
        action = 'USER_ACTIVATED' if new_status else 'USER_DEACTIVATED'
        message = self.format_audit_message(action, details)
        self.crud_logger.info(message)
        self.persist(action, details, resource='user', resource_id=user_id)
    
    def log_password_generated(self, user_id: int, username: str, password_strength: str):
        """Logger la génération d'un mot de passe"""
        details = {
            'user_id': user_id,
            'username': username,
            'password_strength': password_strength
        }
        message = self.format_audit_message('PASSWORD_GENERATED', details)
        self.crud_logger.info(message)
        self.persist('PASSWORD_GENERATED', details, resource='user', resource_id=user_id)
    
    # =============================================================================
    # MÉTHODES D'AUDIT POUR ACTIONS ADMINISTRATIVES
    # =============================================================================
    
    def log_admin_action(self, action: str, target: str, details: Dict[str, Any] = None):
        """Logger une action administrative générique"""
        audit_details = {
            'action': action,
            'target': target
        }
        if details:
            audit_details.update(details)
        
        message = self.format_audit_message(f'ADMIN_{action.upper()}', audit_details)
        self.admin_logger.info(message)
        self.persist(f'ADMIN_{action.upper()}', audit_details, resource=target)
    
    def log_config_change(self, config_key: str, old_value: Any, new_value: Any):
        """Logger un changement de configuration"""
        details = {
            'config_key': config_key,
            'old_value': str(old_value),
            'new_value': str(new_value)
        }
        message = self.format_audit_message('CONFIG_CHANGED', details)
        self.admin_logger.info(message)
        self.persist('CONFIG_CHANGED', details, resource='config', resource_id=config_key)
    
    def log_system_action(self, action: str, details: Dict[str, Any] = None):
        """Logger une action système"""
        message = self.format_audit_message(f'SYSTEM_{action.upper()}', details or {})
        self.admin_logger.info(message)
        self.persist(f'SYSTEM_{action.upper()}', details or {}, resource='system')
        self.persist(f'SYSTEM_{action.upper()}', details or {}, resource='system')

    def log_view(self, resource: str, resource_id: Any = None, details: Dict[str, Any] = None):
        """Logger une consultation (qui consulte quoi)"""
        view_details = {
            'resource': resource
        }
        if resource_id is not None:
            view_details['resource_id'] = resource_id
        if details:
            view_details.update(details)
        message = self.format_audit_message('VIEW', view_details)
        self.admin_logger.info(message)
        self.persist('VIEW', view_details, resource=resource, resource_id=resource_id)
    
    # =============================================================================
    # MÉTHODES D'AUDIT POUR SERVEURS NTP
    # =============================================================================
    
    def log_server_created(self, server_data: Dict[str, Any]):
        """Logger la création d'un serveur NTP"""
        details = {
            'server': {
                'id': server_data.get('id'),
                'name': server_data.get('name'),
                'address': server_data.get('address'),
                'type': server_data.get('server_type')
            }
        }
        message = self.format_audit_message('NTP_SERVER_CREATED', details)
        self.crud_logger.info(message)
        self.persist('NTP_SERVER_CREATED', details, resource='server', resource_id=server_data.get('id'))
    
    def log_server_updated(self, server_id: int, changes: Dict[str, Any]):
        """Logger la modification d'un serveur NTP"""
        details = {
            'server_id': server_id,
            'changes': changes
        }
        message = self.format_audit_message('NTP_SERVER_UPDATED', details)
        self.crud_logger.info(message)
        self.persist('NTP_SERVER_UPDATED', details, resource='server', resource_id=server_id)
    
    def log_server_deleted(self, server_data: Dict[str, Any]):
        """Logger la suppression d'un serveur NTP"""
        details = {
            'server': {
                'id': server_data.get('id'),
                'name': server_data.get('name'),
                'address': server_data.get('address')
            }
        }
        message = self.format_audit_message('NTP_SERVER_DELETED', details)
        self.crud_logger.warning(message)
        self.persist('NTP_SERVER_DELETED', details, resource='server', resource_id=server_data.get('id'))
    
    def log_server_test(self, server_id: int, server_name: str, success: bool, result: Dict[str, Any]):
        """Logger un test de serveur NTP"""
        details = {
            'server_id': server_id,
            'server_name': server_name,
            'test_success': success,
            'result': result
        }
        message = self.format_audit_message('NTP_SERVER_TESTED', details)
        self.crud_logger.info(message)
        self.persist('NTP_SERVER_TESTED', details, resource='server', resource_id=server_id)

# Instance globale du service d'audit
audit_service = AuditService()

# Fonctions utilitaires pour faciliter l'usage
def log_auth_event(action: str, username: str, success: bool = True, reason: str = None):
    """Fonction utilitaire pour logger les événements d'authentification"""
    if action == 'login':
        audit_service.log_login_attempt(username, success, reason)
    elif action == 'logout':
        audit_service.log_logout(username)
    elif action == 'password_change':
        audit_service.log_password_change(username)

def log_crud_event(action: str, entity_type: str, entity_data: Dict[str, Any], **kwargs):
    """Fonction utilitaire pour logger les événements CRUD"""
    if entity_type == 'user':
        if action == 'create':
            audit_service.log_user_created(entity_data, kwargs.get('auto_generated_password', False))
        elif action == 'update':
            audit_service.log_user_updated(entity_data['id'], kwargs.get('old_data', {}), entity_data)
        elif action == 'delete':
            audit_service.log_user_deleted(entity_data)
    elif entity_type == 'server':
        if action == 'create':
            audit_service.log_server_created(entity_data)
        elif action == 'update':
            audit_service.log_server_updated(entity_data['id'], kwargs.get('changes', {}))
        elif action == 'delete':
            audit_service.log_server_deleted(entity_data)

def log_admin_event(action: str, target: str, details: Dict[str, Any] = None):
    """Fonction utilitaire pour logger les actions administratives"""
    audit_service.log_admin_action(action, target, details) 