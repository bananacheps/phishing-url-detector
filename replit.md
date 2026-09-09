# Phishing URL Detector

Prototype Streamlit untuk mendeteksi URL yang terindikasi phishing atau legitimate menggunakan model XGBoost yang diunggah pengguna.

## Run & Operate

- `streamlit run app.py --server.port 5000` — run the Phishing URL Detector
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Model dan extractor berada di `model_assets/`; tidak menggunakan database atau API eksternal.

## Stack

- Python 3.11, Streamlit, XGBoost, Pandas, NumPy, Joblib
- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `app.py` — antarmuka Streamlit dan alur prediksi
- `model_assets/feature_extractor.py` — extractor fitur yang diunggah, dipakai tanpa perubahan
- `model_assets/model_xgboost_7fitur.pkl` — model XGBoost yang diunggah
- `model_assets/feature_info.json` — metadata dan urutan tujuh fitur

## Architecture decisions

- Fitur diekstrak dari teks URL secara lokal; aplikasi tidak membuka, scraping, atau memanggil URL target.
- Probabilitas diambil langsung dari `predict_proba` model yang diunggah.
- Kelas model dipetakan sebagai `0 = Legitimate` dan `1 = Phishing`.

## Product

- Pengguna memasukkan URL dan menerima label prediksi beserta probabilitas phishing dan legitimate.
- Tujuh fitur yang digunakan ditampilkan dalam tabel untuk kebutuhan demonstrasi penelitian.

## User preferences

- Antarmuka menggunakan bahasa Indonesia.
- Jangan mengubah logika extractor atau membuat model Machine Learning baru.

## Gotchas

- URL dianalisis persis seperti input pengguna; masukkan skema URL jika ingin parsing domain dan deteksi HTTPS bekerja sesuai extractor.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
