from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

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

FEATURE_DESCRIPTIONS = {
    "url_length": "Jumlah seluruh karakter pada URL.",
    "domain_length": "Jumlah karakter pada bagian domain URL.",
    "subdomain_count": "Jumlah subdomain yang terdeteksi.",
    "special_char_count": "Jumlah karakter non-alfanumerik pada URL.",
    "digit_count": "Jumlah angka yang terdapat pada URL.",
    "https_usage": "1 jika URL menggunakan HTTPS, 0 jika tidak.",
    "url_entropy": "Ukuran keragaman karakter pada URL.",
}

FINAL_TEST_CASES = [
    {"url": "http://110.37.75.243:55976/i", "ground_truth": "Phishing"},
    {"url": "https://smartinsights.com", "ground_truth": "Legitimate"},
    {"url": "http://119.180.11.199:38087/i", "ground_truth": "Phishing"},
    {"url": "https://al.com", "ground_truth": "Legitimate"},
    {
        "url": "https://cipher.auth0rtoki1l.ru/oy3wo8fm",
        "ground_truth": "Phishing",
    },
    {"url": "https://sb-cd.com", "ground_truth": "Legitimate"},
    {"url": "http://195.178.110.250/a-r.m-6.Sakura", "ground_truth": "Phishing"},
    {"url": "https://kayatan.org", "ground_truth": "Legitimate"},
    {"url": "https://awmcdn.net", "ground_truth": "Legitimate"},
    {"url": "http://182.121.253.20:50869/i", "ground_truth": "Phishing"},
]


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
            "Penjelasan": [FEATURE_DESCRIPTIONS[name] for name in feature_names],
        }
    )


def validate_url(url: str) -> str | None:
    if not url.strip():
        return "Masukkan URL terlebih dahulu."

    if any(character.isspace() for character in url):
        return "URL tidak valid karena mengandung spasi."

    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return (
            "URL tidak valid. Gunakan format lengkap, misalnya "
            "https://www.robobricklab.com/"
        )

    return None


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


def run_final_test(feature_names: list[str]) -> pd.DataFrame:
    results = []
    for number, test_case in enumerate(FINAL_TEST_CASES, start=1):
        prediction, phishing_probability, legitimate_probability, _ = predict_url(
            test_case["url"],
            feature_names,
        )
        predicted_label = "Phishing" if prediction == 1 else "Legitimate"
        results.append(
            {
                "No": number,
                "URL": test_case["url"],
                "Ground Truth": test_case["ground_truth"],
                "Prediksi Model": predicted_label,
                "Prob. Phishing": f"{phishing_probability:.2%}",
                "Prob. Legitimate": f"{legitimate_probability:.2%}",
                "Status": (
                    "BENAR"
                    if predicted_label == test_case["ground_truth"]
                    else "SALAH"
                ),
            }
        )

    return pd.DataFrame(results)


def render_result(
    prediction: int,
    phishing_probability: float,
    legitimate_probability: float,
    feature_table: pd.DataFrame,
) -> None:
    st.subheader("Hasil Analisis")

    if prediction == 1:
        st.error("TERINDIKASI PHISHING")
    else:
        st.success("TERINDIKASI LEGITIMATE")

    probability_columns = st.columns(2)
    with probability_columns[0]:
        st.metric("Probabilitas Phishing", f"{phishing_probability:.2%}")
    with probability_columns[1]:
        st.metric("Probabilitas Legitimate", f"{legitimate_probability:.2%}")

    st.caption(
        f"Prediksi model: {'TERINDIKASI PHISHING' if prediction == 1 else 'TERINDIKASI LEGITIMATE'}"
    )

    st.subheader("Karakteristik URL yang Dianalisis")
    st.dataframe(
        feature_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fitur": st.column_config.TextColumn("Fitur"),
            "Nilai": st.column_config.NumberColumn("Nilai", format="%.6f"),
            "Penjelasan": st.column_config.TextColumn("Penjelasan"),
        },
    )


def main() -> None:
    st.set_page_config(
        page_title="Phishing URL Detector",
        layout="centered",
    )

    st.title("Phishing URL Detector")
    st.subheader("Prototype Sistem Keamanan Website Edukasi Berbasis Machine Learning")
    st.caption("Prototype Penelitian – Studi Kasus Robobrick Lab")

    st.divider()
    st.subheader("Informasi Penelitian")
    research_columns = st.columns(4)
    research_items = [
        ("Studi Kasus", "Robobrick Lab, Medan"),
        ("Metode", "XGBoost"),
        ("Analisis", "URL-based phishing detection"),
        ("Fitur", "7 karakteristik URL"),
    ]
    for column, (label, value) in zip(research_columns, research_items):
        with column:
            st.markdown(f"**{label}**")
            st.write(value)

    st.divider()
    st.subheader("Analisis URL")
    st.write(
        "Masukkan URL lengkap untuk menganalisis karakteristiknya secara lokal. "
        "Aplikasi tidak membuka atau mengakses website tujuan."
    )

    st.info(
        "Gunakan URL dengan skema `http://` atau `https://` agar parsing domain "
        "dan deteksi HTTPS mengikuti extractor penelitian."
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
            "Masukkan URL yang akan dianalisis",
            placeholder="Contoh: https://www.robobricklab.com/",
            help="Sistem hanya menganalisis teks URL dan tidak mengakses website tersebut.",
        )
        submitted = st.form_submit_button("Analisis URL", type="primary")

    if submitted:
        validation_error = validate_url(url)
        if validation_error:
            st.warning(validation_error)
        else:
            with st.spinner("Menganalisis karakteristik URL..."):
                try:
                    prediction, phishing_probability, legitimate_probability, feature_table = (
                        predict_url(url.strip(), feature_names)
                    )
                    render_result(
                        prediction,
                        phishing_probability,
                        legitimate_probability,
                        feature_table,
                    )
                except Exception as error:
                    st.error(f"Analisis tidak dapat dilakukan: {error}")

    st.divider()
    st.subheader("Pengujian Konsistensi Final Test")
    st.write(
        "Jalankan sepuluh sampel final test menggunakan model dan feature extractor "
        "yang sama. URL hanya diproses sebagai string dan tidak diakses."
    )

    if st.button("Jalankan 10 Pengujian Final Test"):
        with st.spinner("Menjalankan 10 pengujian final test..."):
            try:
                final_test_results = run_final_test(feature_names)
            except Exception as error:
                st.error(f"Pengujian final test tidak dapat dilakukan: {error}")
            else:
                st.dataframe(
                    final_test_results,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "No": st.column_config.NumberColumn("No", width="small"),
                        "URL": st.column_config.TextColumn("URL"),
                        "Ground Truth": st.column_config.TextColumn("Ground Truth"),
                        "Prediksi Model": st.column_config.TextColumn("Prediksi Model"),
                        "Prob. Phishing": st.column_config.TextColumn("Prob. Phishing"),
                        "Prob. Legitimate": st.column_config.TextColumn(
                            "Prob. Legitimate"
                        ),
                        "Status": st.column_config.TextColumn("Status"),
                    },
                )

                correct_count = int((final_test_results["Status"] == "BENAR").sum())
                incorrect_count = len(final_test_results) - correct_count
                consistency_percentage = correct_count / len(final_test_results) * 100

                summary_columns = st.columns(3)
                with summary_columns[0]:
                    st.metric("Jumlah pengujian", len(final_test_results))
                with summary_columns[1]:
                    st.metric("Prediksi benar", correct_count)
                with summary_columns[2]:
                    st.metric("Prediksi salah", incorrect_count)

                st.metric(
                    "Persentase konsistensi pengujian 10 sampel",
                    f"{consistency_percentage:.2f}%",
                )
                st.caption(
                    "Sampel pengujian berasal dari final test set penelitian. "
                    "Ground truth berasal dari label dataset. Pengujian aplikasi "
                    "tidak melakukan akses terhadap URL tujuan."
                )

    st.divider()
    st.subheader("Informasi Model")
    model_columns = st.columns(4)
    model_items = [
        ("Model Machine Learning", feature_info.get("model", "XGBoost")),
        ("Jumlah Fitur", str(feature_info.get("number_of_features", len(feature_names)))),
        ("Jenis Analisis", "URL-based"),
        ("Feature Extractor", "feature_extractor.py"),
    ]
    for column, (label, value) in zip(model_columns, model_items):
        with column:
            st.markdown(f"**{label}**")
            st.write(value)

    st.divider()
    st.warning(
        "Catatan: Sistem ini hanya menganalisis karakteristik URL menggunakan 7 fitur "
        "yang telah ditentukan. Hasil prediksi merupakan indikasi berbasis model "
        "Machine Learning dan bukan jaminan mutlak bahwa suatu website aman atau "
        "berbahaya. Jangan membuka URL mencurigakan hanya berdasarkan hasil aplikasi ini."
    )


if __name__ == "__main__":
    main()