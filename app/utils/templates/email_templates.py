from app.auth.model import User


def verification_email_html(link: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background-color: #fff7f0; border-radius: 8px;">
        <h1 style="color: #d35400; text-align: center;">🍕 Verify Your Email</h1>
        <p style="font-size: 16px; color: #555;">
            Thanks for signing up with <strong>PizzaBox</strong>!  
            Please confirm your email address to start ordering your favorite pizzas.
        </p>
        <p style="text-align: center;">
            <a href="{link}" style="background-color: #e67e22; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px;">
                Verify Email
            </a>
        </p>
        <p style="font-size: 14px; color: #888;">If you did not sign up for PizzaBox, you can ignore this email.</p>
    </div>
    """


def welcome_email_html(user: User) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; background-color: #fff7f0; border-radius: 8px;">
        <h1 style="color: #d35400; text-align: center;">🍕 Welcome to PizzaBox, {user.first_name}!</h1>
        <p style="font-size: 16px; color: #555;">
            We're thrilled to have you join the PizzaBox family!  
            Explore our delicious range of pizzas, sides, and desserts — freshly baked just for you.
        </p>
        <p style="font-size: 14px; color: #888;">Craving starts here... 🍕</p>
    </div>
    """


def forgot_password_email_html(link: str) -> str:
    return f"""
    <h1 style="color:#c0392b;">Reset Your Password</h1>
    <p>We received a request to reset your Pizza Box account password.</p>
    <p><a href="{link}" style="color:#fff;background:#c0392b;padding:10px 15px;border-radius:5px;text-decoration:none;">Reset Password</a></p>
    <p style="font-size:12px;color:#555;">If you didn’t request this, you can safely ignore this email.</p>
    """


def password_reset_confirmation_email_html(user: User) -> str:
    return f"""
    <h1 style="color:#2980b9;">Your Password Has Been Changed</h1>
    <p>Hello {user.first_name},</p>
    <p>Your Pizza Box account password was successfully updated.</p>
    <p style="color:#e74c3c;">If this wasn’t you, please contact our support immediately.</p>
    """
