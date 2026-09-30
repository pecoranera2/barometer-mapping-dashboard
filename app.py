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
COL_LAND = "#eeede8"
CHUNK_TONES = ["#efe9d8", "#b8ab84"]
FONT_FAMILY = "Georgia, 'Times New Roman', Times, serif"

CLUSTER_ORDER = ["Socioeconomic", "Employment", "Access", "Gender and social norms", "Institutional"]

# one identity colour per barometer (Okabe-Ito based; distinct from the blue/gray availability tiles)
BAROMETERS = ["Arab Barometer", "Latinobarometro", "Afrobarometer", "Asian Barometer", "Eurobarometer"]
BAR_COLOR = {
    "Arab Barometer": "#d55e00",
    "Latinobarometro": "#009e73",
    "Afrobarometer": "#e69f00",
    "Asian Barometer": "#cc79a7",
    "Eurobarometer": "#5b5ea6",
}
SHARED_COLOR = "#3d3d3a"
BAR_LABEL = {"Latinobarometro": "Latinobarómetro"}
LATEST_SHORT = {
    "Arab Barometer 2024": "Arab Barometer", "Latinobarometer 2024": "Latinobarometro",
    "Afro Barometer 2023": "Afrobarometer", "Asian Barometer 2023": "Asian Barometer",
    "Eurobarometer 2025 (Standard)": "Eurobarometer",
}
# source file + period columns per barometer (cluster pages)
BAR_PAGES = {
    "Arab Barometer": ("arab_clusters.csv", ["2012-2016", "2016-2019", "2020-2022", "2023-2025"],
                       "Waves pooled into 4-year periods.",
                       "Source: Map of Variables 09 04 2026.xlsx - 'Clusters ARAB' tab. Columns are 4-year period buckets, not individual waves."),
    "Latinobarometro": ("latino_clusters.csv", ["2012-2016", "2016-2019", "2020-2022", "2023-2025"],
                        "Waves pooled into 4-year periods.",
                        "Source: Map of Variables 09 04 2026.xlsx - 'Clusters LATINO' tab. Columns are 4-year period buckets, not individual waves."),
    "Afrobarometer": ("afro_clusters.csv", ["2012-2016", "2016-2019", "2020-2022", "2023-2025"],
                      "Rounds pooled into 4-year periods.",
                      "Source: Map of Variables 09 04 2026.xlsx - 'Clusters AFRO' tab. Columns are 4-year period buckets, not individual waves."),
    "Asian Barometer": ("ab_clusters.csv", ["2012", "2016", "2021", "2023"],
                        "ABS waves 3-6, 2012-2023.",
                        "Source: Map of Variables 09 04 2026.xlsx - 'AB CLUSTERS' tab (W3 2010-12, W4 2014-16, W5 2018-21, W6 2021-23)."),
    "Eurobarometer": ("euro_clusters.csv", ["2015", "2017", "2019", "2023", "2024"],
                      "Special Eurobarometer modules, 2015-2024 (Discrimination 2015/2019/2023, Gender Equality "
                      "2017, Gender Stereotypes 2024) - not the Standard EB trend series.",
                      "Source: Map of Variables 09 04 2026.xlsx - 'EURO CLUSTERS' tab."),
}

st.set_page_config(page_title="Cross-Barometer Variable Mapping", layout="wide")

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{ font-family: {FONT_FAMILY}; }}
    .block-container {{ padding-top: 2rem; }}
    h1, h2, h3 {{ font-family: {FONT_FAMILY}; color: {COL_INK}; }}
    .lede {{ color: {COL_INK2}; font-size: 1.08rem; margin: -0.4rem 0 0.8rem 0; }}
    .legend-dot {{ display:inline-block; width:0.8em; height:0.8em; margin-right:0.35em; border-radius:2px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv(name):
    return pd.read_csv(os.path.join(DATA_DIR, name), dtype=str)


@st.cache_data
def load_countries():
    return pd.read_csv(os.path.join(DATA_DIR, "countries.csv"), dtype={"latest": int})


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

    fig.add_trace(go.Heatmap(
        x=["Cluster"], y=var_order, z=[[t] for t in tone_z],
        colorscale=[[0, CHUNK_TONES[0]], [1, CHUNK_TONES[1]]], zmin=0, zmax=1,
        showscale=False, xgap=2, ygap=2,
        customdata=[[cluster_of[v]] for v in var_order],
        hovertemplate="%{customdata[0]}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Heatmap(
        x=x_labels, y=var_order, z=z,
        colorscale=[[0, COL_UNAVAILABLE], [1, COL_AVAILABLE]], zmin=0, zmax=1,
        showscale=False, xgap=2, ygap=2,
        customdata=codes,
        hovertemplate="<b>%{y}</b><br>%{x}<br>code: %{customdata}<extra></extra>",
    ), row=1, col=2)

    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(size=12, color=COL_AVAILABLE, symbol="square"),
                             name="Available"), row=1, col=2)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             marker=dict(size=12, color=COL_UNAVAILABLE, symbol="square"),
                             name="Not available"), row=1, col=2)

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
        height=height or max(300, 30 * n_rows + 170),
        margin=dict(l=10, r=10, t=90, b=40),
        font=dict(family=FONT_FAMILY, color=COL_INK, size=13),
        plot_bgcolor=COL_SURFACE, paper_bgcolor=COL_SURFACE,
        shapes=shapes,
        legend=dict(orientation="h", yanchor="top", y=-0.01, xanchor="left", x=0,
                    font=dict(size=13)),
    )
    return fig


def cluster_pills(df, key):
    """Buttons for each cluster present in df; returns the filtered frame."""
    clusters = [c for c in CLUSTER_ORDER if c in df["cluster"].unique()]
    choice = st.pills("Cluster", ["All"] + clusters, default="All", key=key,
                      label_visibility="collapsed")
    if choice in (None, "All"):
        return df, "All"
    return df[df["cluster"] == choice], choice


# ------------------------------------------------------------------ map helpers
def _fade(hex_color, amount=0.6):
    """Blend a colour toward the page surface (used for barometers that are not selected)."""
    c = hex_color.lstrip("#")
    s = COL_SURFACE.lstrip("#")
    mix = [round(int(c[i:i + 2], 16) * (1 - amount) + int(s[i:i + 2], 16) * amount) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(mix)


def base_geo(fig, height):
    fig.update_geos(
        projection_type="natural earth", showframe=False, showcoastlines=False,
        showland=True, landcolor=COL_LAND, showcountries=True, countrycolor="#d8d7d0",
        showocean=False, bgcolor=COL_SURFACE, lataxis_range=[-58, 82],
    )
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=COL_SURFACE, font=dict(family=FONT_FAMILY, color=COL_INK, size=13),
        legend=dict(orientation="h", yanchor="top", y=0.02, xanchor="left", x=0.0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=13)),
        clickmode="event+select", dragmode=False,
    )


def overview_map(cdf, selected):
    """World map of the countries covered in each barometer's latest round.
    selected = 'All' or a barometer name (others fade)."""
    latest = cdf[cdf["latest"] == 1]
    by_country = {}
    for r in latest.itertuples():
        by_country.setdefault((r.iso3, r.country), []).append((r.barometer, r.round, r.year))

    groups = {}  # (name, colour) -> dict(iso, text)
    for (iso, country), items in by_country.items():
        names = [b for b, _, _ in items]
        if selected != "All" and selected in names:
            key = (BAR_LABEL.get(selected, selected), BAR_COLOR[selected])
        elif selected != "All":
            b = names[0]
            key = (BAR_LABEL.get(b, b) + " (not selected)", _fade(BAR_COLOR[b]))
        elif len(names) == 1:
            key = (BAR_LABEL.get(names[0], names[0]), BAR_COLOR[names[0]])
        else:
            key = ("In two barometers", SHARED_COLOR)
        hover = f"<b>{country}</b><br>" + "<br>".join(
            f"{BAR_LABEL.get(b, b)}: {rnd} ({yr})" for b, rnd, yr in items)
        groups.setdefault(key, {"iso": [], "text": [], "custom": []})
        groups[key]["iso"].append(iso)
        groups[key]["text"].append(hover)
        groups[key]["custom"].append([names[0] if selected == "All" or selected not in names else selected,
                                      len(names)])

    fig = go.Figure()
    order = [BAR_LABEL.get(b, b) for b in BAROMETERS] + ["In two barometers"]
    for key in sorted(groups, key=lambda k: (order.index(k[0]) if k[0] in order else 99, k[0])):
        name, colour = key
        g = groups[key]
        fig.add_trace(go.Choropleth(
            locations=g["iso"], z=[1] * len(g["iso"]), locationmode="ISO-3",
            colorscale=[[0, colour], [1, colour]], showscale=False, zmin=0, zmax=1,
            marker_line_color=COL_SURFACE, marker_line_width=0.6,
            text=g["text"], hovertemplate="%{text}<extra></extra>", customdata=g["custom"],
            name=name, showlegend=True,
            selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
        ))
    base_geo(fig, 520)
    return fig


def round_map(cdf_round, colour, height=430):
    fig = go.Figure(go.Choropleth(
        locations=cdf_round["iso3"], z=[1] * len(cdf_round), locationmode="ISO-3",
        colorscale=[[0, colour], [1, colour]], showscale=False, zmin=0, zmax=1,
        marker_line_color=COL_SURFACE, marker_line_width=0.6,
        text=cdf_round["country"], hovertemplate="<b>%{text}</b><extra></extra>",
    ))
    base_geo(fig, height)
    fig.update_geos(fitbounds="locations", lataxis_range=None)
    fig.update_layout(showlegend=False)
    return fig


# ------------------------------------------------------------------ pages
def overview_page():
    cdf = load_countries()
    st.title("Cross-Barometer Variable Mapping")
    st.markdown('<p class="lede">Which variables can be compared across five public-opinion '
                'barometers - and across which countries and years?</p>', unsafe_allow_html=True)

    options = ["All"] + BAROMETERS
    st.session_state.setdefault("map_pick", "All")
    if "goto_bar_map" in st.session_state:
        st.session_state["map_pick"] = st.session_state.pop("goto_bar_map")
    top = st.columns([3, 1.2])
    with top[0]:
        st.caption("Countries in each barometer's latest round. Pick a barometer to highlight it, or click a country.")
        pick = st.pills("Barometer", options, key="map_pick",
                        format_func=lambda b: BAR_LABEL.get(b, b), label_visibility="collapsed")
    selected = pick or "All"

    event = st.plotly_chart(overview_map(cdf, selected), use_container_width=True,
                            on_select="rerun", selection_mode="points", key="overview_map",
                            config={"displayModeBar": False, "scrollZoom": False})
    # click on a country -> highlight its barometer (first one if the country is in two)
    pts = event.selection.get("points", []) if event and event.selection else []
    if pts:
        cd = pts[0].get("customdata")
        if cd and cd[0] in BAROMETERS and cd[0] != selected:
            st.session_state["goto_bar_map"] = cd[0]
            st.rerun()

    if selected != "All":
        latest = cdf[(cdf["latest"] == 1) & (cdf["barometer"] == selected)]
        rnd = latest.iloc[0]
        c1, c2 = st.columns([3, 1.3])
        with c1:
            st.markdown(f"**{BAR_LABEL.get(selected, selected)}** - latest round: {rnd['round']} ({rnd['year']}), "
                        f"**{len(latest)} countries**.")
            st.caption(", ".join(sorted(latest["country"].unique())))
        with c2:
            if st.button(f"Explore {BAR_LABEL.get(selected, selected)} variables →", use_container_width=True):
                st.session_state["goto_bar_page"] = selected
                st.switch_page(PAGE_BAROMETER)

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("About")
        st.markdown(
            """
This dashboard shows which variables are comparable across five cross-national
public-opinion barometers - **Arab Barometer**, **Latinobarómetro**,
**Afrobarometer**, **Asian Barometer**, and **Eurobarometer** (Special
Eurobarometer thematic modules) - and across time.

- **Latest round** - what is available in the most recent wave of each
  barometer, side by side, one concept cluster at a time.
- **Barometer** - coverage over time for one survey, by cluster and
  wave/period, plus the countries included in each round.

Eurobarometer and Asian Barometer were independently checked against the raw
survey data files; Arab Barometer, Latinobarómetro, and Afrobarometer were
mapped separately and are shown as provided.
            """
        )
    with right:
        st.subheader("How to read the charts")
        st.markdown(
            f"""
- Each tile shows whether a variable was asked, in a comparable form, in a
  given survey/wave or period.
  <span class="legend-dot" style="background:{COL_AVAILABLE}"></span>**Blue = available.**
  <span class="legend-dot" style="background:{COL_UNAVAILABLE}"></span>**Gray = not available.**
  Hover any tile for the exact variable code used in that survey.
- Variables are grouped into five concept clusters (the colored strip on the
  left of each chart): **Socioeconomic**, **Employment**, **Access**,
  **Gender and social norms**, and **Institutional**.
- Use the **cluster buttons** on each page to look at one cluster at a time.
- On the map, each barometer has its own color; countries covered by two
  barometers are shown in dark gray.
            """,
            unsafe_allow_html=True,
        )


def latest_page():
    cdf = load_countries()
    st.header("What's available in the latest round?")
    df_all = load_csv("latest_round.csv").rename(columns={"chunk": "cluster"})
    df, choice = cluster_pills(df_all, "latest_cluster")
    n_vars = df["variable"].nunique()
    st.caption(f"{n_vars} variables x 5 barometers, most recent wave per survey")

    latest = cdf[cdf["latest"] == 1].groupby("barometer")["country"].nunique()
    bar_order = load_csv("latest_round_counts.csv")["barometer"].tolist()
    detail = "  ·  ".join(f"{BAR_LABEL.get(LATEST_SHORT[b], LATEST_SHORT[b])} ({latest[LATEST_SHORT[b]]} countries)"
                          for b in bar_order)
    st.caption(detail)

    # coverage summary for the selected cluster
    avail = df.assign(a=(df["available"] == "1").astype(int)).groupby("barometer")["a"].sum()
    cols = st.columns(5)
    for col, b in zip(cols, bar_order):
        col.metric(BAR_LABEL.get(LATEST_SHORT[b], LATEST_SHORT[b]), f"{int(avail.get(b, 0))} of {n_vars}",
                   help="Variables available in this barometer's latest round")

    fig = build_heatmap(df, x_col="barometer", x_order=bar_order, x_header_map=LATEST_SHORT)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Source: Map of Variables 09 04 2026.xlsx - 'Latest round' tab. Blank/gray = variable not "
        "coded (or not comparable) in that survey's latest round. Shading groups variables into the "
        "mapping's 5 concept clusters; a handful of variables outside those clusters were classified "
        "by concept for this grouping only."
    )


def barometer_page():
    cdf = load_countries()
    st.session_state.setdefault("bar_pick", BAROMETERS[0])
    if "goto_bar_page" in st.session_state:
        st.session_state["bar_pick"] = st.session_state.pop("goto_bar_page")
    st.header("Barometer by period")
    bar = st.pills("Barometer", BAROMETERS, key="bar_pick",
                   format_func=lambda b: BAR_LABEL.get(b, b), label_visibility="collapsed") or BAROMETERS[0]
    csv_file, x_order, subtitle, source_note = BAR_PAGES[bar]
    st.subheader(f"{BAR_LABEL.get(bar, bar)}: coverage by cluster and period")
    st.caption(subtitle)

    tab_vars, tab_map = st.tabs(["Variables by period", "Countries by round"])
    with tab_vars:
        df_all = load_csv(csv_file)
        df, _ = cluster_pills(df_all, f"cluster_{bar}")
        period_col = "period" if "period" in df.columns else "year"
        fig = build_heatmap(df, x_col=period_col, x_order=x_order, cluster_col="cluster")
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        st.caption(source_note)

    with tab_map:
        d = cdf[cdf["barometer"] == bar]
        rounds = d.drop_duplicates("round")[["round", "year"]].reset_index(drop=True)
        labels = [f"{r.round} ({r.year})" for r in rounds.itertuples()]
        default = labels[-1]
        pick = st.select_slider("Round", options=labels, value=default, key=f"round_{bar}")
        rnd = rounds.iloc[labels.index(pick)]["round"]
        sel = d[d["round"] == rnd].drop_duplicates("iso3")
        c1, c2 = st.columns([3, 1.4])
        with c1:
            st.plotly_chart(round_map(sel, BAR_COLOR[bar]), use_container_width=True,
                            config={"displayModeBar": False, "scrollZoom": False})
        with c2:
            st.metric("Countries in this round", len(sel))
            counts = d.groupby("round", sort=False)["iso3"].nunique()
            st.caption("Countries per round: " + " · ".join(f"{k}: {v}" for k, v in counts.items()))
            st.caption(", ".join(sorted(sel["country"])))
        st.caption("Country lists: Arab Barometer, Latinobarómetro and Afrobarometer published documentation "
                   "(rounds/waves as released); Asian Barometer and Eurobarometer read from the raw data files.")


PAGE_OVERVIEW = st.Page(overview_page, title="Overview", url_path="overview", default=True)
PAGE_LATEST = st.Page(latest_page, title="Latest round", url_path="latest")
PAGE_BAROMETER = st.Page(barometer_page, title="Barometer by period", url_path="barometer")

st.navigation([PAGE_OVERVIEW, PAGE_LATEST, PAGE_BAROMETER]).run()
