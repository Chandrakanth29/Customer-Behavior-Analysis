# -*- coding: utf-8 -*-
"""
Customer Behavior Analysis Using Python
========================================

Explores customer behavior using the Online Retail dataset (Kaggle),
containing transactions from a UK-based online retail store.

The analysis covers:
    - Summary statistics (numeric and categorical)
    - Transaction value distribution
    - Customer distribution by country
    - Quantity vs. unit price relationship
    - Customer Lifetime Value (CLV) segmentation
    - Customer conversion funnel
    - Churn rate estimation (6-month inactivity)

Run with:
    python customer_behavior_analysis_using_python.py
"""

import os
import pandas as pd
import plotly.express as px

IMAGES_DIR = "images"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_data(path="data.csv", encoding="ISO-8859-1"):
    """
    Load the Online Retail dataset.

    Uses a relative path, so this works on any machine as long as
    data.csv sits in the same folder as this script (see README for
    where to download it -- the raw file isn't committed to the repo).
    """
    try:
        return pd.read_csv(path, encoding=encoding)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Could not find '{path}'. This project does not include the raw "
            f"dataset -- see the Dataset section in README.md for the download "
            f"link, then place the file in the project root as '{path}'."
        ) from e


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
def print_summary_statistics(data):
    """Print summary statistics for numeric and categorical columns."""
    print("Numeric summary:")
    print(data.describe())
    print("\nCategorical summary:")
    print(data.describe(include='object'))


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def add_total_price(data):
    """Add a TotalPrice column: Quantity x UnitPrice."""
    data['TotalPrice'] = data['Quantity'] * data['UnitPrice']
    return data


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------
def plot_total_price_distribution(data, images_dir=IMAGES_DIR):
    """Histogram of transaction total prices."""
    fig = px.histogram(data, x='TotalPrice', nbins=50,
                       title='Distribution of Transaction Total Prices')
    fig.update_layout(xaxis_title='Total Price (\u00a3)', yaxis_title='Number of Transactions',
                      width=1000, height=350)
    fig.write_image(os.path.join(images_dir, "total_price_distribution.png"))
    fig.show()
    return fig


def plot_country_distribution(data, images_dir=IMAGES_DIR):
    """Bar chart of customer/transaction counts by country."""
    country_counts = data['Country'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Count']
    fig = px.bar(country_counts, x='Country', y='Count', title='Customer Distribution by Country')
    fig.update_layout(width=1000, height=350)
    fig.write_image(os.path.join(images_dir, "customer_distribution_by_country.png"))
    fig.show()
    return fig


def plot_quantity_vs_unit_price(data, images_dir=IMAGES_DIR):
    """Scatter plot of quantity vs. unit price, with an OLS trendline."""
    fig = px.scatter(data, x='Quantity', y='UnitPrice',
                     title='Quantity vs. Unit Price', trendline='ols')
    fig.update_layout(width=1000, height=350)
    fig.write_image(os.path.join(images_dir, "quantity_vs_unit_price.png"))
    fig.show()
    return fig


def plot_avg_quantity_by_country(data, images_dir=IMAGES_DIR, top_n=10):
    """Bar chart of the top N countries by average quantity purchased."""
    country_grouped = data.groupby('Country')['Quantity'].mean().reset_index()
    country_grouped.columns = ['Country', 'Average_Quantity']
    top_countries = country_grouped.sort_values(by='Average_Quantity', ascending=False).head(top_n)
    fig = px.bar(top_countries, x='Country', y='Average_Quantity',
                 title=f'Top {top_n} Countries by Average Quantity Purchased')
    fig.write_image(os.path.join(images_dir, "avg_quantity_by_country.png"))
    fig.show()
    return fig


# ---------------------------------------------------------------------------
# Customer Lifetime Value (CLV) segmentation
# ---------------------------------------------------------------------------
def segment_customers_by_clv(data):
    """
    Calculate CLV per customer (sum of TotalPrice) and bucket customers
    into Low / Medium / High value segments.

    Note: customers with a CLV of 0 or below (common in this dataset due
    to returns/cancellations) fall outside all three bins and are
    excluded from the segment counts -- see README known limitations.
    """
    clv = data.groupby('CustomerID')['TotalPrice'].sum().reset_index()
    clv.columns = ['CustomerID', 'CLV']
    clv['Segment'] = pd.cut(clv['CLV'], bins=[0, 100, 500, float('inf')],
                            labels=['Low Value', 'Medium Value', 'High Value'])
    return clv


def plot_clv_segments(clv, images_dir=IMAGES_DIR):
    """Bar chart of customer counts per CLV segment."""
    segment_counts = clv['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    fig = px.bar(segment_counts, x='Segment', y='Count', title='Customer Segmentation by CLV')
    fig.update_xaxes(title='Segment')
    fig.update_yaxes(title='Number of Customers')
    fig.update_layout(width=1000, height=350)
    fig.write_image(os.path.join(images_dir, "clv_segments.png"))
    fig.show()
    return fig


# ---------------------------------------------------------------------------
# Conversion funnel
# ---------------------------------------------------------------------------
def build_conversion_funnel(data):
    """Build a simple funnel: unique customers -> transactions -> quantity."""
    num_customers = data['CustomerID'].nunique()
    num_transactions = data['InvoiceNo'].nunique()
    total_quantity = data['Quantity'].sum()

    funnel_df = pd.DataFrame({
        'stage': ['Unique Customers', 'Unique Transactions', 'Total Quantity Purchased'],
        'count': [num_customers, num_transactions, total_quantity]
    })
    return funnel_df


def plot_conversion_funnel(funnel_df, images_dir=IMAGES_DIR):
    """Funnel chart visualizing the conversion stages."""
    fig = px.funnel(funnel_df, x='count', y='stage', title='Customer Conversion Funnel')
    fig.update_layout(width=1000, height=350)
    fig.write_image(os.path.join(images_dir, "conversion_funnel.png"))
    fig.show()
    return fig


# ---------------------------------------------------------------------------
# Churn rate
# ---------------------------------------------------------------------------
def calculate_churn_rate(data, inactivity_months=6):
    """
    Estimate churn rate: the share of customers whose most recent
    purchase is older than `inactivity_months` before the dataset's
    latest transaction date.

    Note: groupby('CustomerID') drops rows with a missing CustomerID by
    default, so this rate is calculated only across identified
    customers -- see README known limitations.
    """
    data['InvoiceDate'] = pd.to_datetime(data['InvoiceDate'])
    cutoff_date = data['InvoiceDate'].max() - pd.DateOffset(months=inactivity_months)

    last_purchase = data.groupby('CustomerID')['InvoiceDate'].max().reset_index()
    last_purchase['Churned'] = last_purchase['InvoiceDate'] < cutoff_date

    churn_rate = last_purchase['Churned'].mean()
    return churn_rate


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    data = load_data()
    print(data.head())

    print_summary_statistics(data)

    data = add_total_price(data)

    plot_total_price_distribution(data)
    plot_country_distribution(data)
    plot_quantity_vs_unit_price(data)
    plot_avg_quantity_by_country(data)

    clv = segment_customers_by_clv(data)
    plot_clv_segments(clv)

    funnel_df = build_conversion_funnel(data)
    plot_conversion_funnel(funnel_df)

    churn_rate = calculate_churn_rate(data)
    print(f"Churn Rate: {churn_rate:.2%}")


if __name__ == "__main__":
    main()
