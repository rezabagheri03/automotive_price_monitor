"""
WTForms for dashboard interfaces
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, IntegerField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea, Select
from database.models import User, Product
from config.database import db_manager


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('نام کاربری', validators=[
        DataRequired(message='نام کاربری الزامی است'),
        Length(min=3, max=80, message='نام کاربری باید بین 3 تا 80 کاراکتر باشد')
    ])
    password = PasswordField('رمز عبور', validators=[
        DataRequired(message='رمز عبور الزامی است')
    ])
    remember_me = BooleanField('مرا به خاطر بسپار')


class ProductForm(FlaskForm):
    """Product management form"""
    name = StringField('نام محصول', validators=[
        DataRequired(message='نام محصول الزامی است'),
        Length(min=3, max=255, message='نام محصول باید بین 3 تا 255 کاراکتر باشد')
    ])
    
    sku = StringField('کد محصول (SKU)', validators=[
        Optional(),
        Length(max=100, message='کد محصول نباید از 100 کاراکتر بیشتر باشد')
    ])
    
    category = SelectField('دسته بندی', validators=[
        DataRequired(message='دسته بندی الزامی است')
    ], choices=[
        ('اکتان و مکمل ها', 'اکتان و مکمل ها'),
        ('رینگ و لاستیک', 'رینگ و لاستیک'),
        ('سیستم خنک کننده', 'سیستم خنک کننده'),
        ('قطعات موتوری', 'قطعات موتوری'),
        ('لوازم جانبی خودرو', 'لوازم جانبی خودرو'),
        ('جلوبندی و تعلیق و سیستم فرمان', 'جلوبندی و تعلیق و سیستم فرمان'),
        ('سوخت رسانی و احتراق و اگزوز', 'سوخت رسانی و احتراق و اگزوز'),
        ('فیلتر و صافی', 'فیلتر و صافی'),
        ('گیربکس و انتقال قدرت', 'گیربکس و انتقال قدرت'),
        ('لوازم مصرفی', 'لوازم مصرفی'),
        ('روغن و مایعات', 'روغن و مایعات'),
        ('قطعات بدنه و داخل کابین', 'قطعات بدنه و داخل کابین'),
        ('لوازم الکترونیک و سنسورها', 'لوازم الکترونیک و سنسورها'),
        ('سیستم ترمز', 'سیستم ترمز')
    ])
    
    description = TextAreaField('توضیحات', validators=[
        Optional(),
        Length(max=1000, message='توضیحات نباید از 1000 کاراکتر بیشتر باشد')
    ], widget=TextArea())
    
    image_url = StringField('URL تصویر', validators=[
        Optional(),
        Length(max=500, message='URL تصویر نباید از 500 کاراکتر بیشتر باشد')
    ])
    
    woocommerce_id = IntegerField('شناسه WooCommerce', validators=[
        Optional(),
        NumberRange(min=1, message='شناسه باید عدد مثبت باشد')
    ])
    
    is_active = BooleanField('فعال')
    is_monitored = BooleanField('نظارت شود')
    
    def validate_sku(self, field):
        """Validate SKU uniqueness"""
        if field.data:
            try:
                with db_manager.get_session() as session:
                    existing = session.query(Product).filter(
                        Product.sku == field.data,
                        Product.id != int(self.product_id.data or 0)
                    ).first()
                    
                    if existing:
                        raise ValidationError('این کد محصول قبلاً استفاده شده است')
            except Exception as e:
                raise ValidationError('خطا در بررسی کد محصول')
    
    # Hidden field for edit mode
    product_id = HiddenField()


class SiteConfigForm(FlaskForm):
    """Site configuration form"""
    site_name = StringField('نام سایت', validators=[
        DataRequired(message='نام سایت الزامی است'),
        Length(min=3, max=100)
    ])
    
    base_url = StringField('URL پایه', validators=[
        DataRequired(message='URL پایه الزامی است'),
        Length(max=255)
    ])
    
    request_delay = DecimalField('تأخیر درخواست (ثانیه)', validators=[
        DataRequired(message='تأخیر درخواست الزامی است'),
        NumberRange(min=0.1, max=10.0, message='تأخیر باید بین 0.1 تا 10 ثانیه باشد')
    ], places=1)
    
    concurrent_requests = IntegerField('درخواست همزمان', validators=[
        DataRequired(message='تعداد درخواست همزمان الزامی است'),
        NumberRange(min=1, max=20, message='تعداد درخواست باید بین 1 تا 20 باشد')
    ])
    
    user_agent = TextAreaField('User Agent', validators=[
        Optional(),
        Length(max=500)
    ])
    
    is_active = BooleanField('فعال')
    is_available = BooleanField('در دسترس')


class SettingsForm(FlaskForm):
    """Dashboard settings form"""
    price_display_type = SelectField('نوع نمایش قیمت', validators=[
        DataRequired()
    ], choices=[
        ('avg', 'میانگین'),
        ('min', 'کمترین'),
        ('max', 'بیشترین')
    ])
    
    products_per_page = SelectField('تعداد محصول در صفحه', validators=[
        DataRequired()
    ], choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ])
    
    auto_refresh_interval = SelectField('بازه به‌روزرسانی خودکار', validators=[
        DataRequired()
    ], choices=[
        ('60', '1 دقیقه'),
        ('300', '5 دقیقه'),
        ('600', '10 دقیقه'),
        ('1800', '30 دقیقه'),
        ('3600', '1 ساعت')
    ])
    
    enable_notifications = BooleanField('فعال‌سازی اعلانات ایمیل')
    show_price_trends = BooleanField('نمایش روند قیمت‌ها')
    
    # WooCommerce settings
    woocommerce_url = StringField('URL فروشگاه WooCommerce', validators=[
        Optional(),
        Length(max=255)
    ])
    
    woocommerce_consumer_key = StringField('Consumer Key', validators=[
        Optional(),
        Length(max=100)
    ])
    
    woocommerce_consumer_secret = PasswordField('Consumer Secret', validators=[
        Optional(),
        Length(max=100)
    ])
    
    # Email settings
    email_host = StringField('سرور ایمیل', validators=[
        Optional(),
        Length(max=100)
    ])
    
    email_port = IntegerField('پورت ایمیل', validators=[
        Optional(),
        NumberRange(min=1, max=65535)
    ])
    
    email_user = StringField('نام کاربری ایمیل', validators=[
        Optional(),
        Email(message='فرمت ایمیل نامعتبر است')
    ])
    
    email_password = PasswordField('رمز عبور ایمیل')
    
    email_to = StringField('ایمیل گیرنده اعلانات', validators=[
        Optional(),
        Email(message='فرمت ایمیل نامعتبر است')
    ])


class ScrapingConfigForm(FlaskForm):
    """Scraping configuration form"""
    concurrent_requests = IntegerField('درخواست همزمان کل', validators=[
        DataRequired(message='تعداد درخواست همزمان الزامی است'),
        NumberRange(min=10, max=200, message='تعداد درخواست باید بین 10 تا 200 باشد')
    ])
    
    download_delay = DecimalField('تأخیر کلی (ثانیه)', validators=[
        DataRequired(message='تأخیر کلی الزامی است'),
        NumberRange(min=0.5, max=10.0, message='تأخیر باید بین 0.5 تا 10 ثانیه باشد')
    ], places=1)
    
    user_agent_rotation = BooleanField('چرخش User Agent')
    proxy_enabled = BooleanField('فعال‌سازی پروکسی')
    
    proxy_list = TextAreaField('لیست پروکسی', validators=[
        Optional()
    ], widget=TextArea(), 
    description='هر پروکسی در یک خط، فرمت: host:port یا username:password@host:port')
    
    retry_times = IntegerField('تعداد تلاش مجدد', validators=[
        DataRequired(),
        NumberRange(min=1, max=10)
    ])
    
    timeout_seconds = IntegerField('timeout (ثانیه)', validators=[
        DataRequired(),
        NumberRange(min=10, max=120)
    ])


class ManualScrapingForm(FlaskForm):
    """Manual scraping trigger form"""
    sites = SelectField('سایت‌ها', validators=[
        DataRequired()
    ], choices=[
        ('all', 'همه سایت‌ها'),
        ('autonik', 'اتونیک'),
        ('bmwstor', 'بی ام و استور'),
        ('benzstor', 'بنز استور'),
        ('mryadaki', 'مستریدکی'),
        ('carinopart', 'کارینو پارت'),
        ('japanstor', 'ژاپن استور'),
        ('shojapart', 'شجاع پارت'),
        ('luxyadak', 'لوکس یدک'),
        ('parsianlent', 'پارسیان لنت'),
        ('iranrenu', 'ایران رنو'),
        ('automoby', 'اتوموبی'),
        ('oilcity', 'شهر روغن')
    ])
    
    test_mode = BooleanField('حالت تست (محدود)')
    send_notifications = BooleanField('ارسال اعلانات', default=True)


class UserManagementForm(FlaskForm):
    """User management form"""
    username = StringField('نام کاربری', validators=[
        DataRequired(message='نام کاربری الزامی است'),
        Length(min=3, max=80)
    ])
    
    email = StringField('ایمیل', validators=[
        DataRequired(message='ایمیل الزامی است'),
        Email(message='فرمت ایمیل نامعتبر است'),
        Length(max=120)
    ])
    
    first_name = StringField('نام', validators=[
        Optional(),
        Length(max=50)
    ])
    
    last_name = StringField('نام خانوادگی', validators=[
        Optional(),
        Length(max=50)
    ])
    
    password = PasswordField('رمز عبور', validators=[
        Length(min=6, message='رمز عبور باید حداقل 6 کاراکتر باشد')
    ])
    
    confirm_password = PasswordField('تأیید رمز عبور')
    
    role = SelectField('نقش', validators=[
        DataRequired()
    ], choices=[
        ('user', 'کاربر'),
        ('admin', 'مدیر'),
        ('viewer', 'مشاهده‌گر')
    ])
    
    is_active = BooleanField('فعال', default=True)
    
    # Hidden field for edit mode
    user_id = HiddenField()
    
    def validate_confirm_password(self, field):
        """Validate password confirmation"""
        if self.password.data and field.data != self.password.data:
            raise ValidationError('تأیید رمز عبور مطابقت ندارد')
    
    def validate_username(self, field):
        """Validate username uniqueness"""
        if field.data:
            try:
                with db_manager.get_session() as session:
                    existing = session.query(User).filter(
                        User.username == field.data,
                        User.id != int(self.user_id.data or 0)
                    ).first()
                    
                    if existing:
                        raise ValidationError('این نام کاربری قبلاً استفاده شده است')
            except ValidationError:
                raise
            except:
                raise ValidationError('خطا در بررسی نام کاربری')
    
    def validate_email(self, field):
        """Validate email uniqueness"""
        if field.data:
            try:
                with db_manager.get_session() as session:
                    existing = session.query(User).filter(
                        User.email == field.data,
                        User.id != int(self.user_id.data or 0)
                    ).first()
                    
                    if existing:
                        raise ValidationError('این ایمیل قبلاً استفاده شده است')
            except ValidationError:
                raise
            except:
                raise ValidationError('خطا در بررسی ایمیل')


class BulkImportForm(FlaskForm):
    """Bulk product import form"""
    import_file = StringField('فایل CSV', validators=[
        DataRequired(message='انتخاب فایل الزامی است')
    ])
    
    price_type = SelectField('نوع قیمت برای به‌روزرسانی', validators=[
        DataRequired()
    ], choices=[
        ('avg', 'میانگین'),
        ('min', 'کمترین'),
        ('max', 'بیشترین')
    ])
    
    update_existing = BooleanField('به‌روزرسانی محصولات موجود', default=True)
    create_new = BooleanField('ایجاد محصولات جدید', default=True)
    dry_run = BooleanField('تست بدون اعمال تغییرات')


class FilterForm(FlaskForm):
    """Product filtering form"""
    search = StringField('جستجو در نام محصول')
    
    category = SelectField('دسته بندی', choices=[('', 'همه دسته‌ها')] + [
        ('اکتان و مکمل ها', 'اکتان و مکمل ها'),
        ('رینگ و لاستیک', 'رینگ و لاستیک'),
        ('سیستم خنک کننده', 'سیستم خنک کننده'),
        ('قطعات موتوری', 'قطعات موتوری'),
        ('لوازم جانبی خودرو', 'لوازم جانبی خودرو'),
        ('جلوبندی و تعلیق و سیستم فرمان', 'جلوبندی و تعلیق و سیستم فرمان'),
        ('سوخت رسانی و احتراق و اگزوز', 'سوخت رسانی و احتراق و اگزوز'),
        ('فیلتر و صافی', 'فیلتر و صافی'),
        ('گیربکس و انتقال قدرت', 'گیربکس و انتقال قدرت'),
        ('لوازم مصرفی', 'لوازم مصرفی'),
        ('روغن و مایعات', 'روغن و مایعات'),
        ('قطعات بدنه و داخل کابین', 'قطعات بدنه و داخل کابین'),
        ('لوازم الکترونیک و سنسورها', 'لوازم الکترونیک و سنسورها'),
        ('سیستم ترمز', 'سیستم ترمز')
    ])
    
    status = SelectField('وضعیت', choices=[
        ('', 'همه'),
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('monitored', 'تحت نظارت'),
        ('not_monitored', 'بدون نظارت'),
        ('has_prices', 'دارای قیمت'),
        ('no_prices', 'بدون قیمت')
    ])
    
    price_min = DecimalField('حداقل قیمت', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    
    price_max = DecimalField('حداکثر قیمت', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    
    sort_by = SelectField('مرتب‌سازی بر اساس', choices=[
        ('name', 'نام'),
        ('category', 'دسته بندی'),
        ('price_avg', 'قیمت میانگین'),
        ('price_min', 'کمترین قیمت'),
        ('price_max', 'بیشترین قیمت'),
        ('updated_at', 'آخرین به‌روزرسانی')
    ], default='name')
    
    sort_order = SelectField('ترتیب', choices=[
        ('asc', 'صعودی'),
        ('desc', 'نزولی')
    ], default='asc')


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('رمز عبور فعلی', validators=[
        DataRequired(message='رمز عبور فعلی الزامی است')
    ])
    
    new_password = PasswordField('رمز عبور جدید', validators=[
        DataRequired(message='رمز عبور جدید الزامی است'),
        Length(min=6, message='رمز عبور باید حداقل 6 کاراکتر باشد')
    ])
    
    confirm_password = PasswordField('تأیید رمز عبور جدید', validators=[
        DataRequired(message='تأیید رمز عبور الزامی است')
    ])
    
    def validate_confirm_password(self, field):
        """Validate password confirmation"""
        if field.data != self.new_password.data:
            raise ValidationError('تأیید رمز عبور مطابقت ندارد')


class SearchForm(FlaskForm):
    """Advanced search form"""
    query = StringField('جستجو', validators=[
        DataRequired(message='عبارت جستجو الزامی است'),
        Length(min=2, max=100)
    ])
    
    search_in = SelectField('جستجو در', choices=[
        ('name', 'نام محصول'),
        ('description', 'توضیحات'),
        ('sku', 'کد محصول'),
        ('all', 'همه موارد')
    ], default='all')
    
    category_filter = SelectField('فیلتر دسته بندی', choices=[('', 'همه دسته‌ها')])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate category choices dynamically
        self._populate_categories()
    
    def _populate_categories(self):
        """Populate category choices from database"""
        try:
            with db_manager.get_session() as session:
                categories = session.query(Product.category).distinct().all()
                category_choices = [('', 'همه دسته‌ها')]
                category_choices.extend([(cat[0], cat[0]) for cat in categories if cat[0]])
                self.category_filter.choices = category_choices
        except:
            pass  # Use default choices if database query fails
