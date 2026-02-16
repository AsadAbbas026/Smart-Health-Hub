# save_subscription.py
import json
import streamlit as st
import os

def save_subscription(subscription):
    subs_file = "subscriptions.json"
    subs = []

    if os.path.exists(subs_file):
        with open(subs_file, "r") as f:
            subs = json.load(f)

    # Avoid duplicates
    if subscription not in subs:
        subs.append(subscription)

    with open(subs_file, "w") as f:
        json.dump(subs, f, indent=2)
