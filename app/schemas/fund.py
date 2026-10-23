from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class PlanType(str, Enum):
    DIRECT = "Direct"
    REGULAR = "Regular"


class OptionType(str, Enum):
    GROWTH = "Growth"
    IDCW = "IDCW"


class SEBIRiskLevel(str, Enum):
    LOW = "Low"
    LOW_TO_MODERATE = "Low to Moderate"
    MODERATE = "Moderate"
    MODERATELY_HIGH = "Moderately High"
    HIGH = "High"
    VERY_HIGH = "Very High"


# --- Search Results ---
class FundSearchResult(BaseModel):
    scheme_id: str
    amfi_code: int
    name: str
    amc_name: str
    sebi_category: str
    plan: PlanType
    option_type: OptionType
    nav: Optional[Decimal] = None
    nav_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


# --- Fund Detail ---
class FundStatic(BaseModel):
    scheme_id: str
    amfi_code: int
    name: str
    amc_name: str
    scheme_type: str
    amfi_category: str
    sebi_category: str
    plan: PlanType
    option_type: OptionType
    inception_date: Optional[date] = None
    is_active: bool
    benchmark_name: Optional[str] = None
    fund_manager: Optional[str] = None
    exit_load: Optional[str] = None
    lock_in_period: Optional[str] = None
    min_lumpsum: Optional[int] = None
    min_sip: Optional[int] = None
    sip_available: bool
    base_expense_ratio: Optional[Decimal] = None
    total_expense_ratio: Optional[Decimal] = None
    sebi_risk_level: Optional[SEBIRiskLevel] = None
    avg_maturity: Optional[Decimal] = None
    avg_ytm: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class FundMetrics(BaseModel):
    as_of_date: date
    scheme_id: str

    # Returns
    ret_3m: Optional[Decimal] = None
    ret_6m: Optional[Decimal] = None
    ret_1y: Optional[Decimal] = None
    cagr_3y: Optional[Decimal] = None
    cagr_5y: Optional[Decimal] = None
    cagr_10y: Optional[Decimal] = None
    rolling_3y_avg: Optional[Decimal] = None
    ret_vs_cat_1y: Optional[Decimal] = None
    ret_vs_cat_3y: Optional[Decimal] = None
    ret_vs_cat_5y: Optional[Decimal] = None
    ret_vs_cat_10y: Optional[Decimal] = None

    # Risk & Performance
    alpha: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    volatility: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    sortino_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    tracking_error: Optional[Decimal] = None
    category_std_dev: Optional[Decimal] = None
    pct_from_ath: Optional[Decimal] = None

    # Portfolio (Phase 2)
    equity_pct: Optional[Decimal] = None
    debt_pct: Optional[Decimal] = None
    cash_pct: Optional[Decimal] = None
    largecap_pct: Optional[Decimal] = None
    midcap_pct: Optional[Decimal] = None
    smallcap_pct: Optional[Decimal] = None
    top3_concentration: Optional[Decimal] = None
    top5_concentration: Optional[Decimal] = None
    top10_concentration: Optional[Decimal] = None
    sovereign_debt_pct: Optional[Decimal] = None
    corporate_debt_pct: Optional[Decimal] = None
    bonds_rated_a_pct: Optional[Decimal] = None
    bonds_rated_b_pct: Optional[Decimal] = None
    bonds_poorly_rated_pct: Optional[Decimal] = None

    # Valuation & Debt
    pe_ratio: Optional[Decimal] = None
    category_pe_ratio: Optional[Decimal] = None
    avg_maturity: Optional[Decimal] = None
    avg_ytm: Optional[Decimal] = None
    category_ytm: Optional[Decimal] = None

    # Current NAV
    nav: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class FundDetailResponse(BaseModel):
    static: FundStatic
    metrics: Optional[FundMetrics] = None

    model_config = ConfigDict(from_attributes=True)


# --- Compare ---
class CompareResponse(BaseModel):
    funds: List[FundDetailResponse]


# --- Categories ---
class CategoryInfo(BaseModel):
    sebi_category: str
    fund_count: int