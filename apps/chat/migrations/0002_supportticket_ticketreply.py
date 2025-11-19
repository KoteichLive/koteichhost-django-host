from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255, verbose_name='Тема')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('priority', models.CharField(choices=[('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий')], default='medium', max_length=10, verbose_name='Приоритет')),
                ('status', models.CharField(choices=[('new', 'Новый'), ('in_progress', 'В процессе'), ('waiting', 'Ожидание ответа'), ('resolved', 'Решен'), ('closed', 'Закрыт')], default='new', max_length=20, verbose_name='Статус')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано администратором')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL, verbose_name='Назначено')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_tickets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Тикет техподдержки',
                'verbose_name_plural': 'Тикеты техподдержки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TicketReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Ответ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_replies', to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='chat.supportticket')),
            ],
            options={
                'verbose_name': 'Ответ в тикете',
                'verbose_name_plural': 'Ответы в тикетах',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='supportticket',
            index=models.Index(fields=['status', 'is_read'], name='chat_support_status_c8d3e2_idx'),
        ),
        migrations.AddIndex(
            model_name='supportticket',
            index=models.Index(fields=['user', 'status'], name='chat_support_user_id_a4f2b1_idx'),
        ),
    ]
