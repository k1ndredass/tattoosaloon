from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Расширенная модель пользователя с ролями"""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('master', 'Тату-мастер'),
        ('user', 'Пользователь'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Роль'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    def is_master(self):
        return self.role == 'master' or self.is_admin()
    
    def __str__(self):
        return self.username


class TattooStyle(models.Model):
    """Стили татуировок"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название стиля')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Стиль татуировки'
        verbose_name_plural = 'Стили татуировок'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tattoo(models.Model):
    """Модель татуировки"""
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    style = models.ForeignKey(
        TattooStyle,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Стиль'
    )
    master = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tattoos',
        limit_choices_to={'role': 'master'},
        verbose_name='Мастер'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Цена'
    )
    image = models.ImageField(upload_to='tattoos/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    views_count = models.IntegerField(default=0, verbose_name='Количество просмотров')
    
    class Meta:
        verbose_name = 'Татуировка'
        verbose_name_plural = 'Татуировки'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Appointment(models.Model):
    """Запись на сеанс"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_appointments',
        verbose_name='Клиент'
    )
    master = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='master_appointments',
        limit_choices_to={'role': 'master'},
        verbose_name='Мастер'
    )
    tattoo = models.ForeignKey(
        Tattoo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Татуировка'
    )
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    items_summary = models.TextField(blank=True, verbose_name='Состав заказа')
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Сумма заказа'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Запись на сеанс'
        verbose_name_plural = 'Записи на сеансы'
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.client.username} - {self.master.username} ({self.date})"


class Review(models.Model):
    """Отзывы"""
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор'
    )
    master = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='master_reviews',
        limit_choices_to={'role': 'master'},
        null=True,
        blank=True,
        verbose_name='Мастер'
    )
    tattoo = models.ForeignKey(
        Tattoo,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
        verbose_name='Татуировка'
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка'
    )
    text = models.TextField(verbose_name='Текст отзыва')
    is_moderated = models.BooleanField(default=False, verbose_name='Промодерирован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.author.username} - {self.rating} звезд"


class CartItem(models.Model):
    """Элемент корзины"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Пользователь'
    )
    tattoo = models.ForeignKey(
        Tattoo,
        on_delete=models.CASCADE,
        verbose_name='Татуировка'
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    
    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ['user', 'tattoo']
    
    def __str__(self):
        return f"{self.user.username} - {self.tattoo.title}"


class Lead(models.Model):
    """Заявка с сайта (консультация / звонок / запись)"""
    LEAD_TYPE_CHOICES = [
        ('consultation', 'Бесплатная консультация'),
        ('callback', 'Обратный звонок'),
        ('session', 'Запись на сеанс'),
    ]

    name = models.CharField(max_length=150, verbose_name='Имя')
    phone = models.CharField(max_length=30, verbose_name='Телефон')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    lead_type = models.CharField(
        max_length=20,
        choices=LEAD_TYPE_CHOICES,
        default='consultation',
        verbose_name='Тип заявки'
    )
    preferred_master = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'master'},
        verbose_name='Предпочитаемый мастер'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    processed = models.BooleanField(default=False, verbose_name='Обработана')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_lead_type_display()} — {self.name}"


class CareProduct(models.Model):
    """Дополнительные товары/услуги ухода, выдаются на сеансе"""
    title = models.CharField(max_length=200, verbose_name='Название')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='care_products/', blank=True, null=True, verbose_name='Изображение')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')

    class Meta:
        verbose_name = 'Товар ухода'
        verbose_name_plural = 'Товары ухода'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title

