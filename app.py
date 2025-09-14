import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page config
st.set_page_config(page_title="E-commerce Insights", layout="wide")
st.title("E-commerce Insights Dashboard")

# -------------------------------
# Generate synthetic data
# -------------------------------
@st.cache_data(persist=True, ttl=3600)
def generate_data(n=30000, seed=42):
    np.random.seed(seed)
    users = np.random.randint(1,2000, n)
    dates = pd.date_range('2024-01-01','2024-12-31')
    df = pd.DataFrame({
        'event_id': np.arange(n),
        'user_id': users,
        'date': np.random.choice(dates, n),
        'event': np.random.choice(['view','add_to_cart','purchase'], n, p=[0.6,0.25,0.15]),
        'price': np.round(np.random.uniform(5,300, n), 2)
    })
    df['month'] = df['date'].dt.to_period('M').astype(str)
    return df

df = generate_data()

# -------------------------------
# Sidebar filters
# -------------------------------
with st.sidebar:
    st.header("Filters")
    events = st.multiselect("Events", df['event'].unique(), default=df['event'].unique())
    date_range = st.date_input("Date range", [df['date'].min(), df['date'].max()])
    if len(date_range) != 2:
        st.error("Please select start and end date")

# -------------------------------
# Filter data
# -------------------------------
mask = (
    (df['event'].isin(events)) &
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1]))
)
view = df[mask]

# -------------------------------
# Event Funnel + Conversion Rates
# -------------------------------
funnel = view.groupby('event', as_index=False).agg(count=('event','count'))
funnel_order = ['view','add_to_cart','purchase']
# Add conversion rates
unique_views = view[view['event']=='view']['user_id'].nunique()
unique_adds = view[view['event']=='add_to_cart']['user_id'].nunique()
unique_purchases = view[view['event']=='purchase']['user_id'].nunique()
conv_view_to_add = unique_adds / unique_views if unique_views else 0
conv_add_to_purchase = unique_purchases / unique_adds if unique_adds else 0

fig1 = px.bar(
    funnel, x='event', y='count',
    category_orders={'event': funnel_order},
    title='Event Funnel (views -> add_to_cart -> purchase)',
    hover_data={'count': True},
    text='count'
)
fig1.update_traces(texttemplate='%{text}', textposition='outside')
st.markdown("## Event Funnel")
st.plotly_chart(fig1, use_container_width=True)

# -------------------------------
# Metrics + AOV + Conversion Rates
# -------------------------------
views = unique_views
adds = unique_adds
purchases = unique_purchases
cart_abandonment_rate = 1 - conv_add_to_purchase
avg_order_value = view[view['event']=='purchase']['price'].mean() if purchases else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Unique Viewers", views)
col2.metric("Added to Cart", adds)
col3.metric("Purchasers", purchases)
col4.metric("Cart Abandonment Rate", f"{cart_abandonment_rate:.2%}")
col5.metric("Average Order Value", f"${avg_order_value:.2f}")

st.markdown(f"**Conversion Rate (View → Add to Cart):** {conv_view_to_add:.2%}  |  "
            f"**Conversion Rate (Add to Cart → Purchase):** {conv_add_to_purchase:.2%}")

# -------------------------------
# Monthly Purchase Trend
# -------------------------------
monthly = view[view['event']=='purchase'].groupby('month', as_index=False).agg(purchases=('event','count'),
                                                                             revenue=('price','sum'))
monthly['month'] = pd.to_datetime(monthly['month'])
monthly = monthly.sort_values('month')
fig2 = px.line(monthly, x='month', y='purchases', title='Monthly Purchases', markers=True, hover_data=['revenue'])
st.markdown("## Monthly Purchase Trend")
st.plotly_chart(fig2, use_container_width=True)

# -------------------------------
# Sample data + download
# -------------------------------
st.markdown("### Sample Filtered Data")
st.dataframe(view.head(10))
st.download_button("Download Filtered Data as CSV", view.to_csv(index=False), "ecommerce_data.csv")
