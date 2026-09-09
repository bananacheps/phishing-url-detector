from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from model_assets.feature_extractor import extract_features


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model_assets"
MODEL_PATH = MODEL_DIR / "model_xgboost_7fitur.pkl"
FEATURE_INFO_PATH = MODEL_DIR / "feature_info.json"

FEATURE_LABELS = {
    "url_length": "URL Length",
    "domain_length": "Domain Length",
    "subdomain_count": "Subdomain Count",
    "special_char_count": "Special Character Count",
    "digit_count": "Digit Count",
    "https_usage": "HTTPS Usage",
    "url_entropy": "URL Entropy",
}


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_feature_info() -> dict:
    with FEATURE_INFO_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def get_feature_names() -> list[str]:
    feature_info = load_feature_info()
    feature_names = feature_info.get("features")
    if not isinstance(feature_names, list) or len(feature_names) != 7:
        raise ValueError("Konfigurasi fitur harus berisi tepat 7 fitur.")
    if feature_names != list(FEATURE_LABELS):
        raise ValueError("Urutan fitur pada konfigurasi tidak sesuai dengan aplikasi.")
    return feature_names


def make_feature_table(feature_names: list[str], feature_values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Fitur": [FEATURE_LABELS[name] for name in feature_names],
            "Nilai": feature_values,
        }
    )


def predict_url(url: str, feature_names: list[str]) -> tuple[int, float, float, pd.DataFrame]:
    feature_values = extract_features(url)
    if len(feature_values) != 7:
        raise ValueError("Extractor harus menghasilkan tepat 7 fitur.")

    features = pd.DataFrame([feature_values], columns=feature_names)
    model = load_model()
    probabilities = model.predict_proba(features)[0]
    classes = list(model.classes_)

    if 0 not in classes or 1 not in classes:
        raise ValueError("Model harus memiliki kelas 0 (Legitimate) dan 1 (Phishing).")

    legitimate_probability = float(probabilities[classes.index(0)])
    phishing_probability = float(probabilities[classes.index(1)])
    prediction = int(model.predict(features)[0])

    return (
        prediction,
        phishing_probability,
        legitimate_probability,
        make_feature_table(feature_names, feature_values),
    )


def render_result(
    prediction: int,
    phishing_probability: float,
    legitimate_probability: float,
    feature_table: pd.DataFrame,
) -> None:
    st.subheader("Hasil Analisis")

    if prediction == 1:
        st.error("Terindikasi Phishing")
    else:
        st.success("Terindikasi Legitimate")

    probability_columns = st.columns(2)
    with probability_columns[0]:
        st.metric("Probabilitas Phishing", f"{phishing_probability:.2%}")
    with probability_columns[1]:
        st.metric("Probabilitas Legitimate", f"{legitimate_probability:.2%}")

    st.subheader("Tujuh Fitur yang Digunakan")
    st.dataframe(
        feature_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fitur": st.column_config.TextColumn("Fitur"),
            "Nilai": st.column_config.NumberColumn("Nilai", format="%.6f"),
        },
    )


def main() -> None:
    st.set_page_config(
        page_title="Phishing URL Detector",
        layout="centered",
    )

    st.title("Phishing URL Detector")
    st.write(
        "Prototype penelitian untuk menganalisis karakteristik URL menggunakan "
        "model Machine Learning XGBoost."
    )

    st.info(
        "Masukkan URL lengkap, termasuk `http://` atau `https://`, agar karakteristik "
        "URL dapat dianalisis sesuai dengan extractor penelitian."
    )

    try:
        feature_names = get_feature_names()
        feature_info = load_feature_info()
        model = load_model()
    except Exception as error:
        st.error(f"Komponen model tidak dapat dimuat: {error}")
        st.stop()

    with st.form("url_analysis_form"):
        url = st.text_input(
            "URL yang akan dianalisis",
            placeholder="https://contoh.com/login",
            help="Sistem menganalisis teks URL yang dimasukkan tanpa mengakses website tersebut.",
        )
        submitted = st.form_submit_button("Analisis URL", type="primary")

    if submitted:
        if not url.strip():
            st.warning("Masukkan URL terlebih dahulu.")
        else:
            with st.spinner("Menganalisis karakteristik URL..."):
                try:
                    prediction, phishing_probability, legitimate_probability, feature_table = (
                        predict_url(url, feature_names)
                    )
                    render_result(
                        prediction,
                        phishing_probability,
                        legitimate_probability,
                        feature_table,
                    )
                except Exception as error:
                    st.error(f"Analisis tidak dapat dilakukan: {error}")

    with st.expander("Informasi Model"):
        st.write(f"Model: {feature_info.get('model', 'Tidak tersedia')}")
        st.write(f"Jumlah fitur: {feature_info.get('number_of_features', len(feature_names))}")
        st.write("Extractor dan urutan fitur mengikuti file penelitian yang diunggah.")

    st.warning(
        "Peringatan: sistem ini hanya menganalisis karakteristik URL. Hasil prediksi "
        "bukan jaminan mutlak bahwa sebuah website aman atau berbahaya. Jangan "
        "membuka URL mencurigakan hanya berdasarkan hasil aplikasi ini."
    )


if __name__ == "__main__":
    main()