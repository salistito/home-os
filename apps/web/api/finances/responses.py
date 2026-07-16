from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.finances.types import (
    Entry,
    FinanceOperationStatus,
    Period,
    PeriodDetail,
)

_STATUS_HTTP = {
    FinanceOperationStatus.INVALID_LABEL: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.DUPLICATE_LABEL: HTTPStatus.CONFLICT,
    FinanceOperationStatus.INVALID_AMOUNT: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.AMOUNT_REQUIRED: HTTPStatus.CONFLICT,
    FinanceOperationStatus.INVALID_KIND: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.INVALID_SCOPE: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.INVALID_DETAIL_MODE: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.INCOME_MUST_BE_PERSONAL: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.NOT_PENDING: HTTPStatus.CONFLICT,
    FinanceOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    FinanceOperationStatus.INVALID_LABEL: "El nombre no puede estar vacío.",
    FinanceOperationStatus.DUPLICATE_LABEL: "Ya existe un mes con ese nombre.",
    FinanceOperationStatus.INVALID_AMOUNT: "El monto no puede ser negativo.",
    FinanceOperationStatus.AMOUNT_REQUIRED: "Agrega un monto antes de confirmar.",
    FinanceOperationStatus.INVALID_KIND: "Tipo de movimiento inválido.",
    FinanceOperationStatus.INVALID_SCOPE: "Ámbito inválido.",
    FinanceOperationStatus.INVALID_DETAIL_MODE: "Modo de detalle inválido.",
    FinanceOperationStatus.INCOME_MUST_BE_PERSONAL: "Un ingreso debe ser personal.",
    FinanceOperationStatus.NOT_PENDING: "El movimiento ya no está pendiente.",
    FinanceOperationStatus.NOT_FOUND: "No encontrado.",
}


def serialize_period(period: Period) -> dict:
    return {
        "id": period.id,
        "label": period.label,
        "status": period.status,
        "opened_at": period.opened_at,
    }


def serialize_entry(entry: Entry) -> dict:
    return {
        "id": entry.id,
        "period_id": entry.period_id,
        "kind": entry.kind,
        "scope": entry.scope,
        "owner_id": entry.owner_id,
        "label": entry.label,
        "amount": entry.amount,
        "status": entry.status,
        "paid_at": entry.paid_at,
        "detail_mode": entry.detail_mode,
        "created_at": entry.created_at,
        "details": [
            {
                "id": d.id,
                "entry_id": d.entry_id,
                "label": d.label,
                "amount": d.amount,
            }
            for d in entry.details
        ],
    }


def serialize_period_detail(detail: PeriodDetail) -> dict:
    summary = detail.summary
    return {
        **serialize_period(detail.period),
        "entries": [serialize_entry(e) for e in detail.entries],
        "summary": {
            "shared_total": summary.shared_total,
            "contributions": summary.contributions,
            "people": [
                {
                    "owner_id": p.owner_id,
                    "income": p.income,
                    "expense": p.expense,
                    "balance": p.balance,
                }
                for p in summary.people
            ],
        },
    }


def error_response(status: FinanceOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE[status]},
        status_code=_STATUS_HTTP[status],
    )


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_request", "message": message},
        status_code=HTTPStatus.BAD_REQUEST,
    )
