"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-10-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE plantype AS ENUM ('Direct', 'Regular')")
    op.execute("CREATE TYPE optiontype AS ENUM ('Growth', 'IDCW')")
    op.execute("CREATE TYPE sebirisklevel AS ENUM ('Low', 'Low to Moderate', 'Moderate', 'Moderately High', 'High', 'Very High')")

    # Create amc table
    op.create_table(
        'amc',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create scheme table
    op.create_table(
        'scheme',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amfi_code', sa.Integer(), nullable=False),
        sa.Column('isin_growth', sa.String(length=20), nullable=True),
        sa.Column('isin_dividend', sa.String(length=20), nullable=True),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('amc_id', sa.Integer(), nullable=False),
        sa.Column('scheme_type', sa.String(length=100), nullable=True),
        sa.Column('amfi_category', sa.String(length=200), nullable=True),
        sa.Column('sebi_category', sa.String(length=200), nullable=True),
        sa.Column('plan', sa.Enum('Direct', 'Regular', name='plantype'), nullable=False),
        sa.Column('option_type', sa.Enum('Growth', 'IDCW', name='optiontype'), nullable=False),
        sa.Column('inception_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['amc_id'], ['amc.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('amfi_code')
    )
    op.create_index('ix_scheme_sebi_plan_option', 'scheme', ['sebi_category', 'plan', 'option_type'], unique=False)

    # Create nav_daily table
    op.create_table(
        'nav_daily',
        sa.Column('scheme_id', sa.Integer(), nullable=False),
        sa.Column('nav_date', sa.Date(), nullable=False),
        sa.Column('nav', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.ForeignKeyConstraint(['scheme_id'], ['scheme.id'], ),
        sa.PrimaryKeyConstraint('scheme_id', 'nav_date')
    )
    op.create_index('ix_nav_daily_scheme_date', 'nav_daily', ['scheme_id', 'nav_date'], unique=False)

    # Create benchmark_index table
    op.create_table(
        'benchmark_index',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create benchmark_tri_daily table
    op.create_table(
        'benchmark_tri_daily',
        sa.Column('benchmark_id', sa.Integer(), nullable=False),
        sa.Column('tri_date', sa.Date(), nullable=False),
        sa.Column('tri_value', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.ForeignKeyConstraint(['benchmark_id'], ['benchmark_index.id'], ),
        sa.PrimaryKeyConstraint('benchmark_id', 'tri_date')
    )

    # Create scheme_benchmark table
    op.create_table(
        'scheme_benchmark',
        sa.Column('scheme_id', sa.Integer(), nullable=False),
        sa.Column('benchmark_id', sa.Integer(), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['scheme.id'], ),
        sa.ForeignKeyConstraint(['benchmark_id'], ['benchmark_index.id'], ),
        sa.PrimaryKeyConstraint('scheme_id', 'benchmark_id')
    )

    # Create risk_free_rate table
    op.create_table(
        'risk_free_rate',
        sa.Column('rate_date', sa.Date(), nullable=False),
        sa.Column('rate_91d_tbill', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.PrimaryKeyConstraint('rate_date')
    )

    # Create fund_metrics table
    op.create_table(
        'fund_metrics',
        sa.Column('scheme_id', sa.Integer(), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        # Returns
        sa.Column('ret_3m', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ret_6m', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ret_1y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cagr_3y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cagr_5y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cagr_10y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('rolling_3y_avg', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ret_vs_cat_1y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ret_vs_cat_3y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ret_vs_cat_5y', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('ret_vs_cat_10y', sa.Numeric(precision=10, scale=6), nullable=True),
        # Risk & Performance
        sa.Column('alpha', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('beta', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('volatility', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('sortino_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('tracking_error', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('category_std_dev', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('pct_from_ath', sa.Numeric(precision=10, scale=6), nullable=True),
        # Portfolio
        sa.Column('equity_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('debt_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cash_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('largecap_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('midcap_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('smallcap_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('top3_concentration', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('top5_concentration', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('top10_concentration', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('sovereign_debt_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('corporate_debt_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('bonds_rated_a_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('bonds_rated_b_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('bonds_poorly_rated_pct', sa.Numeric(precision=10, scale=6), nullable=True),
        # Valuation & Debt
        sa.Column('pe_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('category_pe_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('avg_maturity', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('avg_ytm', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('category_ytm', sa.Numeric(precision=10, scale=6), nullable=True),
        # Current NAV
        sa.Column('nav', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['scheme.id'], ),
        sa.PrimaryKeyConstraint('scheme_id', 'as_of_date')
    )

    # Create scheme_static table
    op.create_table(
        'scheme_static',
        sa.Column('scheme_id', sa.Integer(), nullable=False),
        sa.Column('benchmark_name', sa.String(length=200), nullable=True),
        sa.Column('fund_manager', sa.String(length=200), nullable=True),
        sa.Column('exit_load', sa.Text(), nullable=True),
        sa.Column('lock_in_period', sa.String(length=100), nullable=True),
        sa.Column('min_lumpsum', sa.Integer(), nullable=True),
        sa.Column('min_sip', sa.Integer(), nullable=True),
        sa.Column('sip_available', sa.Boolean(), nullable=True, default=True),
        sa.Column('base_expense_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('total_expense_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('sebi_risk_level', sa.Enum('Low', 'Low to Moderate', 'Moderate', 'Moderately High', 'High', 'Very High', name='sebirisklevel'), nullable=True),
        sa.Column('avg_maturity', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('avg_ytm', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['scheme.id'], ),
        sa.PrimaryKeyConstraint('scheme_id')
    )

    # Create scheme_manager table
    op.create_table(
        'scheme_manager',
        sa.Column('scheme_id', sa.Integer(), nullable=False),
        sa.Column('manager_name', sa.String(length=200), nullable=False),
        sa.Column('since_date', sa.Date(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['scheme.id'], ),
        sa.PrimaryKeyConstraint('scheme_id')
    )


def downgrade() -> None:
    op.drop_table('scheme_manager')
    op.drop_table('scheme_static')
    op.drop_table('fund_metrics')
    op.drop_table('risk_free_rate')
    op.drop_table('scheme_benchmark')
    op.drop_table('benchmark_tri_daily')
    op.drop_table('benchmark_index')
    op.drop_index('ix_nav_daily_scheme_date', table_name='nav_daily')
    op.drop_table('nav_daily')
    op.drop_index('ix_scheme_sebi_plan_option', table_name='scheme')
    op.drop_table('scheme')
    op.drop_table('amc')
    op.execute("DROP TYPE sebirisklevel")
    op.execute("DROP TYPE optiontype")
    op.execute("DROP TYPE plantype")