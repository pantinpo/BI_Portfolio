from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
RAW_PATH = BASE_DIR / "data" / "raw" / "sales_raw.csv"
CLEAN_PATH = BASE_DIR / "data" / "processed" / "sales_clean.csv"

CATEGORICAL_COLUMNS = [
    "Customer Type", "Country", "Region", "State", "City", "Channel",
    "Traffic Source", "Payment Method", "Category", "Sub-Category",
    "Product", "Promotion", "Order Status",
]
MONEY_COLUMNS = ["Unit Price", "Gross Sales", "Discount Amount", "Net Sales", "Cost", "Profit"]
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y"]

CHANNEL_ALIASES = {"web": "Website", "app": "Mobile App"}
STATUS_ALIASES = {"canceled": "Cancelled"}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def remove_test_orders(df):
    is_test = (
        df["Customer ID"].str.upper().str.startswith("TEST")
        | df["Order ID"].str.upper().str.contains("TEST")
        | (pd.to_numeric(df["Quantity"], errors="coerce") <= 0)
    )
    return df[~is_test]


def remove_duplicates(df):
    return df.drop_duplicates().drop_duplicates(subset=["Order ID", "Line Item"])


def apply_aliases(series, aliases):
    return series.str.lower().map(aliases).fillna(series)


def unify_casing(series):
    # "WEBSITE" / "website" -> whichever spelling appears most often
    lower = series.str.lower()
    most_common = series.groupby(lower).agg(lambda values: values.value_counts().index[0])
    return lower.map(most_common)


def standardize_text(df):
    df = df.apply(lambda col: col.str.strip())
    df["Channel"] = apply_aliases(df["Channel"], CHANNEL_ALIASES)
    df["Order Status"] = apply_aliases(df["Order Status"], STATUS_ALIASES)
    for col in CATEGORICAL_COLUMNS:
        df[col] = unify_casing(df[col])
    df["State"] = df["State"].str.upper().map(STATE_NAMES).fillna(df["State"])
    return df


def parse_dates(df):
    df = df.copy()
    parsed = pd.Series(pd.NaT, index=df.index)
    for fmt in DATE_FORMATS:
        parsed = parsed.fillna(pd.to_datetime(df["Order Date"], format=fmt, errors="coerce"))
    if parsed.isna().any():
        raise ValueError(f"Unrecognized dates: {df.loc[parsed.isna(), 'Order Date'].unique()[:5]}")
    df["Order Date"] = parsed
    return df


def parse_numbers(df):
    df = df.copy()
    for col in MONEY_COLUMNS:
        df[col] = pd.to_numeric(df[col].str.replace(r"[$,]", "", regex=True))

    is_percent = df["Discount %"].str.endswith("%")
    df["Discount %"] = pd.to_numeric(df["Discount %"].str.rstrip("%"))
    df.loc[is_percent, "Discount %"] /= 100

    df["Line Item"] = df["Line Item"].astype(int)
    df["Quantity"] = df["Quantity"].astype(int)
    return df


def fill_missing(df):
    df = df.copy()

    # customers ship to the same city, so fill from their other orders
    known_city = df.dropna(subset=["City"]).groupby("Customer ID")["City"].first()
    df["City"] = df["City"].fillna(df["Customer ID"].map(known_city)).fillna("Unknown")

    df["Traffic Source"] = df["Traffic Source"].fillna("Unknown")
    df["Payment Method"] = df["Payment Method"].fillna("Unknown")

    df["Net Sales"] = df["Net Sales"].fillna(df["Gross Sales"] - df["Discount Amount"])
    df["Profit"] = df["Profit"].fillna(df["Net Sales"] - df["Cost"])
    df[MONEY_COLUMNS] = df[MONEY_COLUMNS].round(2)
    return df


def validate(df):
    assert not df.duplicated(subset=["Order ID", "Line Item"]).any(), "duplicate order lines"
    assert df.notna().all().all(), f"nulls in {df.columns[df.isna().any()].tolist()}"
    assert (df["Quantity"] > 0).all(), "non-positive quantity"
    assert df["Discount %"].between(0, 1).all(), "discount out of range"
    assert ((df["Gross Sales"] - df["Discount Amount"] - df["Net Sales"]).abs() < 0.01).all(), "net sales mismatch"
    assert set(df["State"]).issubset(STATE_NAMES.values()), "unknown state"


def main():
    # only blank cells are nulls; otherwise pandas reads the "None" promotion as null
    df = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False, na_values=[""])
    print(f"Raw rows:   {len(df):,}")

    df = remove_test_orders(df)
    df = remove_duplicates(df)
    df = standardize_text(df)
    df = parse_dates(df)
    df = parse_numbers(df)
    df = fill_missing(df)
    validate(df)

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(["Order Date", "Order ID", "Line Item"]).to_csv(CLEAN_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Clean rows: {len(df):,}")


if __name__ == "__main__":
    main()
