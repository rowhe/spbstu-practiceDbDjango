from django.db import models
from datetime import date, datetime
import hashlib
import os
from django.core.validators import RegexValidator
from PIL import Image

"""
Рассматриваются 4 таблицы условно обобщающие функционал блога
"""


class Blog(models.Model):
    """
    Таблица Блог, содержащая в себе
    name - название блога
    tagline - используется для хранения краткого описания или слогана блога
    """
    name = models.CharField(max_length=100,
                            unique=True,
                            verbose_name="Название блога",
                            help_text="Название блога уникальное. Ограничение 100 знаков")

    slug_name = models.SlugField(unique=True,
                                 verbose_name="Slug поле названия",
                                 help_text="Название написанное транслитом, для человекочитаемости. Название уникальное.")

    headline = models.TextField(max_length=255,
                                verbose_name="Короткий слоган",
                                null=True, blank=True,
                                help_text="Ограничение 255 символов.")

    description = models.TextField(null=True, blank=True,
                                   verbose_name="Описание блога",
                                   help_text="О чем этот блог? Для кого он, в чем его ценность?")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Блог"
        verbose_name_plural = "Блоги"
        unique_together = (
            'name', 'slug_name'
        )  # Условие на то, что поля 'name' и 'slug_name' должны создавать уникальную группу


class Author(models.Model):
    """
    Таблица Автор, содержащая в себе
    name - username автора
    email - адрес электронной почты автора
    """

    name = models.CharField(max_length=200, verbose_name="Имя")
    email = models.EmailField(unique=True, verbose_name="Почта")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"


def hashed_upload_path(instance, filename):
    """
    Пример замены имени файла на строку <user_hash> для возможного дальнейшего
    использования данных
    """
    # Генерация хэш значения картинки
    file_hash = hashlib.md5(instance.avatar.read()).hexdigest()

    # Получение файлового расширения
    _, ext = os.path.splitext(filename)

    # Новое имя картинки
    new_filename = f"{instance.author.name}_{file_hash}{ext}"

    # Возвращаем полный путь сохранения
    return os.path.join("avatars", new_filename)


class AuthorProfile(models.Model):
    """
    Дополнительная информация к профилю, было создано, чтобы показать, как можно
    расширить какую-то модель за счёт использования отношения
    один к одному(OneToOneField).
    author - связь с таблицей автор (один к одному(у автора может быть только один профиль,
    соответственно профиль принадлежит определенному автору))
    bio - текст о себе
    avatar - картинка профиля. Стоят задачи(просто, чтобы показать как это можно решить):
        1. При сохранении необходимо переименовать картинку по шаблону user_hash
        2. Необходимо все передаваемые картинки для аватара приводить к размеру 200х200
    phone_number - номер телефона с валидацией при внесении
    """
    author = models.OneToOneField(Author, on_delete=models.CASCADE)
    bio = models.TextField(blank=True,
                           null=True,
                           help_text="Короткая биография",
                           )
    avatar = models.ImageField(upload_to=hashed_upload_path,
                               default='avatars/unnamed.png',
                               null=True,
                               blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+79\d{9}$',
        message="Phone number must be entered in the format: '+79123456789'."
    )
    phone_number = models.CharField(validators=[phone_regex],
                                    max_length=12,
                                    blank=True,
                                    null=True,
                                    unique=True,
                                    help_text="Формат +79123456789",
                                    )  # максимальная длина 12 символов
    city = models.CharField(max_length=120,
                            blank=True,
                            null=True,
                            help_text="Город проживания",
                            )

    def __str__(self):
        return self.author.name

    def save(self, *args, **kwargs):
        # Вызов родительского save() метода
        super().save(*args, **kwargs)

        # Открытие картинки
        image = Image.open(self.avatar.path)

        # Определение желаемого размера картинки
        desired_size = (200, 200)

        # Изменение размера
        image.thumbnail(desired_size, Image.ANTIALIAS)

        # Сохранение картинки с перезаписью
        image.save(self.avatar.path)


class Entry(models.Model):
    """
    Статья блога
    blog - связь с конкретным блогом (отношением "один ко многим" (one-to-many).
        Одна запись блога (Entry) может быть связана с одним конкретным блогом (Blog),
        но блог (Blog) может иметь множество связанных записей блога (Entry))
    headline - заголовок
    slug_headline - заголовок в транслите
    summary - краткое описание статьи
    body_text - полный текст статьи
    pub_date - дата и время публикации записи
    mod_date - дата редактирования записи
    authors - авторы написавшие данную статью (отношение "многие ко многим"
        (many-to-many). Один автор может сделать несколько записей в блог (Entry),
         и одну запись могут сделать несколько авторов (Author))
    number_of_comments - число комментариев к статье
    number_of_pingbacks -  число отзывов/комментариев на других блогах или сайтах,
        связанных с определенной записью блога (Entry)
    rating - оценка статьи
    """
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="entryes")  # related_name позволяет создать обратную связь
    headline = models.CharField(max_length=255)
    slug_headline = models.SlugField(primary_key=True, max_length=255)
    summary = models.TextField()
    body_text = models.TextField()
    pub_date = models.DateTimeField(default=datetime.now)
    mod_date = models.DateField(auto_now=True)
    authors = models.ManyToManyField(Author)
    number_of_comments = models.IntegerField(default=0)
    number_of_pingbacks = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.headline

    class Meta:
        unique_together = ('blog', 'headline', 'slug_headline')
