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

    data = data.get("data", [])

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


@st.cache_data(persist=True)
def get_item_detail(item):
    conn = http.client.HTTPSConnection("api.warframe.market")
    headers = {"platform": "pc", "crossplay": "true"}
    slug = item.get("slug", None)

    if slug is None:
        return {"min_price": None, "average_price": None}
    try:
        conn.request("GET", f"/v2/orders/item/{slug}", headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return {"min_price": None, "average_price": None}
        data = response.read().decode("utf-8")
        data = json.loads(data)
    except Exception:
        return {"min_price": None, "average_price": None}
    finally:
        try:
            conn.close()
        except Exception:
            pass

    data = data.get("data", [])

    sell_orders = [
        x.get("platinum")
        for x in data
        if x.get("type", None) == "sell" and x.get("rank") == item.get("max_rank")
        # FIX: only use max rank for arcanes
        # or extract data for unranked and maxed
    ]

    time.sleep(0.35)
    return {"min_price": min(sell_orders), "average_price": average(sell_orders)}


@st.cache_data(persist=True)
def load_data():
    items = get_items()
    if not items:
        return pd.DataFrame(), pd.DataFrame()

    count = 0
    total = len(items)
    items_with_price = []
    for x in items:
        details = get_item_detail(x)
        items_with_price.append(x | details)
        count += 1
        print(f"{count}/{total}")

    df = pd.DataFrame(items_with_price)

    arcanes_df = df[df["type"] == "arcane"].reset_index(drop=True)
    mods_df = df[df["type"] == "mod"].reset_index(drop=True)

    return arcanes_df, mods_df
