from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, or_, and_, String
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date
from decimal import Decimal
from app.db.session import get_db
from app.models import Scheme, AMC, FundMetrics, SchemeStatic, SchemeManager, BenchmarkIndex
from app.schemas.fund import (
    FundSearchResult, FundDetailResponse, CompareResponse, CategoryInfo,
    FundStatic, FundMetrics as FundMetricsSchema
)
from app.services.cache import cache_service
from app.core.config import settings


router = APIRouter(prefix="/funds", tags=["funds"])


def _make_scheme_id(scheme: Scheme) -> str:
    """Generate a unique scheme identifier."""
    return f"{scheme.amc.name.upper().replace(' ', '_')}_{scheme.name.upper().replace(' ', '_').replace('-', '_')}_{scheme.plan.value}_{scheme.option_type.value}"


def _build_search_result(scheme: Scheme, nav: Optional[Decimal] = None, nav_date: Optional[date] = None) -> FundSearchResult:
    return FundSearchResult(
        scheme_id=_make_scheme_id(scheme),
        amfi_code=scheme.amfi_code,
        name=scheme.name,
        amc_name=scheme.amc.name if scheme.amc else "",
        sebi_category=scheme.sebi_category or "",
        plan=scheme.plan,
        option_type=scheme.option_type,
        nav=nav,
        nav_date=nav_date,
    )


@router.get("/search", response_model=List[FundSearchResult])
async def search_funds(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search funds by name, AMC, or category."""
    cache_key = f"search:{q.lower()}:{limit}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Build search query
    search_term = f"%{q}%"
    stmt = (
        select(Scheme, FundMetrics.nav, FundMetrics.as_of_date)
        .join(AMC, Scheme.amc_id == AMC.id)
        .outerjoin(FundMetrics, and_(
            FundMetrics.scheme_id == Scheme.id,
            FundMetrics.as_of_date == select(func.max(FundMetrics.as_of_date))
                .where(FundMetrics.scheme_id == Scheme.id)
                .scalar_subquery()
        ))
        .where(
            and_(
                Scheme.is_active == True,
                Scheme.plan == "Direct",
                Scheme.option_type == "Growth",
                or_(
                    Scheme.name.ilike(search_term),
                    AMC.name.ilike(search_term),
                    Scheme.sebi_category.ilike(search_term),
                    Scheme.amfi_code.cast(String).ilike(search_term),
                ),
            )
        )
        .order_by(Scheme.name)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    funds = [
        _build_search_result(scheme, nav, nav_date)
        for scheme, nav, nav_date in rows
    ]

    await cache_service.set(cache_key, [f.model_dump() for f in funds], settings.CACHE_TTL_SECONDS)
    return funds


@router.get("/{scheme_id}", response_model=FundDetailResponse)
async def get_fund_detail(
    scheme_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full fund detail with all metrics."""
    cache_key = f"fund:{scheme_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Find scheme by our generated scheme_id pattern
    # scheme_id format: AMC_NAME_FUND_NAME_PLAN_OPTION
    # We need to reverse-engineer or do a broader search
    stmt = (
        select(Scheme, FundMetrics, SchemeStatic, SchemeManager, AMC)
        .join(AMC, Scheme.amc_id == AMC.id)
        .outerjoin(FundMetrics, and_(
            FundMetrics.scheme_id == Scheme.id,
            FundMetrics.as_of_date == select(func.max(FundMetrics.as_of_date))
                .where(FundMetrics.scheme_id == Scheme.id)
                .scalar_subquery()
        ))
        .outerjoin(SchemeStatic, SchemeStatic.scheme_id == Scheme.id)
        .outerjoin(SchemeManager, and_(
            SchemeManager.scheme_id == Scheme.id,
            SchemeManager.is_current == True
        ))
        .where(
            and_(
                Scheme.is_active == True,
                Scheme.plan == "Direct",
                Scheme.option_type == "Growth",
            )
        )
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Find matching scheme_id
    matched = None
    for scheme, metrics, static, manager, amc in rows:
        if _make_scheme_id(scheme) == scheme_id:
            matched = (scheme, metrics, static, manager, amc)
            break

    if not matched:
        raise HTTPException(status_code=404, detail="Fund not found")

    scheme, metrics, static, manager, amc = matched

    # Build response
    static_data = FundStatic(
        scheme_id=_make_scheme_id(scheme),
        amfi_code=scheme.amfi_code,
        name=scheme.name,
        amc_name=amc.name,
        scheme_type=scheme.scheme_type or "",
        amfi_category=scheme.amfi_category or "",
        sebi_category=scheme.sebi_category or "",
        plan=scheme.plan,
        option_type=scheme.option_type,
        inception_date=scheme.inception_date,
        is_active=scheme.is_active,
        benchmark_name=static.benchmark_name if static else None,
        fund_manager=manager.manager_name if manager else (static.fund_manager if static else None),
        exit_load=static.exit_load if static else None,
        lock_in_period=static.lock_in_period if static else None,
        min_lumpsum=static.min_lumpsum if static else None,
        min_sip=static.min_sip if static else None,
        sip_available=static.sip_available if static else True,
        base_expense_ratio=static.base_expense_ratio if static else None,
        total_expense_ratio=static.total_expense_ratio if static else None,
        sebi_risk_level=static.sebi_risk_level if static else None,
        avg_maturity=static.avg_maturity if static else None,
        avg_ytm=static.avg_ytm if static else None,
    )

    metrics_data = None
    if metrics:
        metrics_data = FundMetricsSchema(
            as_of_date=metrics.as_of_date,
            scheme_id=_make_scheme_id(scheme),
            ret_3m=metrics.ret_3m,
            ret_6m=metrics.ret_6m,
            ret_1y=metrics.ret_1y,
            cagr_3y=metrics.cagr_3y,
            cagr_5y=metrics.cagr_5y,
            cagr_10y=metrics.cagr_10y,
            rolling_3y_avg=metrics.rolling_3y_avg,
            ret_vs_cat_1y=metrics.ret_vs_cat_1y,
            ret_vs_cat_3y=metrics.ret_vs_cat_3y,
            ret_vs_cat_5y=metrics.ret_vs_cat_5y,
            ret_vs_cat_10y=metrics.ret_vs_cat_10y,
            alpha=metrics.alpha,
            beta=metrics.beta,
            volatility=metrics.volatility,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            max_drawdown=metrics.max_drawdown,
            tracking_error=metrics.tracking_error,
            category_std_dev=metrics.category_std_dev,
            pct_from_ath=metrics.pct_from_ath,
            equity_pct=metrics.equity_pct,
            debt_pct=metrics.debt_pct,
            cash_pct=metrics.cash_pct,
            largecap_pct=metrics.largecap_pct,
            midcap_pct=metrics.midcap_pct,
            smallcap_pct=metrics.smallcap_pct,
            top3_concentration=metrics.top3_concentration,
            top5_concentration=metrics.top5_concentration,
            top10_concentration=metrics.top10_concentration,
            sovereign_debt_pct=metrics.sovereign_debt_pct,
            corporate_debt_pct=metrics.corporate_debt_pct,
            bonds_rated_a_pct=metrics.bonds_rated_a_pct,
            bonds_rated_b_pct=metrics.bonds_rated_b_pct,
            bonds_poorly_rated_pct=metrics.bonds_poorly_rated_pct,
            pe_ratio=metrics.pe_ratio,
            category_pe_ratio=metrics.category_pe_ratio,
            avg_maturity=metrics.avg_maturity,
            avg_ytm=metrics.avg_ytm,
            category_ytm=metrics.category_ytm,
            nav=metrics.nav,
        )

    response = FundDetailResponse(static=static_data, metrics=metrics_data)
    await cache_service.set(cache_key, response.model_dump(), settings.CACHE_TTL_SECONDS)
    return response


@router.get("/compare", response_model=CompareResponse)
async def compare_funds(
    ids: str = Query(..., description="Comma-separated scheme IDs"),
    db: AsyncSession = Depends(get_db),
):
    """Compare multiple funds side by side."""
    scheme_ids = ids.split(",")[:5]  # Max 5 funds

    cache_key = f"compare:{','.join(sorted(scheme_ids))}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    funds = []
    for sid in scheme_ids:
        # Reuse the detail logic
        try:
            fund = await get_fund_detail(sid, db)
            funds.append(fund)
        except HTTPException:
            continue

    if not funds:
        raise HTTPException(status_code=404, detail="No valid funds found")

    response = CompareResponse(funds=funds)
    await cache_service.set(cache_key, response.model_dump(), settings.CACHE_TTL_SECONDS)
    return response


@router.get("/categories", response_model=List[CategoryInfo])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all SEBI categories with fund counts."""
    cache_key = "categories"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    stmt = (
        select(Scheme.sebi_category, func.count(Scheme.id))
        .where(
            and_(
                Scheme.is_active == True,
                Scheme.sebi_category.is_not(None),
            )
        )
        .group_by(Scheme.sebi_category)
        .order_by(Scheme.sebi_category)
    )

    result = await db.execute(stmt)
    categories = [
        CategoryInfo(sebi_category=cat, fund_count=count)
        for cat, count in result.all()
    ]

    await cache_service.set(cache_key, [c.model_dump() for c in categories], settings.CACHE_TTL_SECONDS)
    return categories