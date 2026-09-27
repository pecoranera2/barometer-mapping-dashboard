import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ---- shared palette (same as the R/ggplot2 deliverable) ----
COL_AVAILABLE = "#2a78d6"
COL_UNAVAILABLE = "#e1e0d9"
COL_INK = "#0b0b0b"
COL_INK2 = "#52514e"
COL_MUTED = "#6b6a63"
COL_SURFACE = "#fcfcfb"
CHUNK_TONES = ["#efe9d8", "#b8ab84"]
FONT_FAMILY = "Georgia, 'Times New Roman', Times, serif"

CLUSTER_ORDER = ["Socioeconomic", "Employment", "Access", "Gender and social norms", "Institutional"]

st.set_page_config(page_title="Cross-Barometer Variable Mapping", layout="wide")

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{
        font-family: {FONT_FAMILY};
    }}
    .block-container {{ padding-top: 2rem; }}
    h1, h2, h3 {{ font-family: {FONT_FAMILY}; color: {COL_INK}; }}
    .stCaption, .st-emotion-cache-1629p8f {{ font-family: {FONT_FAMILY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv(name):
    return pd.read_csv(os.path.join(DATA_DIR, name), dtype=str)


def ordered_variables(df, cluster_col="cluster"):
    """Contiguous cluster blocks (Socioeconomic first ... Institutional last),
    most-available variable at the top of each block."""
    d = df.copy()
    d["available_i"] = (d["available"] == "1").astype(int)
    cov = d.groupby([cluster_col, "variable"])["available_i"].sum().reset_index()
    cov["cluster_rank"] = cov[cluster_col].map({c: i for i, c in enumerate(CLUSTER_ORDER)})
    cov = cov.sort_values(["cluster_rank", "available_i"], ascending=[True, True])
    return cov["variable"].tolist()


def build_heatmap(df, x_col, x_order, cluster_col="cluster", code_col="code",
                   x_header_map=None, height=None):
    """A two-panel Plotly heatmap: a narrow cluster swatch column + the
    availability grid, sharing one categorical y-axis so rows line up."""
    var_order = ordered_variables(df, cluster_col)
    n_rows = len(var_order)
    if n_rows == 0:
        st.info("No variables match the current filter.")
        return None

    cluster_of = df.drop_duplicates("variable").set_index("variable")[cluster_col]
    cluster_idx = {c: i for i, c in enumerate(CLUSTER_ORDER)}
    tone_z = [cluster_idx.get(cluster_of[v], 0) % 2 for v in var_order]

    pivot_code = df.pivot_table(index="variable", columns=x_col, values=code_col, aggfunc="first")
    pivot_avail = df.pivot_table(index="variable", columns=x_col, values="available", aggfunc="first")
    pivot_code = pivot_code.reindex(index=var_order, columns=x_order)
    pivot_avail = pivot_avail.reindex(index=var_order, columns=x_order).fillna("0")
    z = pivot_avail.apply(lambda s: s.map({"1": 1, "0": 0})).values
    codes = pivot_code.fillna("").values

    x_labels = [x_header_map.get(c, c) if x_header_map else c for c in x_order]

    # Two separate x-axes (not one shared categorical axis) - Plotly's hover
    # lookup misaligns customdata when two Heatmap traces share one categorical
    # axis but occupy different category subsets, so each panel gets its own axis.
    fig = make_subplots(rows=1, cols=2, column_widths=[0.045, 0.955],
                         shared_yaxes=True, horizontal_spacing=0.006)

    # swatch column - cluster identity, no legend, hover shows the cluster name
    fig.add_trace(go.Heatmap(
        x=["Cluster"], y=var_order, z=[[t] for t in tone_z],
        colorscale=[[0, CHUNK_TONES[0]], [1, CHUNK_TONES[1]]], zmin=0, zmax=1,
        showscale=False, xgap=2, ygap=2,
        customdata=[[cluster_of[v]] for v in var_order],
        hovertemplate="%{customdata[0]}<extra></extra>",
    ), row=1, col=1)

    # main availability grid
    fig.add_trace(go.Heatmap(
        x=x_labels, y=var_order, z=z,
        colorscale=[[0, COL_UNAVAILABLE], [1, COL_AVAILABLE]], zmin=0, zmax=1,
        showscale=False, xgap=2, ygap=2,
        customdata=codes,
        hovertemplate="<b>%{y}</b><br>%{x}<br>code: %{customdata}<extra></extra>",
    ), row=1, col=2)

    # manual legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                              marker=dict(size=12, color=COL_AVAILABLE, symbol="square"),
                              name="Available"), row=1, col=2)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                              marker=dict(size=12, color=COL_UNAVAILABLE, symbol="square"),
                              name="Not available"), row=1, col=2)

    # cluster block separators - full width (paper x), aligned to the shared y-axis
    shapes = []
    boundary = 0
    for c in CLUSTER_ORDER:
        n_in_cluster = sum(1 for v in var_order if cluster_of[v] == c)
        if n_in_cluster == 0:
            continue
        boundary += n_in_cluster
        if boundary < n_rows:
            shapes.append(dict(
                type="line", xref="paper", x0=0, x1=1,
                yref="y", y0=boundary - 0.5, y1=boundary - 0.5,
                line=dict(color=COL_SURFACE, width=3),
            ))

    fig.update_yaxes(autorange="reversed", showgrid=False, zeroline=False,
                      tickfont=dict(size=12), row=1, col=1)
    fig.update_yaxes(autorange="reversed", showgrid=False, zeroline=False,
                      showticklabels=False, row=1, col=2)
    fig.update_xaxes(side="top", showgrid=False, zeroline=False, showticklabels=False,
                      type="category", row=1, col=1)
    fig.update_xaxes(side="top", showgrid=False, zeroline=False, tickfont=dict(size=13),
                      tickangle=-25, type="category", categoryorder="array",
                      categoryarray=x_labels, row=1, col=2)

    fig.update_layout(
        height=height or max(420, 26 * n_rows + 160),
        margin=dict(l=10, r=10, t=90, b=40),
        font=dict(family=FONT_FAMILY, color=COL_INK, size=13),
        plot_bgcolor=COL_SURFACE, paper_bgcolor=COL_SURFACE,
        shapes=shapes,
        legend=dict(orientation="h", yanchor="top", y=-0.01, xanchor="left", x=0,
                    font=dict(size=13)),
    )
    return fig


def filter_controls(df, key_prefix):
    clusters = [c for c in CLUSTER_ORDER if c in df["cluster"].unique()]
    col1, col2 = st.columns([2, 3])
    with col1:
        chosen = st.multiselect("Filter by cluster", clusters, default=clusters, key=f"{key_prefix}_cluster")
    with col2:
        search = st.text_input("Search variable name", key=f"{key_prefix}_search")
    d = df[df["cluster"].isin(chosen)]
    if search:
        d = d[d["variable"].str.contains(search, case=False, na=False)]
    return d


def region_page(csv_file, title, subtitle, source_note, x_order, key_prefix):
    st.header(title)
    st.caption(subtitle)
    df = load_csv(csv_file)
    df = filter_controls(df, key_prefix)
    fig = build_heatmap(df, x_col="period" if "period" in df.columns else "year", x_order=x_order, cluster_col="cluster")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    st.caption(source_note)


def overview_page():
    st.title("Cross-Barometer Variable Mapping")
    st.markdown(
        """
This dashboard shows which variables are comparable across five cross-national
public-opinion barometers - **Arab Barometer**, **Latinobarómetro**,
**Afrobarometer**, **Asian Barometer**, and **Eurobarometer** (Special
Eurobarometer thematic modules) - and across time.

**How to read the charts:**
- Each colored tile shows whether a variable was asked, in a comparable form,
  in a given survey/wave or period. **Blue = available. Gray = not available.**
  Hover any tile for the exact variable code used in that survey.
- Variables are grouped into five concept clusters (shown as a colored strip
  on the left of each chart): **Socioeconomic**, **Employment**, **Access**,
  **Gender and social norms**, and **Institutional**.
- Use the cluster filter and search box on each page to narrow the view.

**Pages:**
- **Latest round** - a snapshot of what's available in the most recent wave of
  each of the five barometers, side by side.
- **Eurobarometer / Asian Barometer / Arab Barometer / Latinobarómetro /
  Afrobarometer** - coverage over time for that survey, by cluster and
  wave/period.

Eurobarometer and Asian Barometer were independently checked against the raw
survey data files; Arab Barometer, Latinobarómetro, and Afrobarometer were
mapped separately and are shown as provided.
        """
    )


PAGES = {
    "Overview": overview_page,
}

st.sidebar.title("Navigate")
page = st.sidebar.radio("", list(PAGES.keys()) + [
    "Latest round", "Eurobarometer", "Asian Barometer", "Arab Barometer",
    "Latinobarometro", "Afrobarometer",
], label_visibility="collapsed")

if page == "Overview":
    overview_page()

elif page == "Latest round":
    st.header("What's available in the latest round?")
    st.caption("51 variables x 5 barometers, most recent wave per survey")
    counts = load_csv("latest_round_counts.csv")
    detail = "  ·  ".join(f"{r.barometer} ({r.n_countries} countries)" for r in counts.itertuples())
    st.caption(detail)
    df = load_csv("latest_round.csv").rename(columns={"chunk": "cluster"})
    df = filter_controls(df, "latest")
    bar_order = load_csv("latest_round_counts.csv")["barometer"].tolist()
    short = {
        "Arab Barometer 2024": "Arab Barometer", "Latinobarometer 2024": "Latinobarometro",
        "Afro Barometer 2023": "Afrobarometer", "Asian Barometer 2023": "Asian Barometer",
        "Eurobarometer 2025 (Standard)": "Eurobarometer",
    }
    fig = build_heatmap(df, x_col="barometer", x_order=bar_order, x_header_map=short, height=1250)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Source: Map of Variables 09 04 2026.xlsx - 'Latest round' tab. Blank/gray = variable not "
        "coded (or not comparable) in that survey's latest round. Shading groups variables into the "
        "mapping's 5 concept clusters; a handful of variables outside those clusters were classified "
        "by concept for this grouping only."
    )

elif page == "Eurobarometer":
    region_page(
        "euro_clusters.csv",
        "Eurobarometer: coverage by cluster and wave",
        "Special Eurobarometer modules, 2015-2024 (Discrimination 2015/2019/2023, Gender Equality "
        "2017, Gender Stereotypes 2024) - not the Standard EB trend series.",
        "Source: Map of Variables 09 04 2026.xlsx - 'EURO CLUSTERS' tab.",
        ["2015", "2017", "2019", "2023", "2024"],
        "euro",
    )

elif page == "Asian Barometer":
    region_page(
        "ab_clusters.csv",
        "Asian Barometer: coverage by cluster and wave",
        "ABS waves 3-6, 2012-2023.",
        "Source: Map of Variables 09 04 2026.xlsx - 'AB CLUSTERS' tab (W3 2010-12, W4 2014-16, "
        "W5 2018-21, W6 2021-23).",
        ["2012", "2016", "2021", "2023"],
        "asian",
    )

elif page == "Arab Barometer":
    region_page(
        "arab_clusters.csv",
        "Arab Barometer: coverage by cluster and period",
        "Waves pooled into 4-year periods.",
        "Source: Map of Variables 09 04 2026.xlsx - 'Clusters ARAB' tab. Columns are 4-year period "
        "buckets, not individual waves.",
        ["2012-2016", "2016-2019", "2020-2022", "2023-2025"],
        "arab",
    )

elif page == "Latinobarometro":
    region_page(
        "latino_clusters.csv",
        "Latinobarometro: coverage by cluster and period",
        "Waves pooled into 4-year periods.",
        "Source: Map of Variables 09 04 2026.xlsx - 'Clusters LATINO' tab. Columns are 4-year period "
        "buckets, not individual waves.",
        ["2012-2016", "2016-2019", "2020-2022", "2023-2025"],
        "latino",
    )

elif page == "Afrobarometer":
    region_page(
        "afro_clusters.csv",
        "Afrobarometer: coverage by cluster and period",
        "Rounds pooled into 4-year periods.",
        "Source: Map of Variables 09 04 2026.xlsx - 'Clusters AFRO' tab. Columns are 4-year period "
        "buckets, not individual waves.",
        ["2012-2016", "2016-2019", "2020-2022", "2023-2025"],
        "afro",
    )
