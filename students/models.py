from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Student(models.Model):
    name = models.TextField(
    )
    birth_date = models.DateField(
        null=True,
    )


class Course(models.Model):
    name = models.TextField(
    )
    students = models.ManyToManyField(
        Student,
        blank=True,
    )

    def clean(self):
        """
        Используется для проверки количества студентов в курсе
        """
        max_students = settings.MAX_STUDENTS_PER_COURSE
        if self.students.count() > max_students:
            raise ValidationError(
                message=f"Maximum number of students per course - {max_students}",
                code='bad_request',
            )
