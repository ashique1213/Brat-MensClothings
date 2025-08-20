# BratMensClothing - Django E-Commerce Platform

BratMensClothing is a Django-based e-commerce platform tailored for men's clothing, featuring products like pants, t-shirts, jeans, and shirts. Built using Django's Model-View-Template (MVT) architecture, it offers a robust and scalable solution for online retail with features like user authentication, product management, shopping cart, order processing, wishlist, coupons, offers, wallet functionality, and sales reporting. The project integrates with Cloudinary for media storage, Razorpay for payments, and Django Allauth for authentication, including Google OAuth.

## Features
- **Product Categories**: Men's clothing including pants, t-shirts, jeans, and shirts.
- **User Authentication**: Email-based and Google OAuth login/registration via Django Allauth.
- **Shopping Cart**: Add, update, or remove items with real-time updates.
- **Order Management**: Place and track orders with Razorpay payment integration.
- **Wishlist**: Save products for future purchase.
- **Coupons & Offers**: Apply discounts during checkout.
- **Wallet**: Manage user funds for transactions.
- **Sales Reports**: Admin dashboard for sales analytics.
- **Media Management**: Cloudinary for storing product images and media.
- **Responsive Design**: Mobile-friendly templates for a seamless user experience.

## Tech Stack
- **Framework**: Django 5.1.2 (Python)
- **Architecture**: Model-View-Template (MVT)
- **Database**: PostgreSQL (via `dj_database_url`)
- **Authentication**: Django Allauth (Google OAuth)
- **Payment Gateway**: Razorpay
- **Media Storage**: Cloudinary
- **Static Files**: Whitenoise
- **Email Service**: Gmail SMTP for notifications
- **Frontend**: Django templates (HTML, CSS, JavaScript)
- **Environment Management**: python-dotenv

## Setup Instructions
### Prerequisites
- Python 3.8+
- PostgreSQL
- Git
- Cloudinary account
- Razorpay account
- Gmail account for SMTP
- Node.js (optional for frontend assets)

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ashique1213/Brat-MensClothings.git
   cd Brat-MensClothings
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note*: If `requirements.txt` is not present, install dependencies manually:
   ```bash
   pip install django==5.1.2 dj-database-url python-dotenv razorpay cloudinary django-allauth whitenoise
   ```

4. **Create `.env` File**:
   In the project root, create a `.env` file with the following:
   ```env
   SECRET_KEY=your-django-secret-key
   DATABASE_URL=postgres://user:password@host:port/dbname
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-email-password
   cloud_name=your-cloudinary-cloud-name
   api_key=your-cloudinary-api-key
   api_secret=your-cloudinary-api-secret
   RAZORPAY_KEY_ID=your-razorpay-key-id
   RAZORPAY_KEY_SECRET=your-razorpay-key-secret
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

5. **Apply Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Collect Static Files**:
   ```bash
   python manage.py collectstatic
   ```

7. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Access the app at `http://127.0.0.1:8000`.

## Configuration
- **Django Settings**: `settings.py` is set for development (`DEBUG = True`). For production, set `DEBUG = False` and configure `ALLOWED_HOSTS` with your domain.
- **Database**: PostgreSQL with `dj_database_url`. Update `DATABASE_URL` in `.env`.
- **Static Files**: Served via Whitenoise (`STATICFILES_STORAGE`).
- **Media Files**: Stored on Cloudinary (`DEFAULT_FILE_STORAGE`).
- **Authentication**: Django Allauth for email and Google login. Set Google OAuth credentials in `.env`.
- **Payments**: Razorpay integration requires `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
- **Email**: Gmail SMTP for notifications (e.g., order confirmations, password resets).

## Django MVT Architecture
The project adheres to Django's **Model-View-Template (MVT)** pattern:
- **Models**: Define database schema for entities like users (`accounts.Users`), products, orders, carts, wishlists, coupons, offers, wallets, and sales reports.
- **Views**: Handle logic and process requests, defined in app-specific views (e.g., `products.views`, `cart.views`).
- **Templates**: Render HTML in `templates/` using Django's template engine, organized by app.
- **URLs**: Map requests to views via `bratmensclothing.urls` and app-specific URL configs.
- **Context Processors**: Provide global data (e.g., authentication status) to templates.

This structure ensures modularity and maintainability.

## Environment Variables
The `.env` file stores sensitive configurations:
- `SECRET_KEY`: Django cryptographic key.
- `DATABASE_URL`: PostgreSQL connection string.
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: Gmail SMTP credentials.
- `cloud_name`, `api_key`, `api_secret`: Cloudinary credentials.
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`: Razorpay credentials.
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: Google OAuth credentials.

## Running the Project
1. **Development**:
   ```bash
   python manage.py runserver
   ```
   Access at `http://127.0.0.1:8000`.

2. **Production**:
   - Use a WSGI server (e.g., Gunicorn) and a reverse proxy (e.g., Nginx).
   - Set `DEBUG = False` and update `ALLOWED_HOSTS`.
   - Ensure `DATABASE_URL` points to a production database.

3. **Admin Dashboard**:
   Access at `/admin` using superuser credentials.

## Contributing
1. Fork the repository: `https://github.com/ashique1213/Brat-MensClothings`.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Open a pull request on GitHub.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details (if available in the repository).

---

For issues or questions, open an issue on [GitHub](https://github.com/ashique1213/Brat-MensClothings) or contact the maintainer.

*Generated on August 20, 2025, at 12:34 PM IST.*
