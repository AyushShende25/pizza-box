from app.auth.model import User


def verification_email_html(link: str) -> str:
    return f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """


def welcome_email_html(user: User):
    return f"""
    <h1>Welcome to pizza-box, {user.first_name}</h1>
    <p>Start devouring our delicious range of pizzas</p>
    """
