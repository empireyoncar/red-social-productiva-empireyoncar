from models.user_model import Usuario
from database import db
from utils.jwt_util import JWTUtil

class AuthService:
    """Servicio de autenticación"""
    
    @staticmethod
    def registrar_usuario(email: str, password: str, nombre: str, apellido: str, username: str = None) -> dict:
        """Registra un nuevo usuario en la base de datos"""
        
        # Verificar si el email ya existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            return {
                'success': False,
                'message': 'El email ya está registrado',
                'usuario': None,
                'token': None
            }
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            email=email,
            nombre=nombre,
            apellido=apellido,
            username=username or email.split('@')[0]
        )
        
        # Hashear contraseña
        nuevo_usuario.set_password(password)
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            # Generar JWT
            token = JWTUtil.generate_token(nuevo_usuario.id, nuevo_usuario.email)
            
            return {
                'success': True,
                'message': 'Usuario registrado exitosamente',
                'usuario': nuevo_usuario.to_dict(),
                'token': token
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error al registrar usuario: {str(e)}',
                'usuario': None,
                'token': None
            }
    
    @staticmethod
    def login_usuario(email: str, password: str) -> dict:
        """Autentica un usuario y genera JWT"""
        
        # Buscar usuario
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            return {
                'success': False,
                'message': 'Email o contraseña incorrectos',
                'usuario': None,
                'token': None
            }
        
        # Verificar contraseña
        if not usuario.check_password(password):
            return {
                'success': False,
                'message': 'Email o contraseña incorrectos',
                'usuario': None,
                'token': None
            }
        
        # Generar JWT
        token = JWTUtil.generate_token(usuario.id, usuario.email)
        
        return {
            'success': True,
            'message': 'Login exitoso',
            'usuario': usuario.to_dict(),
            'token': token
        }
    
    @staticmethod
    def verificar_token(token: str) -> dict:
        """Verifica si un token es válido"""
        payload = JWTUtil.verify_token(token)
        
        if not payload:
            return {
                'valid': False,
                'user_id': None,
                'email': None
            }
        
        return {
            'valid': True,
            'user_id': payload.get('user_id'),
            'email': payload.get('email')
        }
