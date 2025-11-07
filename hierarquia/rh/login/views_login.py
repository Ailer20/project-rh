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
            return redirect('dashboard')
        else:
            return render(request, 'hierarquia/login.html', {
                'error': 'Usuário ou senha inválidos'
            })
    
    return render(request, 'hierarquia/login.html')

def logout_view(request):
    """View para logout de usuários"""
    logout(request)
    return redirect('login')
