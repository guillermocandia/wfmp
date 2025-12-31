import http.client
import json
import time

import pandas as pd
import streamlit as st
from numpy import average


@st.cache_data(persist=True)
def get_items():
    conn = http.client.HTTPSConnection("api.warframe.market")
    headers = {"platform": "pc", "crossplay": "true"}

    try:
        conn.request("GET", "/v2/items", headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return None
        data = response.read().decode("utf-8")
        data = json.loads(data)
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return data.get("data", None)


@st.cache_data(persist=True)
def get_item_detail(item):
    conn = http.client.HTTPSConnection("api.warframe.market")
    headers = {"platform": "pc", "crossplay": "true"}
    slug = item.get("slug", None)

    if slug is None:
        return None

    try:
        conn.request("GET", f"/v2/orders/item/{slug}", headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return None
        data = response.read().decode("utf-8")
        data = json.loads(data)
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

    time.sleep(0.35)

    return data.get("data", None)


def process_items(data):
    filtered_items = [
        x
        for x in data
        if "arcane_enhancement" in x.get("tags", []) or "mod" in x.get("tags", [])
    ]

    def parse_rarity(tags):
        if "common" in tags:
            return "common"
        if "uncommon" in tags:
            return "uncommon"
        if "rare" in tags:
            return "rare"
        if "legendary" in tags:
            return "legendary"
        return None

    def parse_item(item):
        return {
            # "id": item.get("id"),
            "slug": item.get("slug"),
            "name": item.get("i18n", {}).get("en", {}).get("name"),
            # "icon": item.get("i18n", {}).get("en", {}).get("icon"),
            "max_rank": item.get("maxRank"),
            "type": "arcane" if "arcane_enhancement" in item.get("tags", []) else "mod",
            "rarity": parse_rarity(item.get("tags", [])),
        }

    items = [parse_item(x) for x in filtered_items]

    return items


def process_items_detail(data, item):
    if data is None:
        return {
            "min_price_rank_0": None,
            "min_price_max_rank": None,
            "average_price_rank_0": None,
            "average_price_max_rank": None,
        }
    sell_orders = [x for x in data if x.get("type", None) == "sell"]

    sell_orders_rank_0 = [x.get("platinum") for x in sell_orders if x.get("rank") == 0]

    sell_orders_max_rank = [
        x.get("platinum") for x in sell_orders if x.get("rank") == item.get("max_rank")
    ]

    return {
        "min_price_rank_0": (
            min(sell_orders_rank_0) if len(sell_orders_rank_0) > 0 else None
        ),
        "min_price_max_rank": (
            min(sell_orders_max_rank) if len(sell_orders_max_rank) > 0 else None
        ),
        "average_price_rank_0": (
            average(sell_orders_rank_0) if len(sell_orders_rank_0) > 0 else None
        ),
        "average_price_max_rank": (
            average(sell_orders_max_rank) if len(sell_orders_max_rank) > 0 else None
        ),
    }


def load_data():
    raw_items = get_items()
    if not raw_items:
        return pd.DataFrame(), pd.DataFrame()

    items = process_items(raw_items)

    count = 0
    total = len(items)
    items_with_details = []
    for item in items:
        raw_items_details = get_item_detail(item)
        item_details = process_items_detail(raw_items_details, item)
        items_with_details.append(item | item_details)
        count += 1
        print(f"{count}/{total}")

    df = pd.DataFrame(items_with_details)

    arcanes_df = df[df["type"] == "arcane"].reset_index(drop=True)
    mods_df = df[df["type"] == "mod"].reset_index(drop=True)

    return arcanes_df, mods_df
