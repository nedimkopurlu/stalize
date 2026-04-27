from app.services.bist_datastore_adapter import BistDatastoreAdapter


def test_translate_period_maps_known_values():
    adapter = BistDatastoreAdapter()

    assert adapter._translate_period("A") == "Aylık"
    assert adapter._translate_period("G") == "Günlük"
    assert adapter._translate_period("S") == "Seanslık"


def test_get_market_info_maps_parent_groups():
    adapter = BistDatastoreAdapter()

    label, key = adapter._get_market_info("PPB")
    assert label == "Pay Piyasası"
    assert key == "pay_piyasasi"


def test_dataset_row_shape_matches_datastore_payloads():
    adapter = BistDatastoreAdapter()
    product_type = {
        "id": "3157",
        "code": "HIST",
        "name": "Kapanış, En Düşük ve En Yüksek Fiyatlar ile İşlem Hacmi, İşlem Miktarı (Aylık)",
        "period": "A",
        "price": 0.0,
        "access_type": "G",
        "subscription_product": True,
        "data_parent_group": "PPB",
    }
    latest_product = {
        "id": 6584561,
        "file_name": "PP_AYLIKOZET.M.202603.zip",
        "date": "30-03-2026",
        "create_date": "01-04-2026",
        "file_size": 670768,
        "download_endpoint": "https://datastore.borsaistanbul.com/api/file/6584561",
    }

    market_label, market_key = adapter._get_market_info(product_type["data_parent_group"])
    result = {
        "title": product_type.get("name"),
        "market": market_label,
        "market_key": market_key,
        "dataset_code": product_type.get("code"),
        "product_type_id": product_type.get("id"),
        "subscription_product": product_type.get("subscription_product"),
        "price": product_type.get("price"),
        "access_type": product_type.get("access_type"),
        "update_frequency": adapter._translate_period(product_type.get("period")),
        "latest_file_name": latest_product.get("file_name"),
        "latest_file_date": latest_product.get("date"),
        "latest_create_date": latest_product.get("create_date"),
        "latest_file_size": latest_product.get("file_size"),
        "download_endpoint": latest_product.get("download_endpoint"),
        "catalog_url": f"{adapter.base_url}/api/product-type/{product_type.get('id')}/products?page=1&page-size=1",
        "datastore_url": adapter.base_url,
        "source": "Borsa İstanbul Veri Store",
    }

    assert result["market_key"] == "pay_piyasasi"
    assert result["update_frequency"] == "Aylık"
    assert result["latest_file_name"] == "PP_AYLIKOZET.M.202603.zip"
    assert result["download_endpoint"].endswith("/api/file/6584561")


def test_product_file_row_shape_matches_datastore_payloads():
    adapter = BistDatastoreAdapter()
    raw_item = {
        "id": 6584561,
        "fileName": "PP_AYLIKOZET.M.202603.zip",
        "date": "30-03-2026",
        "createDate": "01-04-2026",
        "fileSize": 670768,
        "price": 0.0,
        "discountPrice": 0.0,
        "inLibrary": False,
        "dataDefnEntity": {
            "period": "A",
            "market": "MSPOT",
            "accessType": "G",
            "sourceSystem": "BIST",
        },
    }

    result = {
        "id": raw_item.get("id"),
        "file_name": raw_item.get("fileName"),
        "date": raw_item.get("date"),
        "create_date": raw_item.get("createDate"),
        "file_size": raw_item.get("fileSize"),
        "price": raw_item.get("price"),
        "discount_price": raw_item.get("discountPrice"),
        "in_library": raw_item.get("inLibrary"),
        "period": raw_item.get("dataDefnEntity", {}).get("period"),
        "market": raw_item.get("dataDefnEntity", {}).get("market"),
        "access_type": raw_item.get("dataDefnEntity", {}).get("accessType"),
        "source_system": raw_item.get("dataDefnEntity", {}).get("sourceSystem"),
        "download_endpoint": f"{adapter.base_url}/api/file/{raw_item.get('id')}",
    }

    assert result["file_name"] == "PP_AYLIKOZET.M.202603.zip"
    assert result["market"] == "MSPOT"
    assert result["access_type"] == "G"
    assert result["download_endpoint"].endswith("/api/file/6584561")
