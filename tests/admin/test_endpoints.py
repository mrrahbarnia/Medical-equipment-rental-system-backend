import pytest

from fastapi import status
from async_asgi_testclient import TestClient # type: ignore

from tests.auth.test_endpoints import test_admin_login_successfully

pytestmark = pytest.mark.asyncio


async def test_create_category_successfully(client: TestClient):
    payload = {
        "name": "Category1"
    }
    second_payload = {
        "name": "string"
    }
    third_payload = {
        "name": "third example"
    }
    access_token = await test_admin_login_successfully(client=client)
    response = await client.post(
        "/admin/create-categories/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )
    await client.post(
        "/admin/create-categories/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=second_payload
    )
    await client.post(
        "/admin/create-categories/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=third_payload
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        'name': 'Category1', 'parentCategoryName': None, 'slug': 'category1'
    }


async def test_create_category_with_parent_name_which_not_exist(client: TestClient):
    payload = {
        "name": "Category1",
        "parentCategoryName": "Wrong parent name"
    }
    access_token = await test_admin_login_successfully(client=client)
    response = await client.post(
        "/admin/create-categories/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )

    assert response.json() == {'detail': 'There is no category with the provided parent category name!'}


async def test_search_categories(client: TestClient):
    response = await client.get("/admin/search-categories/?category_name=s")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == ['string']


async def test_get_all_categories_successfully(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    response = await client.get(
        "/admin/all-categories/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.json() == {
        'count': 3,
        'items': [
            {'name': 'Category1', 'slug': 'category1', 'parentName': None},
            {'name': 'string', 'slug': 'string', 'parentName': None},
            {'name': 'third example', 'slug': 'third-example', 'parentName': None}
        ]
    }
    assert response.status_code == status.HTTP_200_OK


async def test_delete_category_with_invalid_category_slug(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    response = await client.delete(
        "/admin/delete-category/wrongSlug/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.json() == {"detail": "There is no category with the provided info!"}
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_category_with_valid_category_slug_successfully(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    response = await client.delete(
        "/admin/delete-category/category1/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_get_category_by_slug_with_invalid_slug(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    response = await client.get(
        "/admin/get-category/wrongCategory/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "There is no category with the provided info!"}


async def test_get_category_by_slug_with_valid_slug(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    response = await client.get(
        "/admin/get-category/string/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'name': 'string', 'parentCategoryName': None, 'slug': 'string'
    }


async def test_update_category_with_invalid_category_slug(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    payload = {
        "name": "category1"
    }
    response = await client.put(
        "/admin/update-category/wrongSlug/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "There is no category with the provided info!"}


async def test_update_category_with_invalid_parent_category_name(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    payload = {
        "name": "category1",
        "parentCategoryName": "wrongParentCategoryName"
    }
    response = await client.put(
        "/admin/update-category/category1/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "There is no category with the provided parent category name!"
    }


async def test_update_category_with_valid_data_successfully(client: TestClient):
    access_token = await test_admin_login_successfully(client=client)
    payload = {
        "name": "edited string",
        "parentCategoryName": "third example"
    }
    response = await client.put(
        "/admin/update-category/string/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
