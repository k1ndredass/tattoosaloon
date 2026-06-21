from django.core.management.base import BaseCommand
from salon.models import User, TattooStyle, Tattoo, Appointment, Review
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Создает тестовые данные для тату-салона'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Создание стилей
        styles_data = [
            {'name': 'Реализм', 'description': 'Реалистичные татуировки'},
            {'name': 'Минимализм', 'description': 'Минималистичные дизайны'},
            {'name': 'Олдскул', 'description': 'Классический стиль'},
            {'name': 'Японский', 'description': 'Традиционные японские татуировки'},
            {'name': 'Геометрия', 'description': 'Геометрические узоры'},
        ]
        
        styles = []
        for style_data in styles_data:
            style, created = TattooStyle.objects.get_or_create(
                name=style_data['name'],
                defaults={'description': style_data['description']}
            )
            styles.append(style)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан стиль: {style.name}'))

        # Создание мастеров
        masters_data = [
            {'username': 'master1', 'first_name': 'Алексей', 'last_name': 'Петров', 'email': 'master1@example.com'},
            {'username': 'master2', 'first_name': 'Мария', 'last_name': 'Иванова', 'email': 'master2@example.com'},
            {'username': 'master3', 'first_name': 'Дмитрий', 'last_name': 'Сидоров', 'email': 'master3@example.com'},
        ]
        
        masters = []
        for master_data in masters_data:
            master, created = User.objects.get_or_create(
                username=master_data['username'],
                defaults={
                    'email': master_data['email'],
                    'role': 'master',
                    'first_name': master_data['first_name'],
                    'last_name': master_data['last_name'],
                }
            )
            if created:
                master.set_password('password123')
                master.save()
                self.stdout.write(self.style.SUCCESS(f'Создан мастер: {master.get_full_name()} ({master.username})'))
            masters.append(master)

        # Создание обычных пользователей
        users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={
                    'email': f'user{i}@example.com',
                    'role': 'user',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user.username}'))
            users.append(user)

        # Создание татуировок
        tattoo_data = [
            {
                'title': 'Роза на руке',
                'description': 'Классическая татуировка розы в реалистичном стиле. Идеально подходит для предплечья или плеча. Размер: средний.',
                'price': 5000
            },
            {
                'title': 'Дракон на спине',
                'description': 'Мощная татуировка дракона в японском стиле. Займет всю спину. Работа выполняется в несколько сеансов.',
                'price': 25000
            },
            {
                'title': 'Геометрический узор',
                'description': 'Современный геометрический дизайн. Минималистичный стиль, идеально подходит для запястья или лодыжки.',
                'price': 3500
            },
            {
                'title': 'Портрет',
                'description': 'Реалистичный портрет. Выполняется по фотографии. Требует высокого мастерства и несколько сеансов.',
                'price': 20000
            },
            {
                'title': 'Японский карп',
                'description': 'Традиционный японский карп кои. Символ удачи и силы. Выполняется в цвете.',
                'price': 8000
            },
            {
                'title': 'Минималистичный цветок',
                'description': 'Простой и элегантный цветок в минималистичном стиле. Идеально для первого тату.',
                'price': 3000
            },
            {
                'title': 'Олдскул якорь',
                'description': 'Классическая татуировка в стиле олдскул. Якорь - символ стабильности и надежды.',
                'price': 4500
            },
            {
                'title': 'Реалистичный волк',
                'description': 'Детализированная татуировка волка в реалистичном стиле. Выполняется на плече или бедре.',
                'price': 12000
            },
            {
                'title': 'Мандала',
                'description': 'Сакральный геометрический узор - мандала. Симметричный дизайн, идеально для спины или груди.',
                'price': 6000
            },
            {
                'title': 'Татуировка с надписью',
                'description': 'Элегантная надпись на выбранном языке. Различные шрифты и стили на выбор.',
                'price': 2500
            },
            {
                'title': 'Птица свободы',
                'description': 'Летящая птица как символ свободы. Может быть выполнена в разных стилях.',
                'price': 4000
            },
            {
                'title': 'Лев на груди',
                'description': 'Мощная татуировка льва на груди. Реалистичный стиль, требует несколько сеансов.',
                'price': 18000
            }
        ]
        
        tattoos = []
        for tattoo_info in tattoo_data:
            tattoo, created = Tattoo.objects.get_or_create(
                title=tattoo_info['title'],
                defaults={
                    'description': tattoo_info['description'],
                    'style': random.choice(styles),
                    'master': random.choice(masters),
                    'price': tattoo_info['price'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана татуировка: {tattoo.title} ({tattoo.price} ₽)'))
            tattoos.append(tattoo)

        # Создание записей
        for i in range(10):
            date = timezone.now().date() + timedelta(days=random.randint(1, 30))
            time = timezone.now().time().replace(
                hour=random.randint(10, 18),
                minute=random.choice([0, 30])
            )
            Appointment.objects.get_or_create(
                client=random.choice(users),
                master=random.choice(masters),
                date=date,
                time=time,
                defaults={
                    'tattoo': random.choice(tattoos) if random.choice([True, False]) else None,
                    'status': random.choice(['pending', 'confirmed', 'completed']),
                    'notes': f'Примечание к записи {i+1}',
                }
            )
        self.stdout.write(self.style.SUCCESS('Созданы записи на сеансы'))

        # Создание отзывов
        for i in range(15):
            Review.objects.get_or_create(
                author=random.choice(users),
                master=random.choice(masters),
                rating=random.randint(3, 5),
                defaults={
                    'tattoo': random.choice(tattoos) if random.choice([True, False]) else None,
                    'text': f'Отличная работа! Очень доволен результатом. Отзыв #{i+1}',
                    'is_moderated': random.choice([True, True, True, False]),  # Большинство промодерированы
                }
            )
        self.stdout.write(self.style.SUCCESS('Созданы отзывы'))

        self.stdout.write(self.style.SUCCESS('\nТестовые данные успешно созданы!'))
        self.stdout.write('\nДанные для входа:')
        self.stdout.write('Администратор: используйте созданного суперпользователя')
        self.stdout.write('Мастера: master1, master2, master3 (пароль: password123)')
        self.stdout.write('Пользователи: user1, user2, user3, user4, user5 (пароль: password123)')

