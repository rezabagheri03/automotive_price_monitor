"""
Dashboard routes and views
"""
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, send_file
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename

from .models import DashboardUser, dashboard_settings
from .forms import (LoginForm, ProductForm, SettingsForm, SiteConfigForm, 
                   ManualScrapingForm, UserManagementForm, BulkImportForm,
                   FilterForm, ChangePasswordForm, SearchForm)
from database.models import Product, PriceHistory, ScrapingLog, SiteConfig, User
from config.database import db_manager
from data_processor.price_calculator import PriceCalculator
from data_processor.csv_generator import CSVGenerator
from woocommerce_integration.csv_importer import CSVImporter
from woocommerce_integration.batch_processor import BatchProcessor
from utils.monitoring import system_monitor
from utils.email_notifier import email_notifier
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)


# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = DashboardUser.authenticate(form.username.data, form.password.data)
        
        if user:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('با موفقیت وارد شدید', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('با موفقیت خارج شدید', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.authenticate(current_user.username, form.current_password.data):
            flash('رمز عبور فعلی اشتباه است', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Change password
        if current_user.change_password(form.new_password.data):
            flash('رمز عبور با موفقیت تغییر یافت', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('خطا در تغییر رمز عبور', 'error')
    
    return render_template('auth/change_password.html', form=form)


# Main dashboard routes
@main_bp.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    try:
        # Get system statistics
        system_stats = system_monitor.get_system_stats()
        db_stats = system_monitor.get_database_stats()
        scraping_perf = system_monitor.get_scraping_performance()
        
        # Get recent activities
        with db_manager.get_session() as session:
            recent_logs = session.query(ScrapingLog).order_by(
                ScrapingLog.start_time.desc()
            ).limit(10).all()
            
            # Get price statistics
            price_calculator = PriceCalculator()
            category_stats = price_calculator.get_category_price_summary()
        
        # Get site status
        site_status = {}
        with db_manager.get_session() as session:
            sites = session.query(SiteConfig).all()
            for site in sites:
                site_status[site.site_name] = {
                    'active': site.is_active,
                    'available': site.is_available,
                    'last_success': site.last_successful_scrape
                }
        
        return render_template('dashboard/index.html',
                             system_stats=system_stats,
                             db_stats=db_stats,
                             scraping_perf=scraping_perf,
                             recent_logs=recent_logs,
                             category_stats=category_stats,
                             site_status=site_status)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('خطا در بارگذاری داشبورد', 'error')
        return render_template('dashboard/index.html')


@main_bp.route('/products')
@login_required
def products():
    """Product management page"""
    form = FilterForm()
    page = request.args.get('page', 1, type=int)
    per_page = int(dashboard_settings.get('products_per_page', 25))
    
    try:
        with db_manager.get_session() as session:
            # Build query
            query = session.query(Product)
            
            # Apply filters
            if form.search.data:
                query = query.filter(Product.name.contains(form.search.data))
            
            if form.category.data:
                query = query.filter(Product.category == form.category.data)
            
            if form.status.data == 'active':
                query = query.filter(Product.is_active == True)
            elif form.status.data == 'inactive':
                query = query.filter(Product.is_active == False)
            elif form.status.data == 'monitored':
                query = query.filter(Product.is_monitored == True)
            elif form.status.data == 'not_monitored':
                query = query.filter(Product.is_monitored == False)
            
            # Apply sorting
            if form.sort_by.data == 'name':
                query = query.order_by(Product.name.asc() if form.sort_order.data == 'asc' else Product.name.desc())
            elif form.sort_by.data == 'category':
                query = query.order_by(Product.category.asc() if form.sort_order.data == 'asc' else Product.category.desc())
            else:
                query = query.order_by(Product.updated_at.desc())
            
            # Paginate results
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            products = pagination.items
            
            return render_template('products/list.html',
                                 products=products,
                                 pagination=pagination,
                                 form=form)
    
    except Exception as e:
        logger.error(f"Products page error: {e}")
        flash('خطا در بارگذاری محصولات', 'error')
        return render_template('products/list.html', products=[], form=form)


@main_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('main.products'))
    
    form = ProductForm()
    
    if form.validate_on_submit():
        try:
            with db_manager.get_session() as session:
                product = Product(
                    name=form.name.data,
                    sku=form.sku.data,
                    category=form.category.data,
                    description=form.description.data,
                    image_url=form.image_url.data,
                    woocommerce_id=form.woocommerce_id.data,
                    is_active=form.is_active.data,
                    is_monitored=form.is_monitored.data,
                    created_at=datetime.utcnow()
                )
                session.add(product)
                
                flash('محصول با موفقیت اضافه شد', 'success')
                return redirect(url_for('main.products'))
        
        except Exception as e:
            logger.error(f"Add product error: {e}")
            flash('خطا در افزودن محصول', 'error')
    
    return render_template('products/form.html', form=form, title='افزودن محصول')


@main_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit existing product"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('main.products'))
    
    try:
        with db_manager.get_session() as session:
            product = session.query(Product).get_or_404(product_id)
            
            form = ProductForm(obj=product)
            form.product_id.data = product_id
            
            if form.validate_on_submit():
                product.name = form.name.data
                product.sku = form.sku.data
                product.category = form.category.data
                product.description = form.description.data
                product.image_url = form.image_url.data
                product.woocommerce_id = form.woocommerce_id.data
                product.is_active = form.is_active.data
                product.is_monitored = form.is_monitored.data
                product.updated_at = datetime.utcnow()
                
                flash('محصول با موفقیت به‌روزرسانی شد', 'success')
                return redirect(url_for('main.products'))
            
            return render_template('products/form.html', 
                                 form=form, 
                                 title='ویرایش محصول',
                                 product=product)
    
    except Exception as e:
        logger.error(f"Edit product error: {e}")
        flash('خطا در ویرایش محصول', 'error')
        return redirect(url_for('main.products'))


@main_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """Product detail page with price history"""
    try:
        with db_manager.get_session() as session:
            product = session.query(Product).get_or_404(product_id)
            
            # Get price history
            price_history = session.query(PriceHistory).filter(
                PriceHistory.product_id == product_id
            ).order_by(PriceHistory.scraped_at.desc()).limit(50).all()
            
            # Get price trends
            price_calculator = PriceCalculator()
            trends = price_calculator.get_price_trends(product_id, days=30)
            
            return render_template('products/detail.html',
                                 product=product,
                                 price_history=price_history,
                                 trends=trends)
    
    except Exception as e:
        logger.error(f"Product detail error: {e}")
        flash('خطا در بارگذاری جزئیات محصول', 'error')
        return redirect(url_for('main.products'))


@main_bp.route('/scraping')
@login_required
def scraping_dashboard():
    """Scraping management dashboard"""
    try:
        with db_manager.get_session() as session:
            # Get site configurations
            sites = session.query(SiteConfig).all()
            
            # Get recent scraping logs
            recent_logs = session.query(ScrapingLog).order_by(
                ScrapingLog.start_time.desc()
            ).limit(20).all()
            
            # Get scraping performance
            performance = system_monitor.get_scraping_performance()
            
            return render_template('scraping/dashboard.html',
                                 sites=sites,
                                 recent_logs=recent_logs,
                                 performance=performance)
    
    except Exception as e:
        logger.error(f"Scraping dashboard error: {e}")
        flash('خطا در بارگذاری داشبورد اسکرپینگ', 'error')
        return render_template('scraping/dashboard.html')


@main_bp.route('/scraping/manual', methods=['GET', 'POST'])
@login_required
def manual_scraping():
    """Manual scraping trigger"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('main.scraping_dashboard'))
    
    form = ManualScrapingForm()
    
    if form.validate_on_submit():
        try:
            # Start scraping process
            import subprocess
            import sys
            
            cmd = [sys.executable, 'scripts/run_scraper.py']
            
            if form.sites.data != 'all':
                cmd.extend(['--spider', form.sites.data])
            
            if form.test_mode.data:
                cmd.append('--test')
            
            if not form.send_notifications.data:
                cmd.append('--no-notify')
            
            # Run in background
            subprocess.Popen(cmd, cwd=current_app.root_path)
            
            flash('اسکرپینگ با موفقیت شروع شد', 'success')
            return redirect(url_for('main.scraping_dashboard'))
        
        except Exception as e:
            logger.error(f"Manual scraping error: {e}")
            flash('خطا در شروع اسکرپینگ', 'error')
    
    return render_template('scraping/manual.html', form=form)


@main_bp.route('/woocommerce')
@login_required
def woocommerce_dashboard():
    """WooCommerce integration dashboard"""
    try:
        # Get WooCommerce statistics
        csv_importer = CSVImporter()
        import_stats = csv_importer.get_import_stats()
        
        # Get recent CSV files
        csv_generator = CSVGenerator()
        export_files = csv_generator.get_export_files()
        
        return render_template('woocommerce/dashboard.html',
                             import_stats=import_stats,
                             export_files=export_files)
    
    except Exception as e:
        logger.error(f"WooCommerce dashboard error: {e}")
        flash('خطا در بارگذاری داشبورد WooCommerce', 'error')
        return render_template('woocommerce/dashboard.html')


@main_bp.route('/woocommerce/update-prices', methods=['POST'])
@login_required
def update_woocommerce_prices():
    """Update WooCommerce prices"""
    if not current_user.is_admin:
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403
    
    try:
        price_type = request.json.get('price_type', 'avg')
        dry_run = request.json.get('dry_run', False)
        
        # Start price update process
        import subprocess
        import sys
        
        cmd = [sys.executable, 'scripts/update_prices.py']
        cmd.extend(['--price-type', price_type])
        
        if dry_run:
            cmd.append('--dry-run')
        
        # Run in background
        process = subprocess.Popen(cmd, cwd=current_app.root_path)
        
        return jsonify({
            'success': True,
            'message': 'به‌روزرسانی قیمت‌ها شروع شد'
        })
    
    except Exception as e:
        logger.error(f"Update prices error: {e}")
        return jsonify({'error': 'خطا در به‌روزرسانی قیمت‌ها'}), 500


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Application settings page"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = SettingsForm()
    
    # Populate form with current settings
    if request.method == 'GET':
        form.price_display_type.data = dashboard_settings.get('price_display_type')
        form.products_per_page.data = str(dashboard_settings.get('products_per_page'))
        form.auto_refresh_interval.data = str(dashboard_settings.get('auto_refresh_interval'))
        form.enable_notifications.data = dashboard_settings.get('enable_notifications')
        form.show_price_trends.data = dashboard_settings.get('show_price_trends')
    
    if form.validate_on_submit():
        try:
            # Update dashboard settings
            dashboard_settings.update({
                'price_display_type': form.price_display_type.data,
                'products_per_page': int(form.products_per_page.data),
                'auto_refresh_interval': int(form.auto_refresh_interval.data),
                'enable_notifications': form.enable_notifications.data,
                'show_price_trends': form.show_price_trends.data
            })
            
            flash('تنظیمات با موفقیت ذخیره شد', 'success')
            return redirect(url_for('main.settings'))
        
        except Exception as e:
            logger.error(f"Settings update error: {e}")
            flash('خطا در ذخیره تنظیمات', 'error')
    
    return render_template('settings/index.html', form=form)


@main_bp.route('/users')
@login_required
def users():
    """User management page"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        with db_manager.get_session() as session:
            users = session.query(User).order_by(User.created_at.desc()).all()
            return render_template('users/list.html', users=users)
    
    except Exception as e:
        logger.error(f"Users page error: {e}")
        flash('خطا در بارگذاری کاربران', 'error')
        return render_template('users/list.html', users=[])


@main_bp.route('/reports')
@login_required
def reports():
    """Reports and analytics page"""
    try:
        # Get report data
        price_calculator = PriceCalculator()
        category_stats = price_calculator.get_category_price_summary()
        
        # Get system health
        health = system_monitor.check_health()
        
        return render_template('reports/index.html',
                             category_stats=category_stats,
                             health=health)
    
    except Exception as e:
        logger.error(f"Reports page error: {e}")
        flash('خطا در بارگذاری گزارشات', 'error')
        return render_template('reports/index.html')


# API routes
@api_bp.route('/health')
def health_check():
    """API health check endpoint"""
    try:
        health = system_monitor.check_health()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats')
@login_required
def api_stats():
    """Get system statistics"""
    try:
        stats = {
            'system': system_monitor.get_system_stats(),
            'database': system_monitor.get_database_stats(),
            'scraping': system_monitor.get_scraping_performance()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/products/<int:product_id>/prices')
@login_required
def product_prices_api(product_id):
    """Get product price history API"""
    try:
        days = request.args.get('days', 30, type=int)
        
        price_calculator = PriceCalculator()
        trends = price_calculator.get_price_trends(product_id, days=days)
        
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/export/csv/<price_type>')
@login_required
def export_csv_api(price_type):
    """Generate and download CSV file"""
    if not current_user.is_admin:
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403
    
    try:
        csv_generator = CSVGenerator()
        
        if price_type == 'woocommerce':
            csv_path = csv_generator.generate_woocommerce_csv('avg')
        elif price_type == 'comparison':
            csv_path = csv_generator.generate_price_comparison_csv()
        elif price_type == 'inventory':
            csv_path = csv_generator.generate_inventory_report_csv()
        else:
            return jsonify({'error': 'نوع CSV نامعتبر'}), 400
        
        return send_file(csv_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({'error': 'خطا در تولید فایل CSV'}), 500


# Error handlers
@main_bp.app_errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500


@main_bp.app_errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return render_template('errors/403.html'), 403
