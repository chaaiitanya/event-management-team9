from users.forms import LoginForm

def get_login_form(request):
    login_form = LoginForm()
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
    return {
        'login_form': login_form,
    }