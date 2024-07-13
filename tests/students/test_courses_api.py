from unittest.mock import Mock

import pytest
from model_bakery import baker
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
def settings_with_max_students(settings):
    """
    Фикстура для MAX_STUDENTS_PER_COURSE
    """
    settings.MAX_STUDENTS_PER_COURSE = 20
    return settings


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


@pytest.mark.parametrize(
    'students_count, response_status',
    [(25, 400), (15, 201), (20, 201)]
)
@pytest.mark.django_db
def test_max_students(settings_with_max_students, client, course_factory,
                      student_factory, students_count, response_status):
    """
    Тест на добавление конкретного количества студентов
    """
    students = student_factory(
        _quantity=students_count
    )
    response = client.post(
        '/api/v1/courses/',
        data={
            'name': 'Test course',
            'students': [i.id for i in students]
        })
    assert response.status_code == response_status
