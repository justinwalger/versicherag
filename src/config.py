from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    gemini_api_key: str
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_chat_model: str = "gemini-3.6-flash"
    gemini_metadata_model: str = "gemini-3.6-flash"
    gemini_judge_model: str = "gemini-3.5-flash-lite"
    qdrant_host: str
    qdrant_api_key: str
    app_password: str
    qdrant_port: int = 6333
    qdrant_collection_name: str = "versicherungsassist_collection"
    qdrant_vector_size: int = 3072
    source_urls: list[str] = [
        # Private-customer documents, see README.md "Wichtige Dokumente"
        "https://www.ruv.de/dam/jcr:038d2022-558e-46d7-b161-e37647ff9a2d/PLG0426.pdf",
        "https://www.ruv.de/dam/jcr:3c83cc53-f7a0-4e80-8ec4-2f3f8e5a40fc/bedinungsheft-ruv-lebensversicherung-niederlassung-luxemburg.pdf",
        "https://www.ruv.de/dam/jcr:8f25cbab-bcc7-4ff4-ab73-2d80ab705dc3/Hinweis-zum-au%C3%9Fergerichtlichen-Streitbeiligungsverfahren-RVL.pdf",
        "https://www.ruv.de/dam/jcr:47a9ec12-7b45-4630-901c-d4a6e361ef97/mietkautionsbuergschaft-bedingungen.pdf",
        "https://www.ruv.de/dam/jcr:41df7b64-f3f4-48be-9230-0a74d7760284/ruv-kpr-privatkunden-privatpolice-verbraucherinfo.pdf",
        "https://www.ruv.de/dam/jcr:536cbb74-a0e6-47d3-be55-f2d2860f5030/ruv-kpp-privatkunden-privatpolice-comfort-verbraucherinfo.pdf",
        "https://www.ruv.de/dam/jcr:39eec8f2-3568-4374-9dde-87edb956fc4d/Allgemeine%20Bedingungen%20R+V-Ger%C3%A4teSchutz.pdf",
        "https://www.ruv.de/dam/jcr:a1e69927-3527-4ed5-8223-6ebe712d11d5/informationen-zum-darlehensvertrag.pdf",
        "https://www.ruv.de/dam/jcr:8cb02e39-1ef6-4a44-8c4e-7b02de852006/informationen-zum-prolongationsangebot.pdf",
        "https://www.ruv.de/dam/jcr:697df30d-36c9-478f-a8a0-f1783b7843e1/Verbraucherinformation_RVA_Pkw_01.07.2026.pdf",
        "https://www.ruv.de/dam/jcr:f353bb0b-7a8f-423e-8520-78e051971d79/Verbraucherinformation_RVA_Nicht-Pkw_01.07.2026.pdf",
        "https://www.ruv.de/dam/jcr:149bf1c9-4a74-45d3-845b-0f0f2fc554a8/ruv-kkm-moped-verbraucherinfo.pdf",
        "https://www.ruv.de/dam/jcr:266e323c-c558-4fa0-a67f-820016db0dd9/pkx0726.PDF",
        "https://www.ruv.de/dam/jcr:5bd1b54a-9b52-461f-b836-3bb598ddc3d0/KHR0123.PDF",
        "https://www.ruv.de/dam/jcr:454128d9-56f7-424c-a705-81bbdf4d8f31/privatkunden-verbraucherinformation-hausrat-haftpflicht-premium.pdf",
        "https://www.ruv.de/dam/jcr:c565a8f7-e260-4455-a33b-65e92d63c154/avb_tlp.PDF",
        "https://www.ruv.de/dam/jcr:99b0715a-b65a-40de-be08-d970a9659f5e/OPK_Pferd_AVB.pdf",
        "https://www.ruv.de/dam/jcr:b8a71fdc-2ee5-4c21-bd54-7f56ff63579a/opk-hund-avb-erweitert.pdf",
        "https://www.ruv.de/dam/jcr:14f4d452-1ae5-455d-8692-2adbf8f8429b/PUR0122.PDF",
        "https://www.ruv.de/dam/jcr:28f8bae4-36c3-4d94-95f2-4ba5eef3c1cc/kapital-unfallversicherung-avb-0122.pdf",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


class UISettings(BaseSettings):
    """Settings for the Streamlit frontend only - deliberately separate from Settings so the
    UI container never needs the backend's secrets (Gemini/Qdrant/APP_PASSWORD) just to start."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    backend_api_url: str = "http://127.0.0.1:8000/api"


@lru_cache
def get_ui_settings() -> UISettings:
    return UISettings()
