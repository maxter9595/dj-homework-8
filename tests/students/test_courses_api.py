from unittest.mock import MagicMock

import pytest
from model_bakery import baker
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from students.models import Course, Student


@pytest.fixture
def api_client():
    """
    Фикстура для api-client
    """
    return APIClient()


@pytest.fixture
def course_factory():
    """
    Фикстура для фабрики курсов
    """
    def create_course(*args, **kwargs):
        return baker.make(
            Course,
            *args,
            **kwargs
        )
    return create_course


@pytest.fixture
def student_factory():
    """
    Фикстура для фабрики студентов
    """
    def create_student(*args, **kwargs):
        return baker.make(
            Student,
            *args,
            **kwargs
        )
    return create_student


@pytest.fixture
def max_students_settings(settings):
    """
    Фикстура для MAX_STUDENTS_PER_COURSE
    """
    return settings.MAX_STUDENTS_PER_COURSE


@pytest.mark.django_db
def test_get_first_course(api_client, course_factory):
    """
    Проверка получения первого курса (retrieve-логика)
    """
    course = course_factory(
        name='Test course',
    )
    response = api_client.get(
        '/api/v1/courses/'
    )
    data = response.json(
    )
    assert response.status_code == 200
    assert data[0].get('name') == course.name


@pytest.mark.django_db
def test_get_course_list(api_client, course_factory):
    """
    Проверка получения списка курсов (list-логика)
    """
    courses = course_factory(
        _quantity=2,
    )
    response = api_client.get(
        '/api/v1/courses/'
    )
    data = response.json(
    )
    assert response.status_code == 200
    for idx, course_data in enumerate(data):
        assert course_data.get('name') == courses[idx].name


@pytest.mark.django_db
def test_filter_course_list_by_id(api_client, course_factory):
    """
    Проверка фильтрации списка курсов по id
    """
    courses = course_factory(
        _quantity=3
    )
    for course in courses:
        response = api_client.get(
            f'/api/v1/courses/?id={course.id}'
        )
        data = response.json(
        )
        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['id'] == course.id


@pytest.mark.django_db
def test_filter_course_list_by_name(api_client, course_factory):
    """
    Проверка фильтрации списка курсов по name
    """
    courses = course_factory(
        _quantity=3
    )
    for course in courses:
        response = api_client.get(
            f'/api/v1/courses/?name={course.name}'
        )
        data = response.json(
        )
        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['name'] == course.name


@pytest.mark.django_db
def test_create_course(api_client):
    """
    Тест успешного создания курса
    """
    count = Course.objects.count()
    data = {
        'name': 'Test course',
    }
    response = api_client.post(
        '/api/v1/courses/',
        data,
    )
    assert response.status_code == 201
    assert Course.objects.count() == count + 1


@pytest.mark.django_db
def test_update_course(api_client, course_factory):
    """
    Тест успешного обновления курса
    """
    course = course_factory()
    data = {
        'name': 'Updated course name',
    }
    response = api_client.patch(
        f'/api/v1/courses/{course.id}/',
        data
    )
    assert response.status_code == 200
    course.refresh_from_db()
    assert course.name == data.get('name')


@pytest.mark.django_db
def test_delete_course(api_client, course_factory):
    """
    Тест успешного удаления курса
    """
    course = course_factory()
    response = api_client.delete(
        f'/api/v1/courses/{course.id}/'
    )
    assert response.status_code == 204
    assert not Course.objects.filter(
        id=course.id
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "students_count", [
        19,
        20,
        21
    ]
)
def test_max_students_per_course(student_factory,  course_factory,
                                 max_students_settings, students_count):
    """
    Тест на ограничение кол-ва студентов на курсе
    - Создаем макет (mock) для course.students.add через MagicMock
    - Добавляем студентов через созданный макет
    """
    course = course_factory()
    max_students = max_students_settings
    students = [
        student_factory() for _ in range(students_count)
    ]
    course_add_mock = MagicMock()
    course.students.add = course_add_mock
    course.students.add(
        *students
    )
    api_client = APIClient()
    response = api_client.get(
        '/api/v1/courses/'
    )
    try:
        assert course.students.count() == students_count
        assert response.status_code == 200
    except ValidationError as exc_info:
        error_message = exc_info.value.message_dict.get('__all__')[0]
        expected_error = f"Maximum number of students per course - {max_students}"
        assert error_message == expected_error
        assert response.status_code == 400
