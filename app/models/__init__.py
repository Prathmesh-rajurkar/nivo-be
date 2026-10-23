from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean,
    Numeric, ForeignKey, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class PlanType(str, enum.Enum):
    DIRECT = "Direct"
    REGULAR = "Regular"


class OptionType(str, enum.Enum):
    GROWTH = "Growth"
    IDCW = "IDCW"


class SEBIClassification(str, enum.Enum):
    LOW = "Low"
    LOW_TO_MODERATE = "Low to Moderate"
    MODERATE = "Moderate"
    MODERATELY_HIGH = "Moderately High"
    HIGH = "High"
    VERY_HIGH = "Very High"


class AMC(Base):
    __tablename__ = "amc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    schemes = relationship("Scheme", back_populates="amc")


class Scheme(Base):
    __tablename__ = "scheme"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amfi_code = Column(Integer, unique=True, nullable=False, index=True)
    isin_growth = Column(String(20), nullable=True)
    isin_dividend = Column(String(20), nullable=True)
    name = Column(String(500), nullable=False)
    amc_id = Column(Integer, ForeignKey("amc.id"), nullable=False)
    scheme_type = Column(String(100), nullable=True)
    amfi_category = Column(String(200), nullable=True)
    sebi_category = Column(String(200), nullable=True, index=True)
    plan = Column(SQLEnum(PlanType), nullable=False, default=PlanType.DIRECT)
    option_type = Column(SQLEnum(OptionType), nullable=False, default=OptionType.GROWTH)
    inception_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    amc = relationship("AMC", back_populates="schemes")
    nav_history = relationship("NAVDaily", back_populates="scheme", lazy="dynamic")
    metrics = relationship("FundMetrics", back_populates="scheme", uselist=False)
    static_info = relationship("SchemeStatic", back_populates="scheme", uselist=False)
    manager = relationship("SchemeManager", back_populates="scheme", uselist=False)

    __table_args__ = (
        Index("ix_scheme_sebi_plan_option", "sebi_category", "plan", "option_type"),
    )


class NAVDaily(Base):
    __tablename__ = "nav_daily"

    scheme_id = Column(Integer, ForeignKey("scheme.id"), primary_key=True)
    nav_date = Column(Date, primary_key=True)
    nav = Column(Numeric(18, 6), nullable=False)

    scheme = relationship("Scheme", back_populates="nav_history")

    __table_args__ = (
        Index("ix_nav_daily_scheme_date", "scheme_id", "nav_date"),
    )


class BenchmarkIndex(Base):
    __tablename__ = "benchmark_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)
    source = Column(String(50), nullable=True)


class BenchmarkTRIDaily(Base):
    __tablename__ = "benchmark_tri_daily"

    benchmark_id = Column(Integer, ForeignKey("benchmark_index.id"), primary_key=True)
    tri_date = Column(Date, primary_key=True)
    tri_value = Column(Numeric(18, 6), nullable=False)

    benchmark = relationship("BenchmarkIndex")


class SchemeBenchmark(Base):
    __tablename__ = "scheme_benchmark"

    scheme_id = Column(Integer, ForeignKey("scheme.id"), primary_key=True)
    benchmark_id = Column(Integer, ForeignKey("benchmark_index.id"), primary_key=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)

    scheme = relationship("Scheme")
    benchmark = relationship("BenchmarkIndex")


class RiskFreeRate(Base):
    __tablename__ = "risk_free_rate"

    rate_date = Column(Date, primary_key=True)
    rate_91d_tbill = Column(Numeric(10, 6), nullable=False)


class FundMetrics(Base):
    __tablename__ = "fund_metrics"

    scheme_id = Column(Integer, ForeignKey("scheme.id"), primary_key=True)
    as_of_date = Column(Date, primary_key=True)

    # Returns
    ret_3m = Column(Numeric(10, 6))
    ret_6m = Column(Numeric(10, 6))
    ret_1y = Column(Numeric(10, 6))
    cagr_3y = Column(Numeric(10, 6))
    cagr_5y = Column(Numeric(10, 6))
    cagr_10y = Column(Numeric(10, 6))
    rolling_3y_avg = Column(Numeric(10, 6))
    ret_vs_cat_1y = Column(Numeric(10, 6))
    ret_vs_cat_3y = Column(Numeric(10, 6))
    ret_vs_cat_5y = Column(Numeric(10, 6))
    ret_vs_cat_10y = Column(Numeric(10, 6))

    # Risk & Performance
    alpha = Column(Numeric(10, 6))
    beta = Column(Numeric(10, 6))
    volatility = Column(Numeric(10, 6))
    sharpe_ratio = Column(Numeric(10, 6))
    sortino_ratio = Column(Numeric(10, 6))
    max_drawdown = Column(Numeric(10, 6))
    tracking_error = Column(Numeric(10, 6))
    category_std_dev = Column(Numeric(10, 6))
    pct_from_ath = Column(Numeric(10, 6))

    # Portfolio (Phase 2)
    equity_pct = Column(Numeric(10, 6))
    debt_pct = Column(Numeric(10, 6))
    cash_pct = Column(Numeric(10, 6))
    largecap_pct = Column(Numeric(10, 6))
    midcap_pct = Column(Numeric(10, 6))
    smallcap_pct = Column(Numeric(10, 6))
    top3_concentration = Column(Numeric(10, 6))
    top5_concentration = Column(Numeric(10, 6))
    top10_concentration = Column(Numeric(10, 6))
    sovereign_debt_pct = Column(Numeric(10, 6))
    corporate_debt_pct = Column(Numeric(10, 6))
    bonds_rated_a_pct = Column(Numeric(10, 6))
    bonds_rated_b_pct = Column(Numeric(10, 6))
    bonds_poorly_rated_pct = Column(Numeric(10, 6))

    # Valuation & Debt
    pe_ratio = Column(Numeric(10, 6))
    category_pe_ratio = Column(Numeric(10, 6))
    avg_maturity = Column(Numeric(10, 6))
    avg_ytm = Column(Numeric(10, 6))
    category_ytm = Column(Numeric(10, 6))

    # Current NAV
    nav = Column(Numeric(18, 6))

    scheme = relationship("Scheme", back_populates="metrics")


class SchemeStatic(Base):
    __tablename__ = "scheme_static"

    scheme_id = Column(Integer, ForeignKey("scheme.id"), primary_key=True)
    benchmark_name = Column(String(200), nullable=True)
    fund_manager = Column(String(200), nullable=True)
    exit_load = Column(Text, nullable=True)
    lock_in_period = Column(String(100), nullable=True)
    min_lumpsum = Column(Integer, nullable=True)
    min_sip = Column(Integer, nullable=True)
    sip_available = Column(Boolean, default=True)
    base_expense_ratio = Column(Numeric(10, 6))
    total_expense_ratio = Column(Numeric(10, 6))
    sebi_risk_level = Column(SQLEnum(SEBIClassification), nullable=True)
    avg_maturity = Column(Numeric(10, 6))
    avg_ytm = Column(Numeric(10, 6))

    scheme = relationship("Scheme", back_populates="static_info")


class SchemeManager(Base):
    __tablename__ = "scheme_manager"

    scheme_id = Column(Integer, ForeignKey("scheme.id"), primary_key=True)
    manager_name = Column(String(200), nullable=False)
    since_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)

    scheme = relationship("Scheme", back_populates="manager")