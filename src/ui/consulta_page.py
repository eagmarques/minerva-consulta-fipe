from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.providers.api_provider import (
    ApiProvider,
    FipeAuthError,
    FipeNotFoundError,
    FipeProviderError,
    FipeServerError,
    FipeSubscriptionError,
)
from src.services.fipe_service import FipeService

VEHICLE_TYPES = {
    "Carros": "cars",
    "Motos": "motorcycles",
    "Caminhões": "trucks",
}


def _init_state() -> None:
    defaults = {
        "vehicle_type": "",
        "reference": "",
        "brand_id": "",
        "model_id": "",
        "year_id": "",
        "price_result": None,
        "consulted_at": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _reset_from(level: str) -> None:
    if level == "vehicle":
        st.session_state.reference = ""
        st.session_state.brand_id = ""
        st.session_state.model_id = ""
        st.session_state.year_id = ""
    elif level == "reference":
        st.session_state.brand_id = ""
        st.session_state.model_id = ""
        st.session_state.year_id = ""
    elif level == "brand":
        st.session_state.model_id = ""
        st.session_state.year_id = ""
    elif level == "model":
        st.session_state.year_id = ""

    st.session_state.price_result = None
    st.session_state.consulted_at = ""


@st.cache_resource(show_spinner=False)
def _get_service() -> FipeService:
    provider = ApiProvider()
    return FipeService(provider=provider)


@st.cache_data(show_spinner=False)
def _cached_references() -> list[tuple[str, str]]:
    service = _get_service()
    return [(item.code, item.month) for item in service.list_references()]


@st.cache_data(show_spinner=False)
def _cached_brands(vehicle_type: str, reference: str) -> list[tuple[str, str]]:
    service = _get_service()
    return [(item.code, item.name) for item in service.list_brands(vehicle_type, reference)]


@st.cache_data(show_spinner=False)
def _cached_models(vehicle_type: str, brand_id: str, reference: str) -> list[tuple[str, str]]:
    service = _get_service()
    return [
        (item.code, item.name) for item in service.list_models(vehicle_type, brand_id, reference)
    ]


@st.cache_data(show_spinner=False)
def _cached_years(
    vehicle_type: str,
    brand_id: str,
    model_id: str,
    reference: str,
) -> list[tuple[str, str]]:
    service = _get_service()
    return [
        (item.code, item.name)
        for item in service.list_years(
            vehicle_type=vehicle_type,
            brand_id=brand_id,
            model_id=model_id,
            reference=reference,
        )
    ]


def _latest_three_references(references: list[tuple[str, str]]) -> list[tuple[str, str]]:
    def _to_sort_key(item: tuple[str, str]) -> int:
        try:
            return int(item[0])
        except ValueError:
            return -1

    return sorted(references, key=_to_sort_key, reverse=True)[:3]


def _render_selectbox(
    label: str,
    key: str,
    options: dict[str, str],
    reset_level: str | None = None,
) -> str:
    values = [""] + list(options.keys())
    if st.session_state.get(key, "") not in values:
        st.session_state[key] = ""
    selected = st.selectbox(
        label=label,
        options=values,
        key=key,
        format_func=lambda value: "Selecione..." if not value else options[value],
    )
    if reset_level:
        previous_key = f"_previous_{key}"
        previous_value = st.session_state.get(previous_key, "")
        if selected != previous_value:
            _reset_from(reset_level)
        st.session_state[previous_key] = selected
    return selected


def _show_provider_error(error: FipeProviderError) -> None:
    if isinstance(error, FipeSubscriptionError):
        st.error(
            "A API retornou 402 (assinatura/plano). "
            "Verifique se o FIPE_TOKEN possui acesso a este endpoint."
        )
        return
    if isinstance(error, FipeAuthError):
        st.error("Token inválido ou ausente. Configure FIPE_TOKEN corretamente.")
        return
    if isinstance(error, FipeServerError):
        st.error("A API FIPE está indisponível no momento. Tente novamente.")
        return
    if isinstance(error, FipeNotFoundError):
        st.error("Recurso não encontrado para os filtros selecionados.")
        return
    st.error(str(error))


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background: radial-gradient(circle at top, #172338 0%, #0b1322 45%, #08101d 100%);
        }
        .block-container{
            max-width: 920px;
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }
        .fipe-hero{
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: rgba(15, 23, 42, 0.7);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-bottom: 1.1rem;
        }
        .fipe-hero p{
            margin: 0;
            color: #dbeafe;
            line-height: 1.5;
        }
        .stSelectbox > label{
            font-weight: 600;
        }
        div[data-baseweb="select"] > div{
            border-radius: 10px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.95);
        }
        div[data-testid="stButton"] button{
            width: 100%;
            border-radius: 10px;
            height: 2.8rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }
        [data-testid="stDataFrame"]{
            border: 1px solid rgba(148, 163, 184, 0.3);
            border-radius: 12px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Consulta FIPE", page_icon=":oncoming_automobile:", layout="centered"
    )
    _apply_theme()
    st.title("Consulta Tabela FIPE")
    st.markdown(
        """
        <div class="fipe-hero">
            <p>
                Esta aplicação consulta o valor médio de veículos na Tabela FIPE
                usando a API oficial. Selecione tipo, mês de referência, marca,
                modelo e ano/combustível para obter o preço atualizado em segundos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _init_state()

    try:
        service = _get_service()
    except FipeAuthError as error:
        st.error(str(error))
        return

    vehicle_map = {value: key for key, value in VEHICLE_TYPES.items()}
    vehicle_type = _render_selectbox(
        label="Tipo de veículo",
        key="vehicle_type",
        options=vehicle_map,
        reset_level="vehicle",
    )

    reference_options: dict[str, str] = {}
    if vehicle_type:
        try:
            with st.spinner("Carregando meses de referência..."):
                references = _latest_three_references(_cached_references())
            reference_options = {code: label for code, label in references}
        except FipeProviderError as error:
            _show_provider_error(error)
            return

    reference = _render_selectbox(
        label="Mês de referência",
        key="reference",
        options=reference_options,
        reset_level="reference" if reference_options else None,
    )
    if reference_options:
        st.caption("Exibindo somente os 3 meses mais recentes para evitar erro de retorno da API.")

    brand_options: dict[str, str] = {}
    if reference:
        try:
            with st.spinner("Carregando marcas..."):
                brands = _cached_brands(vehicle_type, reference)
            brand_options = {code: name for code, name in brands}
        except FipeProviderError as error:
            _show_provider_error(error)
            return

    brand_id = _render_selectbox(
        label="Marca",
        key="brand_id",
        options=brand_options,
        reset_level="brand" if brand_options else None,
    )

    model_options: dict[str, str] = {}
    if brand_id:
        try:
            with st.spinner("Carregando modelos..."):
                models = _cached_models(vehicle_type, brand_id, reference)
            model_options = {code: name for code, name in models}
        except FipeProviderError as error:
            _show_provider_error(error)
            return

    model_id = _render_selectbox(
        label="Modelo",
        key="model_id",
        options=model_options,
        reset_level="model" if model_options else None,
    )

    year_options: dict[str, str] = {}
    if model_id:
        try:
            with st.spinner("Carregando anos e combustível..."):
                years = _cached_years(vehicle_type, brand_id, model_id, reference)
            year_options = {code: name for code, name in years}
        except FipeProviderError as error:
            _show_provider_error(error)
            return

    year_id = _render_selectbox(
        label="Ano + combustível",
        key="year_id",
        options=year_options,
        reset_level=None,
    )

    can_consult = all(
        [
            st.session_state.vehicle_type,
            st.session_state.reference,
            st.session_state.brand_id,
            st.session_state.model_id,
            st.session_state.year_id,
        ]
    )

    if st.button("Consultar", type="primary", disabled=not can_consult):
        try:
            with st.spinner("Consultando preço FIPE..."):
                st.session_state.price_result = service.get_price(
                    vehicle_type,
                    brand_id,
                    model_id,
                    year_id,
                    reference,
                )
                st.session_state.consulted_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        except FipeProviderError as error:
            _show_provider_error(error)

    if st.session_state.price_result:
        st.subheader("Resultado da consulta")
        result = st.session_state.price_result
        rows = [
            {"Campo": "Mês de referência", "Valor": result.reference_month},
            {"Campo": "Código Fipe", "Valor": result.code_fipe},
            {"Campo": "Marca", "Valor": result.brand},
            {"Campo": "Modelo", "Valor": result.model},
            {"Campo": "Ano Modelo", "Valor": result.model_year},
            {"Campo": "Data da consulta", "Valor": st.session_state.consulted_at or "-"},
            {"Campo": "Preço Médio", "Valor": result.price},
        ]
        result_df = pd.DataFrame(rows)
        st.dataframe(result_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
