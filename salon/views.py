from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django import forms
from .models import User, Tattoo, TattooStyle, Appointment, Review, CartItem, Lead, CareProduct
from .forms import (
    CustomUserCreationForm, TattooForm, AppointmentForm, AppointmentAdminForm,
    ReviewForm, UserForm, LeadForm, CareProductForm
)

def _care_addons_selected(request):
    """Возвращает множество выбранных ID доп.товаров из сессии"""
    return set(request.session.get('care_addons', []))


def _care_addons_save(request, ids):
    request.session['care_addons'] = list(ids)


def is_admin(user):
    return user.is_authenticated and user.is_admin()


def is_master(user):
    return user.is_authenticated and user.is_master()


# ==================== Общие представления ====================

def home(request):
    """Главная страница"""
    featured_tattoos = Tattoo.objects.filter(is_active=True)[:9]
    masters = User.objects.filter(role='master')[:8]
    recent_reviews = Review.objects.filter(is_moderated=True)[:6]
    lead_form = LeadForm()
    
    context = {
        'featured_tattoos': featured_tattoos,
        'masters': masters,
        'recent_reviews': recent_reviews,
        'lead_form': lead_form,
    }
    return render(request, 'salon/home.html', context)


def about(request):
    """Страница О нас"""
    masters = User.objects.filter(role='master')
    return render(request, 'salon/about.html', {'masters': masters})


def catalog(request):
    """Каталог татуировок"""
    tattoos = Tattoo.objects.filter(is_active=True)
    styles = TattooStyle.objects.all()
    
    # Фильтрация по стилю
    style_filter = request.GET.get('style')
    if style_filter:
        tattoos = tattoos.filter(style_id=style_filter)
    
    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        tattoos = tattoos.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_asc':
        tattoos = tattoos.order_by('price')
    elif sort_by == 'price_desc':
        tattoos = tattoos.order_by('-price')
    elif sort_by == 'popularity':
        tattoos = tattoos.annotate(reviews_count=Count('reviews')).order_by('-reviews_count', '-views_count')
    elif sort_by == 'rating':
        tattoos = tattoos.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        tattoos = tattoos.order_by('-created_at')
    
    paginator = Paginator(tattoos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'styles': styles,
        'current_style': style_filter,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'salon/catalog.html', context)


def tattoo_detail(request, pk):
    """Детальная страница татуировки"""
    tattoo = get_object_or_404(Tattoo, pk=pk, is_active=True)
    tattoo.views_count += 1
    tattoo.save(update_fields=['views_count'])
    
    related_tattoos = Tattoo.objects.filter(
        style=tattoo.style,
        is_active=True
    ).exclude(pk=pk)[:4]
    
    reviews = Review.objects.filter(tattoo=tattoo, is_moderated=True)
    
    context = {
        'tattoo': tattoo,
        'related_tattoos': related_tattoos,
        'reviews': reviews,
    }
    return render(request, 'salon/tattoo_detail.html', context)


def reviews(request):
    """Страница отзывов"""
    reviews_list = Review.objects.filter(is_moderated=True)
    
    # Фильтрация по мастеру
    master_filter = request.GET.get('master')
    if master_filter:
        reviews_list = reviews_list.filter(master_id=master_filter)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'rating_desc':
        reviews_list = reviews_list.order_by('-rating', '-created_at')
    elif sort_by == 'rating_asc':
        reviews_list = reviews_list.order_by('rating', '-created_at')
    else:
        reviews_list = reviews_list.order_by('-created_at')
    
    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    masters = User.objects.filter(role='master')
    
    context = {
        'page_obj': page_obj,
        'masters': masters,
        'current_master': master_filter,
        'current_sort': sort_by,
    }
    return render(request, 'salon/reviews.html', context)


@login_required
def add_review(request):
    """Добавление отзыва"""
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.author = request.user
            # Администраторы могут публиковать сразу
            if request.user.is_admin():
                review.is_moderated = True
            review.save()
            messages.success(request, 'Отзыв успешно добавлен!')
            return redirect('reviews')
    else:
        form = ReviewForm()
    
    return render(request, 'salon/add_review.html', {'form': form})


@login_required
def submit_lead(request):
    """Обработка заявок (консультация / звонок / запись)"""
    if request.method != 'POST':
        messages.error(request, 'Неверный метод')
        return redirect('home')

    form = LeadForm(request.POST)
    if form.is_valid():
        lead = form.save()
        subject = f"Новая заявка: {lead.get_lead_type_display()}"
        body = (
            f"Имя: {lead.name}\n"
            f"Телефон: {lead.phone}\n"
            f"Email: {lead.email or '—'}\n"
            f"Тип: {lead.get_lead_type_display()}\n"
            f"Предпочитаемый мастер: {lead.preferred_master or 'Любой'}\n"
            f"Комментарий: {lead.comment or '—'}\n"
            f"Создано: {lead.created_at}\n"
        )
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [getattr(settings, 'LEAD_NOTIFY_EMAIL', settings.DEFAULT_FROM_EMAIL)],
                fail_silently=True,
            )
        except Exception:
            pass  # если не отправилось — не блокируем

        messages.success(request, 'Заявка отправлена! Мы свяжемся с вами.')
    else:
        messages.error(request, 'Исправьте ошибки в форме.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def contacts(request):
    """Страница контактов"""
    lead_form = LeadForm()
    return render(request, 'salon/contacts.html', {'lead_form': lead_form})


# ==================== Корзина ====================

@login_required
def cart(request):
    """Корзина пользователя"""
    cart_items = CartItem.objects.filter(user=request.user)
    selected_addons = _care_addons_selected(request)
    products = CareProduct.objects.filter(is_active=True)
    addons_dict = {str(p.id): p for p in products}
    addons = [addons_dict[i] for i in selected_addons if i in addons_dict]
    addons_total = sum(p.price for p in addons)
    total_price = sum(item.tattoo.price for item in cart_items) + addons_total
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'care_products': products,
        'selected_addons': addons,
        'addons_total': addons_total,
    }
    return render(request, 'salon/cart.html', context)


@login_required
def add_to_cart(request, tattoo_id):
    """Добавление татуировки в корзину"""
    tattoo = get_object_or_404(Tattoo, pk=tattoo_id, is_active=True)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        tattoo=tattoo
    )
    if created:
        messages.success(request, f'Татуировка "{tattoo.title}" добавлена в корзину')
    else:
        messages.info(request, 'Татуировка уже в корзине')
    return redirect('tattoo_detail', pk=tattoo_id)


@login_required
def remove_from_cart(request, cart_item_id):
    """Удаление из корзины"""
    cart_item = get_object_or_404(CartItem, pk=cart_item_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Татуировка удалена из корзины')
    return redirect('cart')


@login_required
def cart_checkout(request):
    """Подготовка записи из корзины: собираем состав заказа и доп. товары"""
    if request.method != 'POST':
        return redirect('cart')

    cart_items = list(CartItem.objects.filter(user=request.user).select_related('tattoo'))

    selected_addons = list(_care_addons_selected(request))
    products = CareProduct.objects.filter(is_active=True)
    addons_dict = {str(p.id): p for p in products}

    summary_lines = []
    total = 0

    for item in cart_items:
        line = f"Татуировка: {item.tattoo.title} — {item.tattoo.price} ₽"
        summary_lines.append(line)
        total += item.tattoo.price

    for addon_id in selected_addons:
        addon = addons_dict.get(addon_id)
        if addon:
            summary_lines.append(f"Доп: {addon.title} — {addon.price} ₽")
            total += addon.price

    if not cart_items and not summary_lines:
        messages.error(request, 'Корзина пуста')
        return redirect('cart')

    request.session['cart_checkout'] = {
        'items': summary_lines,
        'total': float(total),
        'addon_ids': selected_addons,
        'tattoo_ids': [c.tattoo_id for c in cart_items],
    }
    return redirect(f"{reverse('create_appointment')}?from_cart=1")


# ==================== Записи на сеансы ====================

@login_required
def appointments(request):
    """Список записей на сеансы"""
    if request.user.is_master():
        # Мастер видит свои записи
        appointments_list = Appointment.objects.filter(master=request.user)
    elif request.user.is_admin():
        # Администратор видит все записи
        appointments_list = Appointment.objects.all()
    else:
        # Пользователь видит свои записи
        appointments_list = Appointment.objects.filter(client=request.user)
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        appointments_list = appointments_list.filter(status=status_filter)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-date')
    if sort_by == 'date_asc':
        appointments_list = appointments_list.order_by('date', 'time')
    else:
        appointments_list = appointments_list.order_by('-date', '-time')
    
    paginator = Paginator(appointments_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_status': status_filter,
        'current_sort': sort_by,
    }
    return render(request, 'salon/appointments.html', context)


@login_required
def get_available_times(request):
    """API endpoint для получения доступного времени"""
    from django.http import JsonResponse
    from datetime import datetime, time as dt_time
    
    master_id = request.GET.get('master_id')
    date_str = request.GET.get('date')
    
    if not master_id or not date_str:
        return JsonResponse({'error': 'Не указаны мастер или дата'}, status=400)
    
    try:
        master = User.objects.get(pk=master_id, role='master')
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (User.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Неверные данные'}, status=400)
    
    # Рабочие часы: 10:00 - 20:00, интервал 30 минут
    start_time = dt_time(10, 0)
    end_time = dt_time(20, 0)
    interval_minutes = 30
    
    # Генерируем все возможные временные слоты
    available_times = []
    current_time = start_time
    
    while current_time < end_time:
        available_times.append(current_time.strftime('%H:%M'))
        # Добавляем 30 минут
        hour = current_time.hour
        minute = current_time.minute + interval_minutes
        if minute >= 60:
            hour += 1
            minute -= 60
        current_time = dt_time(hour, minute)
    
    # Получаем занятые временные слоты для этого мастера и даты
    # Исключаем отмененные записи
    booked_appointments = Appointment.objects.filter(
        master=master,
        date=appointment_date,
        status__in=['pending', 'confirmed', 'completed']
    ).values_list('time', flat=True)
    
    booked_times = [t.strftime('%H:%M') for t in booked_appointments]
    
    # Фильтруем доступное время
    free_times = [t for t in available_times if t not in booked_times]
    
    return JsonResponse({
        'available_times': free_times,
        'booked_times': booked_times
    })


@login_required
def create_appointment(request):
    """Создание записи на сеанс"""
    cart_checkout = request.session.get('cart_checkout')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Проверяем, не занято ли время
            master = form.cleaned_data['master']
            date = form.cleaned_data['date']
            time = form.cleaned_data['time']
            
            # Проверяем конфликты (исключая текущую запись при редактировании)
            conflicting = Appointment.objects.filter(
                master=master,
                date=date,
                time=time,
                status__in=['pending', 'confirmed']
            )
            
            if form.instance.pk:
                conflicting = conflicting.exclude(pk=form.instance.pk)
            
            if conflicting.exists():
                form.add_error('time', 'Это время уже занято. Выберите другое время.')
            else:
                appointment = form.save(commit=False)
                appointment.client = request.user
                # если оформляем из корзины, не привязываем к конкретной татуировке
                if cart_checkout:
                    appointment.tattoo = None
                    appointment.items_summary = "\n".join(cart_checkout.get('items', []))
                    appointment.total_price = cart_checkout.get('total', 0)
                else:
                    # по умолчанию считаем сумму по татуировке
                    if appointment.tattoo:
                        appointment.items_summary = f"Татуировка: {appointment.tattoo.title} — {appointment.tattoo.price} ₽"
                        appointment.total_price = appointment.tattoo.price
                appointment.save()
                # если заказ из корзины — очищаем корзину
                if cart_checkout:
                    CartItem.objects.filter(user=request.user).delete()
                    _care_addons_save(request, set())  # очищаем выбранные допы
                    request.session.pop('cart_checkout', None)
                messages.success(request, 'Запись успешно создана!')
                return redirect('appointments')
    else:
        form = AppointmentForm()
    
    return render(request, 'salon/create_appointment.html', {'form': form})


@login_required
def appointment_detail(request, pk):
    """Детальная страница записи"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Проверка доступа
    if not (request.user.is_admin() or 
            appointment.client == request.user or 
            appointment.master == request.user):
        messages.error(request, 'У вас нет доступа к этой записи')
        return redirect('appointments')
    
    return render(request, 'salon/appointment_detail.html', {'appointment': appointment})


# ==================== Доп. товары (уход) ====================

@login_required
def care_products(request):
    """Страница с доп. товарами ухода"""
    selected = _care_addons_selected(request)
    products = CareProduct.objects.filter(is_active=True)
    return render(request, 'salon/care_products.html', {
        'care_products': products,
        'selected_addons': selected
    })


@login_required
def add_care_addon(request, product_id):
    product = get_object_or_404(CareProduct, pk=product_id, is_active=True)
    selected = _care_addons_selected(request)
    selected.add(str(product.id))
    _care_addons_save(request, selected)
    messages.success(request, f'{product.title} добавлен в заказ. Будет выдан на сеансе.')
    return redirect(request.META.get('HTTP_REFERER', reverse('care_products')))


@login_required
def remove_care_addon(request, product_id):
    selected = _care_addons_selected(request)
    pid = str(product_id)
    if pid in selected:
        selected.remove(pid)
        _care_addons_save(request, selected)
        messages.info(request, 'Товар убран из заказа.')
    return redirect(request.META.get('HTTP_REFERER', reverse('care_products')))


@login_required
def cart_attach_to_active_appointment(request):
    """Добавить выбранные средства ухода к ближайшей активной записи"""
    selected_addons = list(_care_addons_selected(request))
    if not selected_addons:
        messages.error(request, 'Нет выбранных средств ухода.')
        return redirect('cart')

    products = CareProduct.objects.filter(is_active=True)
    addons_dict = {str(p.id): p for p in products}
    addons = [addons_dict[i] for i in selected_addons if i in addons_dict]
    if not addons:
        messages.error(request, 'Выбранные средства недоступны.')
        return redirect('cart')

    appt = Appointment.objects.filter(
        client=request.user,
        status__in=['pending', 'confirmed']
    ).order_by('date', 'time').first()

    if not appt:
        messages.error(request, 'Нет активных записей. Создайте новую запись.')
        return redirect('cart')

    lines = [f"Доп: {a.title} — {a.price} ₽" for a in addons]
    append_text = "\n".join(lines)
    if appt.items_summary:
        appt.items_summary = f"{appt.items_summary}\n{append_text}"
    else:
        appt.items_summary = append_text
    appt.total_price = (appt.total_price or 0) + sum(a.price for a in addons)
    appt.save()

    _care_addons_save(request, set())
    messages.success(request, f"Товары ухода добавлены к записи #{appt.pk}. Их выдадут на сеансе.")
    return redirect('cart')


# ==================== Админ: Товары ухода ====================

@login_required
@user_passes_test(is_admin)
def admin_care_products(request):
    products = CareProduct.objects.all()
    search = request.GET.get('search')
    active = request.GET.get('active')
    if search:
        products = products.filter(title__icontains=search)
    if active == 'true':
        products = products.filter(is_active=True)
    elif active == 'false':
        products = products.filter(is_active=False)

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'salon/admin/care_products.html', {
        'page_obj': page_obj,
        'search_query': search,
        'current_active': active,
    })


@login_required
@user_passes_test(is_admin)
def admin_care_product_create(request):
    if request.method == 'POST':
        form = CareProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар ухода создан')
            return redirect('admin_care_products')
    else:
        form = CareProductForm()
    return render(request, 'salon/admin/care_product_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_care_product_edit(request, pk):
    product = get_object_or_404(CareProduct, pk=pk)
    if request.method == 'POST':
        form = CareProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар ухода обновлён')
            return redirect('admin_care_products')
    else:
        form = CareProductForm(instance=product)
    return render(request, 'salon/admin/care_product_form.html', {'form': form, 'product': product})


@login_required
@user_passes_test(is_admin)
def admin_care_product_delete(request, pk):
    product = get_object_or_404(CareProduct, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар ухода удалён')
        return redirect('admin_care_products')
    return render(request, 'salon/admin/care_product_confirm_delete.html', {'product': product})


# ==================== Администратор ====================

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Управление пользователями (администратор)"""
    users = User.objects.all()
    
    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Фильтрация по роли
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_role': role_filter,
        'search_query': search_query,
    }
    return render(request, 'salon/admin/users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_create(request):
    """Создание пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пользователь успешно создан')
            return redirect('admin_users')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'salon/admin/user_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_user_edit(request, pk):
    """Редактирование пользователя"""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пользователь успешно обновлен')
            return redirect('admin_users')
    else:
        form = UserForm(instance=user)
    
    return render(request, 'salon/admin/user_form.html', {'form': form, 'user': user})


@login_required
@user_passes_test(is_admin)
def admin_user_delete(request, pk):
    """Удаление пользователя"""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Пользователь удален')
        return redirect('admin_users')
    return render(request, 'salon/admin/user_confirm_delete.html', {'user': user})


@login_required
@user_passes_test(is_admin)
def admin_reviews(request):
    """Управление отзывами (администратор)"""
    reviews_list = Review.objects.all()
    
    # Фильтрация по статусу модерации
    moderation_filter = request.GET.get('moderation')
    if moderation_filter == 'pending':
        reviews_list = reviews_list.filter(is_moderated=False)
    elif moderation_filter == 'moderated':
        reviews_list = reviews_list.filter(is_moderated=True)
    
    paginator = Paginator(reviews_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_moderation': moderation_filter,
    }
    return render(request, 'salon/admin/reviews.html', context)


@login_required
@user_passes_test(is_admin)
def admin_review_moderate(request, pk, action):
    """Модерация отзыва"""
    review = get_object_or_404(Review, pk=pk)
    if action == 'approve':
        review.is_moderated = True
        review.save()
        messages.success(request, 'Отзыв одобрен')
    elif action == 'delete':
        review.delete()
        messages.success(request, 'Отзыв удален')
    return redirect('admin_reviews')


@login_required
@user_passes_test(is_admin)
def admin_tattoos(request):
    """Управление татуировками (администратор)"""
    tattoos = Tattoo.objects.all()
    
    # Фильтрация
    style_filter = request.GET.get('style')
    if style_filter:
        tattoos = tattoos.filter(style_id=style_filter)
    
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        tattoos = tattoos.filter(is_active=True)
    elif active_filter == 'false':
        tattoos = tattoos.filter(is_active=False)
    
    paginator = Paginator(tattoos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    styles = TattooStyle.objects.all()
    
    context = {
        'page_obj': page_obj,
        'styles': styles,
        'current_style': style_filter,
        'current_active': active_filter,
    }
    return render(request, 'salon/admin/tattoos.html', context)


@login_required
@user_passes_test(is_admin)
def admin_tattoo_create(request):
    """Создание татуировки"""
    if request.method == 'POST':
        form = TattooForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Татуировка успешно создана')
            return redirect('admin_tattoos')
    else:
        form = TattooForm()
    
    return render(request, 'salon/admin/tattoo_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_tattoo_edit(request, pk):
    """Редактирование татуировки"""
    tattoo = get_object_or_404(Tattoo, pk=pk)
    if request.method == 'POST':
        form = TattooForm(request.POST, request.FILES, instance=tattoo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Татуировка успешно обновлена')
            return redirect('admin_tattoos')
    else:
        form = TattooForm(instance=tattoo)
    
    return render(request, 'salon/admin/tattoo_form.html', {'form': form, 'tattoo': tattoo})


@login_required
@user_passes_test(is_admin)
def admin_tattoo_delete(request, pk):
    """Удаление татуировки"""
    tattoo = get_object_or_404(Tattoo, pk=pk)
    if request.method == 'POST':
        tattoo.delete()
        messages.success(request, 'Татуировка удалена')
        return redirect('admin_tattoos')
    return render(request, 'salon/admin/tattoo_confirm_delete.html', {'tattoo': tattoo})


@login_required
@user_passes_test(is_admin)
def admin_appointments(request):
    """Управление записями (администратор)"""
    appointments_list = Appointment.objects.all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        appointments_list = appointments_list.filter(status=status_filter)
    
    paginator = Paginator(appointments_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_status': status_filter,
    }
    return render(request, 'salon/admin/appointments.html', context)


@login_required
@user_passes_test(is_admin)
def admin_appointment_edit(request, pk):
    """Редактирование записи"""
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        form = AppointmentAdminForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись успешно обновлена')
            return redirect('admin_appointments')
    else:
        form = AppointmentAdminForm(instance=appointment)
    
    return render(request, 'salon/admin/appointment_form.html', {'form': form, 'appointment': appointment})


@login_required
@user_passes_test(is_admin)
def admin_appointment_delete(request, pk):
    """Удаление записи"""
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Запись удалена')
        return redirect('admin_appointments')
    return render(request, 'salon/admin/appointment_confirm_delete.html', {'appointment': appointment})


# ==================== Тату-мастер ====================

@login_required
@user_passes_test(is_master)
def master_tattoos(request):
    """Управление татуировками (мастер)"""
    tattoos = Tattoo.objects.filter(master=request.user)
    
    style_filter = request.GET.get('style')
    if style_filter:
        tattoos = tattoos.filter(style_id=style_filter)
    
    paginator = Paginator(tattoos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    styles = TattooStyle.objects.all()
    
    context = {
        'page_obj': page_obj,
        'styles': styles,
        'current_style': style_filter,
    }
    return render(request, 'salon/master/tattoos.html', context)


@login_required
@user_passes_test(is_master)
def master_tattoo_create(request):
    """Создание татуировки (мастер)"""
    if request.method == 'POST':
        form = TattooForm(request.POST, request.FILES)
        if form.is_valid():
            tattoo = form.save(commit=False)
            tattoo.master = request.user
            tattoo.save()
            messages.success(request, 'Татуировка успешно создана')
            return redirect('master_tattoos')
    else:
        form = TattooForm(initial={'master': request.user})
        form.fields['master'].widget = forms.HiddenInput()
        form.fields['master'].queryset = User.objects.filter(pk=request.user.pk)
    
    return render(request, 'salon/master/tattoo_form.html', {'form': form})


@login_required
@user_passes_test(is_master)
def master_tattoo_edit(request, pk):
    """Редактирование татуировки (мастер)"""
    tattoo = get_object_or_404(Tattoo, pk=pk, master=request.user)
    if request.method == 'POST':
        form = TattooForm(request.POST, request.FILES, instance=tattoo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Татуировка успешно обновлена')
            return redirect('master_tattoos')
    else:
        form = TattooForm(instance=tattoo)
        form.fields['master'].widget = forms.HiddenInput()
        form.fields['master'].queryset = User.objects.filter(pk=request.user.pk)
    
    return render(request, 'salon/master/tattoo_form.html', {'form': form, 'tattoo': tattoo})


@login_required
@user_passes_test(is_master)
def master_tattoo_delete(request, pk):
    """Удаление татуировки (мастер)"""
    tattoo = get_object_or_404(Tattoo, pk=pk, master=request.user)
    if request.method == 'POST':
        tattoo.delete()
        messages.success(request, 'Татуировка удалена')
        return redirect('master_tattoos')
    return render(request, 'salon/master/tattoo_confirm_delete.html', {'tattoo': tattoo})


# ==================== Аутентификация ====================

def register(request):
    """Регистрация"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

