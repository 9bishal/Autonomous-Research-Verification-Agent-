"""
graph/config.py
================
Centralised configuration — reads from os.environ first,
then falls back to streamlit secrets for Streamlit Cloud.
"""

import os

def get_secret(key: str, default: str | None = None) -> str | None:
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default
