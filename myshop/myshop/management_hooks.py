from django.contrib.auth import get_user_model

def create_live_admin():
    User = get_user_model()
    username = 'admin_meet'
    email = 'meet@example.com'
    password = 'MySecurePassword123' 

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"--> Superuser '{username}' successfully created for live site!")
    else:
        print(f"--> Superuser '{username}' already exists.")