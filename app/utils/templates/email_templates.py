from app.auth.model import User
from app.orders.model import Order


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


def order_confirmation_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#2980b9;">Order Placed Successfully</h1>
    <p>Hello {user.first_name},</p>
    <p>Thank you for ordering from Pizza Box!</p>
    <p>Your order <strong>#{order.order_no}</strong> has been received successfully.</p>

    <p>
        <strong>Order Total:</strong> ₹{order.total:.2f}
    </p>

    <p>
        We’ll keep you updated as your order progresses.
    </p>

    <p>Thank you for choosing Pizza Box!</p>
    """


def payment_successful_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#27ae60;">Payment Successful</h1>
    <p>Hello {user.first_name},</p>

    <p>
        Your payment for order <strong>#{order.order_no}</strong>
        was successfully received.
    </p>

    <p>
        <strong>Amount Paid:</strong> ₹{order.total:.2f}
    </p>

    <p>
        Your order is now confirmed and will be prepared shortly.
    </p>

    <p>Thank you for choosing Pizza Box!</p>
    """


def payment_failed_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#e74c3c;">Payment Failed</h1>
    <p>Hello {user.first_name},</p>

    <p>
        We were unable to process the payment for order
        <strong>#{order.order_no}</strong>.
    </p>

    <p>
        <strong>Amount:</strong> ₹{order.total:.2f}
    </p>

    <p>
        Please try the payment again to complete your order.
    </p>

    <p>
        If you believe this was a mistake, please contact our support team.
    </p>
    """


def order_confirmed_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#27ae60;">Order Confirmed</h1>
    <p>Hello {user.first_name},</p>

    <p>
        Your order <strong>#{order.order_no}</strong> has been confirmed.
    </p>

    <p>
        <strong>Order Total:</strong> ₹{order.total:.2f}
    </p>

    <p>
        We’ll start preparing your order shortly.
    </p>

    <p>Thank you for ordering from Pizza Box!</p>
    """


def order_preparing_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#f39c12;">Your Order Is Being Prepared</h1>
    <p>Hello {user.first_name},</p>

    <p>
        Great news! Your order <strong>#{order.order_no}</strong>
        is now being prepared.
    </p>

    <p>
        We'll let you know when your order is on its way.
    </p>

    <p>Thank you for choosing Pizza Box!</p>
    """


def order_out_for_delivery_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#2980b9;">Your Order Is On Its Way!</h1>
    <p>Hello {user.first_name},</p>

    <p>
        Your order <strong>#{order.order_no}</strong>
        is out for delivery.
    </p>

    <p>
        Please keep your phone available in case the delivery partner
        needs to contact you.
    </p>

    <p>Enjoy your meal!</p>
    """


def order_delivered_email_html(
    user: User,
    order: Order,
) -> str:
    return f"""
    <h1 style="color:#27ae60;">Order Delivered</h1>
    <p>Hello {user.first_name},</p>

    <p>
        Your order <strong>#{order.order_no}</strong>
        has been delivered successfully.
    </p>

    <p>
        We hope you enjoyed your meal!
    </p>

    <p>Thank you for choosing Pizza Box.</p>
    """


def order_cancelled_email_html(
    user: User,
    order: Order,
    reason: str | None = None,
) -> str:
    reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""

    return f"""
    <h1 style="color:#e74c3c;">Order Cancelled</h1>
    <p>Hello {user.first_name},</p>

    <p>
        Your order <strong>#{order.order_no}</strong>
        has been cancelled.
    </p>

    {reason_html}

    <p>
        If you have any questions about this cancellation,
        please contact our support team.
    </p>

    <p>We apologize for the inconvenience.</p>
    """
