"""
FATI Accounts - Views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from .models import Permission
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    TokenSerializer,
    PermissionSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des utilisateurs"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['role', 'status', 'assigned_region']
    search_fields = ['email', 'first_name', 'last_name', 'organization']
    ordering_fields = ['created_at', 'last_name', 'role']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filtrer selon les permissions de l'utilisateur"""
        user = self.request.user
        
        # Admin voit tout
        if user.is_admin:
            return User.objects.all()
        
        # Institution voit les utilisateurs de son niveau et en dessous
        if user.is_institution:
            return User.objects.filter(role__in=[
                'institution', 'sector_health', 'sector_education',
                'local_manager', 'contributor'
            ])
        
        # Les autres ne voient que leur profil
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Authentification d'un utilisateur"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=email, password=password)
        
        if not user:
            return Response(
                {'error': 'Identifiants invalides'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.status != 'active':
            return Response(
                {'error': 'Compte inactif ou suspendu'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mettre à jour la dernière connexion
        user.update_last_login()
        
        # Créer ou récupérer le token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Déconnexion d'un utilisateur"""
        try:
            request.user.auth_token.delete()
        except:
            pass
        return Response({'message': 'Déconnexion réussie'})
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Changer le mot de passe"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Vérifier l'ancien mot de passe
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Ancien mot de passe incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Changer le mot de passe
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Régénérer le token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return Response({
            'message': 'Mot de passe changé avec succès',
            'token': token.key
        })
    
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Lister les utilisateurs par rôle"""
        role = request.query_params.get('role')
        if not role:
            return Response(
                {'error': 'Le paramètre role est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = self.get_queryset().filter(role=role)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les permissions"""
    
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_permissions(self, request):
        """Récupérer les permissions de l'utilisateur connecté"""
        permissions = Permission.objects.filter(role=request.user.role)
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
