

def include_login_form(request):
    from .forms import LoginForm
    form = LoginForm()
    return {'login_form': form}

