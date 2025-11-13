from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    """View para login de usuários"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redireciona o usuário para o nome da URL 'dashboard'
            return redirect('dashboard') 
        else:
            # Renderiza o template de login novamente, passando a mensagem de erro
            return render(request, 'hierarquia/login.html', {
                 'error': 'Usuário ou senha inválidos'
            })
    
    # Renderização inicial do formulário (método GET)
    return render(request, 'hierarquia/login.html')

def logout_view(request):
    """View para logout de usuários"""
    logout(request)
    # CORREÇÃO: Redireciona para o novo nome da URL
    return redirect('rh_login')