"""
Service de gestion des mots de passe - NTP Monitor
Génération automatique de mots de passe sécurisés et communication
"""

import secrets
import string
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PasswordService:
    """Service de génération et gestion des mots de passe"""
    
    # Configuration par défaut
    DEFAULT_LENGTH = 12
    MIN_LENGTH = 8
    MAX_LENGTH = 32
    
    # Caractères autorisés (évite les caractères ambigus)
    LETTERS_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    LETTERS_LOWER = 'abcdefghijklmnopqrstuvwxyz'
    DIGITS = '23456789'  # Évite 0, 1 (ambigus avec O, l)
    SPECIAL_CHARS = '@#$%&*+-=?'  # Caractères spéciaux sûrs
    
    def __init__(self):
        """Initialiser le service de mots de passe"""
        self.temp_passwords = {}  # Cache temporaire pour les mots de passe générés
        
    def generate_password(self, 
                         length: int = None, 
                         include_uppercase: bool = True,
                         include_lowercase: bool = True,
                         include_digits: bool = True,
                         include_special: bool = True,
                         readable: bool = False) -> str:
        """
        Générer un mot de passe sécurisé
        
        Args:
            length: Longueur du mot de passe (défaut: 12)
            include_uppercase: Inclure majuscules
            include_lowercase: Inclure minuscules
            include_digits: Inclure chiffres
            include_special: Inclure caractères spéciaux
            readable: Générer un mot de passe plus lisible
            
        Returns:
            str: Mot de passe généré
        """
        if length is None:
            length = self.DEFAULT_LENGTH
            
        if length < self.MIN_LENGTH:
            length = self.MIN_LENGTH
        elif length > self.MAX_LENGTH:
            length = self.MAX_LENGTH
            
        # Construction de l'alphabet
        alphabet = ''
        required_chars = []
        
        if include_uppercase:
            alphabet += self.LETTERS_UPPER
            required_chars.append(secrets.choice(self.LETTERS_UPPER))
            
        if include_lowercase:
            alphabet += self.LETTERS_LOWER
            required_chars.append(secrets.choice(self.LETTERS_LOWER))
            
        if include_digits:
            alphabet += self.DIGITS
            required_chars.append(secrets.choice(self.DIGITS))
            
        if include_special:
            alphabet += self.SPECIAL_CHARS
            required_chars.append(secrets.choice(self.SPECIAL_CHARS))
            
        if not alphabet:
            raise ValueError("Au moins un type de caractère doit être inclus")
            
        # Générer le mot de passe
        if readable:
            return self._generate_readable_password(length, alphabet, required_chars)
        else:
            return self._generate_random_password(length, alphabet, required_chars)
    
    def _generate_random_password(self, length: int, alphabet: str, required_chars: List[str]) -> str:
        """Générer un mot de passe aléatoire"""
        # Commencer avec les caractères requis
        password = required_chars.copy()
        
        # Compléter avec des caractères aléatoires
        remaining_length = length - len(required_chars)
        for _ in range(remaining_length):
            password.append(secrets.choice(alphabet))
            
        # Mélanger le mot de passe
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def _generate_readable_password(self, length: int, alphabet: str, required_chars: List[str]) -> str:
        """Générer un mot de passe plus lisible (patterns syllabiques)"""
        # Pour un mot de passe lisible, on alterne consonnes/voyelles
        consonants = 'bcdfghjklmnpqrstvwxyz'
        vowels = 'aeiou'
        
        password = []
        use_consonant = True
        
        # Ajouter les caractères requis d'abord
        password.extend(required_chars)
        
        # Générer le reste en alternant
        remaining = length - len(required_chars)
        for i in range(remaining):
            if use_consonant and i < remaining - 2:  # Laisser place aux chiffres/spéciaux
                if any(c in consonants for c in alphabet):
                    char = secrets.choice([c for c in alphabet if c.lower() in consonants])
                else:
                    char = secrets.choice(alphabet)
            elif not use_consonant and i < remaining - 2:
                if any(c in vowels for c in alphabet):
                    char = secrets.choice([c for c in alphabet if c.lower() in vowels])
                else:
                    char = secrets.choice(alphabet)
            else:
                char = secrets.choice(alphabet)
                
            password.append(char)
            use_consonant = not use_consonant
            
        # Mélanger légèrement pour éviter les patterns trop prévisibles
        if len(password) > 4:
            # Échanger quelques positions aléatoirement
            for _ in range(len(password) // 4):
                i, j = secrets.randbelow(len(password)), secrets.randbelow(len(password))
                password[i], password[j] = password[j], password[i]
        
        return ''.join(password)
    
    def generate_username(self, first_name: str, last_name: str, existing_usernames: List[str] = None) -> str:
        """
        Générer un nom d'utilisateur basé sur le prénom et nom
        
        Args:
            first_name: Prénom
            last_name: Nom de famille
            existing_usernames: Liste des noms d'utilisateur existants
            
        Returns:
            str: Nom d'utilisateur unique
        """
        if existing_usernames is None:
            existing_usernames = []
            
        # Nettoyer les noms
        first_clean = re.sub(r'[^a-zA-Z]', '', first_name.lower())
        last_clean = re.sub(r'[^a-zA-Z]', '', last_name.lower())
        
        # Patterns de génération par ordre de préférence
        patterns = [
            f"{first_clean}.{last_clean}",
            f"{first_clean}{last_clean}",
            f"{first_clean[0]}.{last_clean}",
            f"{first_clean}{last_clean[0]}",
            f"{first_clean[:3]}.{last_clean[:3]}",
        ]
        
        # Essayer chaque pattern
        for pattern in patterns:
            if pattern not in existing_usernames and len(pattern) >= 3:
                return pattern
                
        # Si aucun pattern ne fonctionne, ajouter un suffixe numérique
        base = f"{first_clean}.{last_clean}"
        counter = 1
        while f"{base}{counter}" in existing_usernames:
            counter += 1
            
        return f"{base}{counter}"
    
    def validate_password_strength(self, password: str) -> Dict[str, any]:
        """
        Valider la force d'un mot de passe
        
        Args:
            password: Mot de passe à valider
            
        Returns:
            Dict contenant le score et les détails
        """
        score = 0
        feedback = []
        requirements = {
            'length': False,
            'uppercase': False,
            'lowercase': False,
            'digits': False,
            'special': False
        }
        
        # Longueur
        if len(password) >= 8:
            score += 1
            requirements['length'] = True
        else:
            feedback.append("Minimum 8 caractères requis")
            
        if len(password) >= 12:
            score += 1
            
        # Majuscules
        if re.search(r'[A-Z]', password):
            score += 1
            requirements['uppercase'] = True
        else:
            feedback.append("Au moins une majuscule requise")
            
        # Minuscules
        if re.search(r'[a-z]', password):
            score += 1
            requirements['lowercase'] = True
        else:
            feedback.append("Au moins une minuscule requise")
            
        # Chiffres
        if re.search(r'\d', password):
            score += 1
            requirements['digits'] = True
        else:
            feedback.append("Au moins un chiffre requis")
            
        # Caractères spéciaux
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
            requirements['special'] = True
        else:
            feedback.append("Au moins un caractère spécial requis")
            
        # Patterns courants (malus)
        common_patterns = [
            r'123', r'abc', r'qwerty', r'password', r'admin',
            r'(.)\1{2,}',  # Répétitions
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                score -= 1
                feedback.append("Évitez les motifs courants")
                break
                
        # Évaluation finale
        if score >= 5:
            strength = 'Très fort'
            strength_level = 'excellent'
        elif score >= 4:
            strength = 'Fort'
            strength_level = 'good'
        elif score >= 3:
            strength = 'Moyen'
            strength_level = 'medium'
        elif score >= 2:
            strength = 'Faible'
            strength_level = 'weak'
        else:
            strength = 'Très faible'
            strength_level = 'very_weak'
            
        return {
            'score': max(0, score),
            'max_score': 7,
            'strength': strength,
            'strength_level': strength_level,
            'requirements': requirements,
            'feedback': feedback,
            'is_valid': score >= 4 and all(requirements.values())
        }
    
    def store_temporary_password(self, user_id: int, password: str, expires_hours: int = 24) -> str:
        """
        Stocker temporairement un mot de passe généré
        
        Args:
            user_id: ID de l'utilisateur
            password: Mot de passe à stocker
            expires_hours: Durée d'expiration en heures
            
        Returns:
            str: Token de récupération
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        self.temp_passwords[token] = {
            'user_id': user_id,
            'password': password,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        
        # Nettoyer les tokens expirés
        self._cleanup_expired_tokens()
        
        logger.info(f"Mot de passe temporaire stocké pour utilisateur {user_id}")
        return token
    
    def get_temporary_password(self, token: str) -> Optional[Dict]:
        """
        Récupérer un mot de passe temporaire
        
        Args:
            token: Token de récupération
            
        Returns:
            Dict contenant les informations ou None si expiré/invalide
        """
        if token not in self.temp_passwords:
            return None
            
        data = self.temp_passwords[token]
        
        if datetime.utcnow() > data['expires_at']:
            del self.temp_passwords[token]
            return None
            
        return data
    
    def _cleanup_expired_tokens(self):
        """Nettoyer les tokens expirés"""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, data in self.temp_passwords.items()
            if now > data['expires_at']
        ]
        
        for token in expired_tokens:
            del self.temp_passwords[token]
            
        if expired_tokens:
            logger.info(f"Nettoyé {len(expired_tokens)} tokens expirés")

# Instance globale du service
password_service = PasswordService()

def generate_secure_password(length: int = 12, readable: bool = False) -> str:
    """
    Fonction utilitaire pour générer un mot de passe sécurisé
    
    Args:
        length: Longueur du mot de passe
        readable: Générer un mot de passe lisible
        
    Returns:
        str: Mot de passe généré
    """
    return password_service.generate_password(length=length, readable=readable)

def validate_password(password: str) -> Dict[str, any]:
    """
    Fonction utilitaire pour valider un mot de passe
    
    Args:
        password: Mot de passe à valider
        
    Returns:
        Dict: Résultat de la validation
    """
    return password_service.validate_password_strength(password) 