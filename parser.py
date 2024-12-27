
import requests
from sqlalchemy.orm import Session
from models import Category, Product

def get_categories(session: Session, parent_id=None):
    url = "https://api-ecomm.sdvor.com/occ/v2/sd/catalogs/sdvrProductCatalog/Online/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        categories_data = data.get('categories', [])
        for category_data in categories_data:
            category = Category(
                id=category_data['id'],
                name=category_data['name'],
                parent_id=parent_id
            )
            session.merge(category)
            session.commit()
            # Рекурсивно получить подкатегории
            if 'subcategories' in category_data:
                get_subcategories(session, category_data['subcategories'], category_data['id'])
    else:
        print(f"Ошибка получения категорий: {response.status_code}")

def get_subcategories(session: Session, subcategories_data, parent_id):
    for category_data in subcategories_data:
        category = Category(
            id=category_data['id'],
            name=category_data['name'],
            parent_id=parent_id
        )
        session.merge(category)
        session.commit()
        if 'subcategories' in category_data:
            get_subcategories(session, category_data['subcategories'], category_data['id'])

def get_products(session: Session, category_id):
    url = f"https://api-ecomm.sdvor.com/occ/v2/sd/products/search?fields=algorithmsForAddingRelatedProducts%2CcategoryCode%2Cproducts(code%2Cbonus%2Cslug%2CdealType%2Cname%2Cunit%2Cunits(FULL)%2CunitPrices(FULL)%2CavailableInStores(FULL)%2Cbadges(DEFAULT)%2Cmultiunit%2Cprice(FULL)%2CcrossedPrice(FULL)%2CtransitPrice(FULL)%2CpersonalPrice(FULL)%2Cimages(DEFAULT)%2Cstock(FULL)%2CmarketingAttributes%2CisArchive%2Ccategories(FULL)%2CcategoryNamesForAnalytics)%2Cfacets%2Cbreadcrumbs%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2Cbanners(FULL)%2CfreeTextSearch%2CcurrentQuery%2CkeywordRedirectUrl&currentPage=0&pageSize=9999999&facets=allCategories%3A{category_id}&lang=ru&curr=RUB&deviceType=desktop&baseStore=ekb"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products_data = data.get('products', [])
        for product_data in products_data:
            price = product_data.get('price', {}).get('value', 0.0)
            product = Product(
                code=product_data['code'],
                name=product_data['name'],
                price=price,
                category_id=category_id
            )
            session.merge(product)
        session.commit()
    else:
        print(f"Ошибка получения продуктов для категории {category_id}: {response.status_code}")