"""
CX Tech N2 — Service Desk Dashboard
Streamlit app · Jira Cloud REST API
"""

import os
from datetime import datetime, timedelta

import urllib3
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
CLOUD_ID       = "c5242d2e-3908-4a3a-8bef-054296db8c38"
FILTER_ID      = "23089"
RETAINED_SQUAD = "CX Tech-L2"
JIRA_BASE      = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3"
JIRA_FIELDS    = (
    "summary,status,assignee,created,resolutiondate,project,"
    "customfield_10950,customfield_10033,customfield_15420,customfield_17153,priority"
)

# Brand palette
C_GREEN       = "#0C8046"
C_GREEN_DARK  = "#034036"
C_GREEN_LIGHT = "#F2FFCC"
C_MAGENTA     = "#F2496B"
C_MAGENTA_LT  = "#FFEBF1"
C_PURPLE_MID  = "#5B4191"
C_PURPLE_MAIN = "#A880FF"
C_PURPLE_LT   = "#DDCCFF"
C_PURPLE_DARK = "#1B1340"
C_BG          = "#FBF8EC"
C_BG_S1       = "#F6EDDF"
C_BG_S2       = "#ECE0CD"
C_MUTED       = "#8a8099"


# ─────────────────────────────────────────────────────────────────────────────
# Page config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CX Tech N2 — Service Desk Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* ── Page background ── */
  .stApp {{ background: {C_BG}; }}
  .stApp > header {{ background: transparent; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
      background: white;
      border-right: 1px solid {C_BG_S2};
  }}
  [data-testid="stSidebar"] .stMarkdown p {{
      color: {C_PURPLE_MID};
      font-size: 12px;
  }}

  /* ── Give every Plotly chart a card look ── */
  [data-testid="stPlotlyChart"] > div {{
      background: white;
      border-radius: 10px;
      box-shadow: 0 1px 4px rgba(27,19,64,0.09);
      padding: 4px;
  }}

  /* ── DataFrames ── */
  [data-testid="stDataFrame"] > div {{
      border-radius: 10px;
      box-shadow: 0 1px 4px rgba(27,19,64,0.09);
      overflow: hidden;
  }}

  /* ── KPI cards ── */
  .kpi-card {{
      background: white;
      border-radius: 10px;
      padding: 18px 20px 14px;
      box-shadow: 0 1px 4px rgba(27,19,64,0.09);
      height: 100%;
  }}
  .kpi-icon  {{ font-size: 22px; margin-bottom: 6px; }}
  .kpi-val   {{ font-size: 30px; font-weight: 700; line-height: 1; }}
  .kpi-label {{
      font-size: 10px; color: {C_PURPLE_MID}; margin-top: 6px;
      text-transform: uppercase; letter-spacing: .06em; font-weight: 700;
  }}
  .kpi-sub   {{ font-size: 11px; color: {C_MUTED}; margin-top: 2px; }}
  .kpi-bar-bg {{
      height: 4px; background: {C_BG_S2};
      border-radius: 2px; margin-top: 10px; overflow: hidden;
  }}
  .kpi-bar   {{ height: 100%; border-radius: 2px; }}

  /* ── Section headers ── */
  .sec-header {{
      display: flex; align-items: center; gap: 10px;
      margin: 28px 0 10px;
  }}
  .sec-accent {{
      width: 4px; height: 22px;
      border-radius: 2px; flex-shrink: 0;
  }}
  .sec-title {{
      font-size: 15px; font-weight: 700; color: {C_PURPLE_DARK};
  }}
  .sec-sub {{
      font-size: 12px; color: {C_MUTED}; margin-left: 2px;
  }}

  /* ── Page header banner ── */
  .page-header {{
      background: linear-gradient(120deg, {C_PURPLE_DARK} 0%, {C_PURPLE_MID} 100%);
      border-radius: 12px;
      padding: 22px 28px;
      margin-bottom: 22px;
      display: flex;
      justify-content: space-between;
      align-items: center;
  }}
  .page-header h1 {{
      color: white !important;
      font-size: 20px;
      margin: 0 0 4px;
      font-weight: 700;
  }}
  .page-header p {{
      color: {C_PURPLE_LT};
      font-size: 12px;
      margin: 0;
  }}
  .page-header-right {{
      text-align: right;
  }}
  .page-header-right .date-badge {{
      background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.25);
      border-radius: 20px;
      padding: 4px 14px;
      color: white;
      font-size: 12px;
      font-weight: 500;
  }}
  .page-header-right .refresh-label {{
      color: {C_PURPLE_LT};
      font-size: 11px;
      margin-top: 6px;
  }}

  /* ── Chart sub-captions ── */
  .chart-cap {{
      font-size: 11px; font-weight: 600; color: {C_MUTED};
      text-transform: uppercase; letter-spacing: .04em;
      margin-bottom: 4px;
  }}

  /* ── Hide Streamlit branding ── */
  #MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────
def get_credentials():
    try:
        return st.secrets["JIRA_EMAIL"], st.secrets["JIRA_TOKEN"]
    except Exception:
        return os.getenv("JIRA_EMAIL", ""), os.getenv("JIRA_TOKEN", "")


# ─────────────────────────────────────────────────────────────────────────────
# Jira API  (cached 5 min)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_issues(from_date: str, to_date: str, email: str, _token: str):
    jql = (
        f"filter = {FILTER_ID}"
        f' AND created >= "{from_date}"'
        f' AND created <= "{to_date}"'
        f" ORDER BY created ASC"
    )
    all_issues, next_token = [], None
    progress = st.empty()

    while True:
        progress.caption(f"⏳ Fetching tickets… {len(all_issues)} loaded")
        body = {"jql": jql, "fields": JIRA_FIELDS.split(","), "maxResults": 100}
        if next_token:
            body["nextPageToken"] = next_token

        resp = requests.post(
            f"{JIRA_BASE}/search/jql",
            auth=(email, _token),
            json=body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        data  = resp.json()
        batch = data.get("issues", [])
        all_issues.extend(batch)
        next_token = data.get("nextPageToken")
        if not next_token or not batch:
            break

    progress.empty()
    return all_issues


# ─────────────────────────────────────────────────────────────────────────────
# Field helpers
# ─────────────────────────────────────────────────────────────────────────────
def is_retained(i):  return (i["fields"].get("customfield_10950") or {}).get("value", "") == RETAINED_SQUAD
def get_squad(i):    return (i["fields"].get("customfield_15420") or {}).get("value", "Unknown")
def is_done(i):      return (i["fields"].get("status") or {}).get("statusCategory", {}).get("key") == "done"

def get_issue_tag(i):
    tags = i["fields"].get("customfield_17153") or []
    return tags[0].replace("_", " ") if tags else "Unknown"

def get_sla(i):
    sla = i["fields"].get("customfield_10033")
    if not sla: return {"available": False}
    cycles = sla.get("completedCycles", [])
    if cycles: return {"available": True, "breached": cycles[-1].get("breached", False)}
    ongoing = sla.get("ongoingCycle")
    if ongoing: return {"available": True, "breached": ongoing.get("breached", False)}
    return {"available": False}

def get_ym(i):
    d = i["fields"].get("created", "")
    if not d: return ""
    dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
    return f"{dt.year}-{dt.month:02d}"

def label_ym(ym):
    y, m = ym.split("-")
    return datetime(int(y), int(m), 1).strftime("%b %y")

def pct(n, t):        return round(n * 100 / t) if t else 0
def ret_color(r):     return C_GREEN if r >= 80 else C_PURPLE_MAIN if r >= 60 else C_MAGENTA

def fmt_date(d):
    if not d: return "—"
    return datetime.fromisoformat(d.replace("Z", "+00:00")).strftime("%d %b %Y")

def fmt_resolution(created, resolved):
    if not resolved: return "—"
    h = (
        datetime.fromisoformat(resolved.replace("Z", "+00:00"))
        - datetime.fromisoformat(created.replace("Z", "+00:00"))
    ).total_seconds() / 3600
    if h < 1:  return "<1h"
    if h < 24: return f"{round(h)}h"
    return f"{h / 24:.1f}d"


# ─────────────────────────────────────────────────────────────────────────────
# Chart defaults
# ─────────────────────────────────────────────────────────────────────────────
def chart_layout(**overrides):
    base = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                  color=C_PURPLE_DARK, size=11),
        margin=dict(l=12, r=12, t=36, b=12),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.28,
            xanchor="center", x=0.5, font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="white", bordercolor=C_BG_S2,
                        font=dict(size=12, color=C_PURPLE_DARK)),
    )
    base.update(overrides)
    return base

AXIS_DEFAULTS = dict(
    showgrid=True, gridcolor=C_BG_S1,
    zeroline=False, linecolor=C_BG_S2, tickfont=dict(size=11)
)

def section(title, subtitle="", color=C_MAGENTA):
    st.markdown(
        f'<div class="sec-header">'
        f'<div class="sec-accent" style="background:{color}"></div>'
        f'<span class="sec-title">{title}</span>'
        f'<span class="sec-sub">{subtitle}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Credentials check
# ─────────────────────────────────────────────────────────────────────────────
email, token = get_credentials()
if not email or not token:
    st.error(
        "**Missing Jira credentials.**  \n"
        "Add `JIRA_EMAIL` and `JIRA_TOKEN` to your `.env` file (local) "
        "or to *App settings → Secrets* on Streamlit Community Cloud."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="padding:16px 0 8px">'
        f'<span style="font-size:22px">🎯</span>'
        f'<span style="font-size:16px;font-weight:700;color:{C_PURPLE_DARK};margin-left:8px">N2 Dashboard</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:{C_PURPLE_MID};text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Date range</div>', unsafe_allow_html=True)

    today        = datetime.today().date()
    default_from = (datetime.today() - timedelta(days=90)).date()
    date_range   = st.date_input("", value=(default_from, today), max_value=today, label_visibility="collapsed")

    if len(date_range) != 2:
        st.warning("Select a start and end date.")
        st.stop()

    from_date, to_date = str(date_range[0]), str(date_range[1])
    st.divider()

    with st.spinner("Loading from Jira…"):
        try:
            issues = fetch_all_issues(from_date, to_date, email, token)
        except requests.HTTPError as e:
            st.error(f"Jira API error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    if not issues:
        st.warning("No tickets found for this period.")
        st.stop()

    st.markdown(
        f'<div style="background:{C_GREEN_LIGHT};border-radius:6px;padding:8px 12px;'
        f'font-size:12px;color:{C_GREEN_DARK};font-weight:600">'
        f'✓ {len(issues)} tickets loaded</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    if "fk" not in st.session_state:
        st.session_state.fk = 0
    fk = st.session_state.fk

    st.markdown(f'<div style="font-size:11px;font-weight:700;color:{C_PURPLE_MID};text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Filters</div>', unsafe_allow_html=True)

    projects = sorted({(i["fields"].get("project") or {}).get("name", "Unknown") for i in issues})
    proj_sel = st.selectbox("Project",   ["All Projects"] + projects,                      key=f"proj_{fk}")

    squads   = sorted({get_squad(i) for i in issues})
    sq_sel   = st.selectbox("Squad",     ["All Squads"]   + squads,                        key=f"sq_{fk}")

    tags     = sorted({get_issue_tag(i) for i in issues})
    tag_sel  = st.selectbox("Issue Tag", ["All Tags"]     + tags,                          key=f"tag_{fk}")

    months_avail = sorted({get_ym(i) for i in issues if get_ym(i)})
    month_labels = [label_ym(m) for m in months_avail]
    mo_sel   = st.selectbox("Month",     ["All Months"]   + month_labels,                  key=f"mo_{fk}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✕  Clear all filters", type="secondary", use_container_width=True):
        st.session_state.fk += 1
        st.rerun()

    st.divider()
    st.markdown(
        f'<div style="font-size:11px;color:{C_MUTED}">Refreshed {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Apply filters
# ─────────────────────────────────────────────────────────────────────────────
filtered = issues[:]
if proj_sel != "All Projects": filtered = [i for i in filtered if (i["fields"].get("project") or {}).get("name") == proj_sel]
if sq_sel   != "All Squads":   filtered = [i for i in filtered if get_squad(i) == sq_sel]
if tag_sel  != "All Tags":     filtered = [i for i in filtered if get_issue_tag(i) == tag_sel]
if mo_sel   != "All Months":
    sel_ym = next((m for m in months_avail if label_ym(m) == mo_sel), None)
    if sel_ym: filtered = [i for i in filtered if get_ym(i) == sel_ym]

active_filters = [f for f in [
    proj_sel if proj_sel != "All Projects" else None,
    sq_sel   if sq_sel   != "All Squads"   else None,
    tag_sel  if tag_sel  != "All Tags"     else None,
    mo_sel   if mo_sel   != "All Months"   else None,
] if f]


# ─────────────────────────────────────────────────────────────────────────────
# KPI calculations
# ─────────────────────────────────────────────────────────────────────────────
total      = len(filtered)
retained   = sum(1 for i in filtered if is_retained(i))
escalated  = total - retained
open_cnt   = sum(1 for i in filtered if not is_done(i))
done_cnt   = total - open_cnt
ret_rate   = pct(retained, total)

sla_issues   = [i for i in filtered if get_sla(i)["available"]]
sla_breached = sum(1 for i in sla_issues if get_sla(i)["breached"])
sla_ok       = len(sla_issues) - sla_breached
sla_rate     = pct(sla_ok, len(sla_issues)) if sla_issues else None

rc      = ret_color(ret_rate)
sc      = ret_color(sla_rate) if sla_rate is not None else "#97a0af"
sla_val = f"{sla_rate}%" if sla_rate is not None else "—"
sla_sub = f"{sla_breached} breached" if sla_issues else "no SLA data"

filter_note = " · ".join(active_filters) if active_filters else "All data"
date_label  = f"{date_range[0].strftime('%d %b %y')} → {date_range[1].strftime('%d %b %y')}"


# ─────────────────────────────────────────────────────────────────────────────
# Page header banner
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div>
    <h1>🎯 CX Tech N2 — Service Desk Dashboard</h1>
    <p>{filter_note}</p>
  </div>
  <div class="page-header-right">
    <div class="date-badge">{date_label}</div>
    <div class="refresh-label">Refreshed {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI cards
# ─────────────────────────────────────────────────────────────────────────────
def kpi_card(icon, val, label, sub, color, bar_pct=None):
    bar_html = ""
    if bar_pct is not None:
        bar_html = (
            f'<div class="kpi-bar-bg">'
            f'<div class="kpi-bar" style="width:{bar_pct}%;background:{color}"></div>'
            f'</div>'
        )
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-val" style="color:{color}">{val}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'{bar_html}'
        f'</div>'
    )

cols = st.columns(6)
cards = [
    ("📥", str(total),    "Total Received",  "escalated to L2",  C_PURPLE_DARK, None),
    ("✅", str(retained), "Retained (N2)",   "resolved by team", C_GREEN,       None),
    ("⬆️", str(escalated),"Escalated (L3)",  "passed to N3",     C_MAGENTA,     None),
    ("📊", f"{ret_rate}%","Retention Rate",  "",                 rc,            ret_rate),
    ("🔵", str(open_cnt), "Open",            f"{done_cnt} done", C_PURPLE_MAIN, None),
    ("⏱️", sla_val,       "SLA Compliance",  sla_sub,            sc,            sla_rate),
]
for col, (icon, val, label, sub, color, bar) in zip(cols, cards):
    with col:
        st.markdown(kpi_card(icon, val, label, sub, color, bar), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Monthly buckets
# ─────────────────────────────────────────────────────────────────────────────
mb = {}
for i in filtered:
    ym = get_ym(i)
    if not ym: continue
    if ym not in mb:
        mb[ym] = dict(retained=0, escalated=0, open=0, sla_ok=0, sla_br=0)
    if not is_done(i):           mb[ym]["open"]      += 1
    elif is_retained(i):         mb[ym]["retained"]   += 1
    else:                        mb[ym]["escalated"]  += 1
    sla = get_sla(i)
    if sla["available"]:
        if sla["breached"]:      mb[ym]["sla_br"]     += 1
        else:                    mb[ym]["sla_ok"]      += 1

months   = sorted(mb.keys())
m_labels = [label_ym(m) for m in months]


# ─────────────────────────────────────────────────────────────────────────────
# Row 1 — Retention donut + Monthly volume
# ─────────────────────────────────────────────────────────────────────────────
section("Ticket Volume & Retention", color=C_PURPLE_MAIN)
col_d, col_v = st.columns([1, 2])

with col_d:
    fig = go.Figure(go.Pie(
        labels=["Retained (N2)", "Escalated (L3)", "Still Open"],
        values=[retained, escalated, open_cnt],
        hole=0.62,
        marker=dict(colors=[C_GREEN, C_MAGENTA, C_PURPLE_MID], line=dict(color="white", width=2)),
        textinfo="percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value} tickets (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{ret_rate}%</b><br><span style='font-size:10px'>retained</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=rc),
        align="center",
    )
    fig.update_layout(title=dict(text="Retention vs L3 Escalation", font=dict(size=13, color=C_PURPLE_DARK)), height=290, **chart_layout(margin=dict(l=12, r=12, t=40, b=12)))
    st.plotly_chart(fig, use_container_width=True)

with col_v:
    rr_line = [
        round(mb[m]["retained"] / (mb[m]["retained"] + mb[m]["escalated"]) * 100)
        if (mb[m]["retained"] + mb[m]["escalated"]) else None
        for m in months
    ]
    fig = go.Figure([
        go.Bar(name="Retained (N2)",  x=m_labels, y=[mb[m]["retained"]  for m in months],
               marker=dict(color=C_GREEN,      line=dict(width=0)), offsetgroup=0,
               hovertemplate="<b>%{x}</b><br>Retained: %{y}<extra></extra>"),
        go.Bar(name="Escalated (L3)", x=m_labels, y=[mb[m]["escalated"] for m in months],
               marker=dict(color=C_MAGENTA,    line=dict(width=0)), offsetgroup=0,
               hovertemplate="<b>%{x}</b><br>Escalated: %{y}<extra></extra>"),
        go.Bar(name="Open",           x=m_labels, y=[mb[m]["open"]      for m in months],
               marker=dict(color=C_PURPLE_MID, line=dict(width=0)), offsetgroup=0,
               hovertemplate="<b>%{x}</b><br>Open: %{y}<extra></extra>"),
        go.Scatter(
            name="Retention %", x=m_labels, y=rr_line,
            mode="lines+markers",
            line=dict(color=C_PURPLE_MAIN, width=2.5, dash="dot"),
            marker=dict(size=7, color=C_PURPLE_MAIN, line=dict(color="white", width=1.5)),
            yaxis="y2", connectgaps=True,
            hovertemplate="<b>%{x}</b><br>Retention: %{y}%<extra></extra>",
        ),
    ])
    fig.update_layout(
        title=dict(text="Monthly Ticket Volume", font=dict(size=13, color=C_PURPLE_DARK)),
        barmode="stack", height=290,
        xaxis=dict(**AXIS_DEFAULTS),
        yaxis=dict(title="Tickets", **AXIS_DEFAULTS),
        yaxis2=dict(overlaying="y", side="right", range=[0, 110], ticksuffix="%",
                    showgrid=False, tickfont=dict(color=C_PURPLE_MAIN),
                    title=dict(text="Retention %", font=dict(color=C_PURPLE_MAIN))),
        **chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Row 2 — SLA
# ─────────────────────────────────────────────────────────────────────────────
section("SLA Performance", color=C_GREEN)
col_sd, col_sm = st.columns([1, 2])

with col_sd:
    if sla_issues:
        fig = go.Figure(go.Pie(
            labels=["SLA Met", "SLA Breached"],
            values=[sla_ok, sla_breached],
            hole=0.62,
            marker=dict(colors=[C_GREEN, C_MAGENTA], line=dict(color="white", width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>%{value} tickets (%{percent})<extra></extra>",
        ))
        sla_disp = f"{sla_rate}%" if sla_rate is not None else "—"
        fig.add_annotation(
            text=f"<b>{sla_disp}</b><br><span style='font-size:10px'>SLA met</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=sc), align="center",
        )
        fig.update_layout(title=dict(text="SLA Compliance", font=dict(size=13, color=C_PURPLE_DARK)), height=290, **chart_layout(margin=dict(l=12, r=12, t=40, b=12)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No SLA data available for this period.")

with col_sm:
    fig = go.Figure([
        go.Bar(name="SLA Met",      x=m_labels, y=[mb[m]["sla_ok"] for m in months],
               marker=dict(color=C_GREEN,  line=dict(width=0)), offsetgroup=0),
        go.Bar(name="SLA Breached", x=m_labels, y=[mb[m]["sla_br"] for m in months],
               marker=dict(color=C_MAGENTA, line=dict(width=0)), offsetgroup=0),
    ])
    fig.update_layout(
        title=dict(text="SLA Breaches by Month", font=dict(size=13, color=C_PURPLE_DARK)),
        barmode="stack", height=290,
        **chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: paired horizontal bar charts
# ─────────────────────────────────────────────────────────────────────────────
def render_hbar_pair(sec_title, sec_sub, items_vol, items_rate):
    section(sec_title, sec_sub, color=C_MAGENTA)
    col_vol, col_rate = st.columns(2)
    bar_h = max(260, len(items_vol) * 44)

    with col_vol:
        st.markdown('<div class="chart-cap">Volume — Retained vs Escalated</div>', unsafe_allow_html=True)
        fig = go.Figure([
            go.Bar(
                name="Retained (N2)",
                y=[s["name"] for s in items_vol], x=[s["retained"]  for s in items_vol],
                orientation="h", marker=dict(color=C_GREEN,  line=dict(width=0)), offsetgroup=0,
                hovertemplate="<b>%{y}</b><br>Retained: %{x}<extra></extra>",
            ),
            go.Bar(
                name="Escalated (L3)",
                y=[s["name"] for s in items_vol], x=[s["escalated"] for s in items_vol],
                orientation="h", marker=dict(color=C_MAGENTA, line=dict(width=0)), offsetgroup=0,
                hovertemplate="<b>%{y}</b><br>Escalated: %{x}<extra></extra>",
            ),
        ])
        fig.update_layout(
            barmode="stack", height=bar_h,
            xaxis=dict(title="Tickets", showgrid=True, gridcolor=C_BG_S1),
            yaxis=dict(showgrid=False, tickfont=dict(size=11)),
            **chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_rate:
        st.markdown('<div class="chart-cap">Retention Rate %</div>', unsafe_allow_html=True)
        rates = [pct(s["retained"], s["total"]) for s in items_rate]
        fig = go.Figure(go.Bar(
            y=[s["name"] for s in items_rate], x=rates,
            orientation="h",
            marker=dict(color=[ret_color(r) for r in rates], line=dict(width=0)),
            text=[f"  {r}%" for r in rates],
            textposition="outside",
            textfont=dict(size=11, color=C_PURPLE_DARK),
            hovertemplate="<b>%{y}</b><br>Retention: %{x}%<br>Total: %{customdata} tickets<extra></extra>",
            customdata=[s["total"] for s in items_rate],
        ))
        fig.update_layout(
            height=bar_h,
            xaxis=dict(range=[0, 118], ticksuffix="%", showgrid=True, gridcolor=C_BG_S1),
            yaxis=dict(showgrid=False, tickfont=dict(size=11)),
            showlegend=False,
            **chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Squad charts
# ─────────────────────────────────────────────────────────────────────────────
squad_map = {}
for i in filtered:
    sq = get_squad(i)
    if sq not in squad_map: squad_map[sq] = dict(retained=0, escalated=0)
    if is_retained(i): squad_map[sq]["retained"] += 1
    else:              squad_map[sq]["escalated"] += 1

top_squads     = sorted(
    [{"name": k, **v, "total": v["retained"] + v["escalated"]} for k, v in squad_map.items()],
    key=lambda x: x["total"], reverse=True,
)[:10]
squads_by_rate = sorted(top_squads, key=lambda s: pct(s["retained"], s["total"]))

render_hbar_pair(
    "Top Squads by Volume",
    f"top {len(top_squads)} of {len(squad_map)}",
    list(reversed(top_squads)),
    squads_by_rate,
)


# ─────────────────────────────────────────────────────────────────────────────
# Issue tag charts
# ─────────────────────────────────────────────────────────────────────────────
issue_map = {}
for i in filtered:
    tag = get_issue_tag(i)
    if tag not in issue_map: issue_map[tag] = dict(retained=0, escalated=0)
    if is_retained(i): issue_map[tag]["retained"] += 1
    else:              issue_map[tag]["escalated"] += 1

top_tags     = sorted(
    [{"name": k, **v, "total": v["retained"] + v["escalated"]} for k, v in issue_map.items()],
    key=lambda x: x["total"], reverse=True,
)[:10]
tags_by_rate = sorted(top_tags, key=lambda s: pct(s["retained"], s["total"]))

render_hbar_pair(
    "Top Issue Tags by Volume",
    f"top {len(top_tags)} of {len(issue_map)}",
    list(reversed(top_tags)),
    tags_by_rate,
)


# ─────────────────────────────────────────────────────────────────────────────
# By Area (Project)
# ─────────────────────────────────────────────────────────────────────────────
section("By Area (Project)", color=C_PURPLE_MID)

areas = {}
for i in filtered:
    proj = (i["fields"].get("project") or {}).get("name", "Unknown")
    if proj not in areas: areas[proj] = dict(total=0, retained=0, escalated=0, sla_br=0, sla_tot=0)
    areas[proj]["total"] += 1
    if is_retained(i): areas[proj]["retained"] += 1
    else:              areas[proj]["escalated"] += 1
    sla = get_sla(i)
    if sla["available"]:
        areas[proj]["sla_tot"] += 1
        if sla["breached"]: areas[proj]["sla_br"] += 1

area_rows = [
    {
        "Project":        name,
        "Total":          a["total"],
        "Retained (N2)":  a["retained"],
        "Escalated (L3)": a["escalated"],
        "Retention Rate": f"{pct(a['retained'], a['total'])}%",
        "SLA Breached":   f"{a['sla_br']} / {a['sla_tot']}" if a["sla_tot"] else "—",
    }
    for name, a in sorted(areas.items(), key=lambda x: -x[1]["total"])
]
if area_rows:
    st.dataframe(pd.DataFrame(area_rows), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Team Workload
# ─────────────────────────────────────────────────────────────────────────────
section("Team Workload", color=C_PURPLE_MID)

workload = {}
for i in filtered:
    name = (i["fields"].get("assignee") or {}).get("displayName", "Unassigned")
    if name not in workload: workload[name] = dict(open=0, done=0, retained=0, escalated=0)
    if not is_done(i): workload[name]["open"] += 1
    else:              workload[name]["done"] += 1
    if is_retained(i): workload[name]["retained"] += 1
    else:              workload[name]["escalated"] += 1

wl_rows = [
    {
        "Assignee":     name,
        "Open":         w["open"],
        "Done":         w["done"],
        "Retained":     w["retained"],
        "Escalated L3": w["escalated"],
        "Total":        w["retained"] + w["escalated"],
        "Retention %":  f"{pct(w['retained'], w['retained'] + w['escalated'])}%",
    }
    for name, w in sorted(workload.items(), key=lambda x: -(x[1]["retained"] + x[1]["escalated"]))
]
if wl_rows:
    st.dataframe(pd.DataFrame(wl_rows), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# All Tickets
# ─────────────────────────────────────────────────────────────────────────────
section("All Tickets", color=C_PURPLE_MID)

fc1, fc2, fc3, fc4 = st.columns(4)
with fc1: status_f = st.selectbox("Status", ["All", "Done", "Open / WIP"],       key=f"fs_{fk}")
with fc2: type_f   = st.selectbox("Type",   ["All", "Retained", "Escalated L3"], key=f"ft_{fk}")
with fc3: sla_f    = st.selectbox("SLA",    ["All", "Breached", "OK"],           key=f"fl_{fk}")
with fc4: search_f = st.text_input("Search summary", placeholder="Type to search…", key=f"fq_{fk}")

tf = filtered[:]
if status_f == "Done":         tf = [i for i in tf if is_done(i)]
if status_f == "Open / WIP":   tf = [i for i in tf if not is_done(i)]
if type_f   == "Retained":     tf = [i for i in tf if is_retained(i)]
if type_f   == "Escalated L3": tf = [i for i in tf if not is_retained(i)]
if sla_f    == "Breached":     tf = [i for i in tf if get_sla(i)["available"] and     get_sla(i)["breached"]]
if sla_f    == "OK":           tf = [i for i in tf if get_sla(i)["available"] and not get_sla(i)["breached"]]
if search_f:                   tf = [i for i in tf if search_f.lower() in (i["fields"].get("summary") or "").lower()]

ticket_rows = [
    {
        "Key":        f"https://gympass.atlassian.net/browse/{i['key']}",
        "Summary":    (i["fields"].get("summary") or "")[:90],
        "Project":    (i["fields"].get("project") or {}).get("key", "?"),
        "Squad":      get_squad(i),
        "Assignee":   (i["fields"].get("assignee") or {}).get("displayName", "Unassigned"),
        "Status":     (i["fields"].get("status") or {}).get("name", "?"),
        "Type":       "Retained" if is_retained(i) else "Escalated L3",
        "SLA":        ("Breached" if get_sla(i)["breached"] else "OK") if get_sla(i)["available"] else "—",
        "Created":    fmt_date(i["fields"].get("created")),
        "Resolution": fmt_resolution(i["fields"].get("created"), i["fields"].get("resolutiondate")),
    }
    for i in tf
]

if ticket_rows:
    df_t = pd.DataFrame(ticket_rows)
    st.dataframe(
        df_t,
        hide_index=True,
        use_container_width=True,
        height=420,
        column_config={
            "Key": st.column_config.LinkColumn("Key", display_text=r"browse/(\S+)$"),
        },
    )
    st.markdown("<br>", unsafe_allow_html=True)
    csv_bytes = df_t.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️  Download CSV",
        data=csv_bytes,
        file_name=f"N2_dashboard_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )
else:
    st.info("No tickets match the current filters.")
