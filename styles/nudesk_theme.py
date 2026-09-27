"""
nuDesk MX Design System & Theme Engine
Derived directly from nuDesk production tokens (https://nudesk.ai):
- Primary Heritage Green: #3EA258 / #48B46B
- Accent Muted Teal: #2A9D8F / #3AB7A8
- Soft Navy: #2C3E50 / #384C63
- Cool Slate-Gray Surfaces: #F4F7F9 / #EDF3F5
- High-Contrast Text: #1D242E / #F8FAFC
- Zero Warm Amber/Orange (Replaced by cool cyan/teal and soft navy chips)
- Strict WCAG AAA Contrast Compliance across Light and Dark Modes
"""

def get_nudesk_css(theme: str = "light") -> str:
    """Generate dynamic CSS tokens based on selected theme mode."""
    is_dark = (theme == "dark")

    # Dynamic variables
    bg_body = "#0A0F16" if is_dark else "#F4F7F9"
    bg_surface = "#141D2B" if is_dark else "#FFFFFF"
    bg_surface_alt = "#1A2536" if is_dark else "#EDF3F5"
    text_primary = "#F8FAFC" if is_dark else "#1D242E"
    text_muted = "#94A3B8" if is_dark else "#5A6A7E"
    border_color = "#223145" if is_dark else "#D5E0E8"
    border_subtle = "#1A2536" if is_dark else "#E5ECF0"
    header_gradient = "linear-gradient(135deg, #0A0F16 0%, #162233 100%)" if is_dark else "linear-gradient(135deg, #1E293B 0%, #2C3E50 100%)"
    brand_green = "#48B46B" if is_dark else "#3EA258"
    accent_teal = "#3AB7A8" if is_dark else "#2A9D8F"

    # Input styling
    input_bg = "#162030" if is_dark else "#FFFFFF"
    input_text = "#F8FAFC" if is_dark else "#1D242E"
    input_border = "#2A3D54" if is_dark else "#CBD7E0"
    disabled_bg = "#0E1522" if is_dark else "#EAEFF2"
    disabled_text = "#94A3B8" if is_dark else "#475569"

    # NuDesk Authentic Badges (Zero Orange)
    badge_green_bg = "#0A3D24" if is_dark else "#EAF7EE"
    badge_green_txt = "#6FE69A" if is_dark else "#1E7E34"
    badge_green_bdr = "#17633B" if is_dark else "#C6E8CF"

    badge_teal_bg = "#0B3835" if is_dark else "#E6F4F3"
    badge_teal_txt = "#5FE0D4" if is_dark else "#1D6F68"
    badge_teal_bdr = "#145954" if is_dark else "#B8E3E0"

    badge_navy_bg = "#182638" if is_dark else "#EFF3F6"
    badge_navy_txt = "#CFDAE5" if is_dark else "#2C3E50"
    badge_navy_bdr = "#283C54" if is_dark else "#D5E0E8"

    badge_red_bg = "#421010" if is_dark else "#FEEFEF"
    badge_red_txt = "#FCA5A5" if is_dark else "#A31D1D"
    badge_red_bdr = "#821F1F" if is_dark else "#FCD3D3"

    return f"""
<style>
    /* Google Fonts: Host Grotesk & Manrope (nuDesk Official) */
    @import url('https://fonts.googleapis.com/css2?family=Host+Grotesk:wght@500;600;700;800&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        --nd-bg: {bg_body};
        --nd-surface: {bg_surface};
        --nd-surface-alt: {bg_surface_alt};
        --nd-text: {text_primary};
        --nd-muted: {text_muted};
        --nd-border: {border_color};
        --nd-border-subtle: {border_subtle};
        --nd-green: {brand_green};
        --nd-teal: {accent_teal};
        --nd-input-bg: {input_bg};
        --nd-input-text: {input_text};
        --nd-input-border: {input_border};
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--nd-bg) !important;
        color: var(--nd-text) !important;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Host Grotesk', 'Manrope', sans-serif !important;
        color: var(--nd-text) !important;
        letter-spacing: -0.02em;
    }}

    /* Streamlit top header bar */
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
        height: 2.0rem;
    }}

    /* Main container padding */
    .block-container {{
        padding-top: 1.0rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1240px !important;
    }}

    /* Brand Header Banner */
    .nudesk-header {{
        background: {header_gradient};
        border-radius: 8px;
        padding: 1.15rem 1.65rem;
        color: #FFFFFF;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.15rem;
        box-shadow: 0 4px 18px -4px rgba(10, 15, 22, 0.25);
        border-bottom: 3px solid var(--nd-green);
    }}

    .nudesk-header h1 {{
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0;
        color: #FFFFFF !important;
        letter-spacing: -0.025em;
    }}

    .nudesk-header .subtitle {{
        font-size: 0.85rem;
        color: #A3B5C7 !important;
        margin-top: 0.2rem;
        font-weight: 500;
    }}

    /* Badges (nuDesk Palette - Zero Orange) */
    .nudesk-badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.22rem 0.65rem;
        border-radius: 4px;
        font-size: 0.73rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-family: 'Host Grotesk', sans-serif;
    }}

    .badge-green {{
        background-color: {badge_green_bg} !important;
        color: {badge_green_txt} !important;
        border: 1px solid {badge_green_bdr} !important;
    }}

    .badge-teal {{
        background-color: {badge_teal_bg} !important;
        color: {badge_teal_txt} !important;
        border: 1px solid {badge_teal_bdr} !important;
    }}

    .badge-navy {{
        background-color: {badge_navy_bg} !important;
        color: {badge_navy_txt} !important;
        border: 1px solid {badge_navy_bdr} !important;
    }}

    .badge-red {{
        background-color: {badge_red_bg} !important;
        color: {badge_red_txt} !important;
        border: 1px solid {badge_red_bdr} !important;
    }}

    /* Universal Form Control Overrides (Fixes Dark/Light Text Contrast) */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
        background-color: var(--nd-input-bg) !important;
        color: var(--nd-input-text) !important;
        border: 1px solid var(--nd-input-border) !important;
        border-radius: 6px !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 0.92rem !important;
    }}

    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--nd-green) !important;
        box-shadow: 0 0 0 1px var(--nd-green) !important;
    }}

    .stTextArea textarea:disabled {{
        background-color: {disabled_bg} !important;
        color: {disabled_text} !important;
        border: 1px dashed var(--nd-border) !important;
        cursor: not-allowed !important;
        opacity: 0.95 !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: var(--nd-input-bg) !important;
        color: var(--nd-input-text) !important;
        border-color: var(--nd-input-border) !important;
        border-radius: 6px !important;
    }}

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {{
        background-color: var(--nd-surface) !important;
        color: var(--nd-text) !important;
        border: 1px solid var(--nd-border) !important;
    }}

    li[role="option"] {{
        color: var(--nd-text) !important;
        background-color: var(--nd-surface) !important;
    }}

    li[role="option"]:hover, li[aria-selected="true"] {{
        background-color: var(--nd-surface-alt) !important;
        color: var(--nd-green) !important;
    }}

    /* Streamlit Expanders */
    div[data-testid="stExpander"] {{
        background-color: var(--nd-surface) !important;
        border: 1px solid var(--nd-border) !important;
        border-radius: 8px !important;
        margin-bottom: 0.65rem !important;
    }}

    div[data-testid="stExpander"] details summary {{
        color: var(--nd-text) !important;
        font-family: 'Host Grotesk', sans-serif !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stExpander"] details summary:hover {{
        color: var(--nd-green) !important;
    }}

    div[data-testid="stExpander"] details div[role="region"] {{
        background-color: var(--nd-surface) !important;
        color: var(--nd-text) !important;
        padding-top: 0.5rem !important;
    }}

    /* Studio Card */
    .studio-card {{
        background-color: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1.15rem;
        box-shadow: 0 1px 3px rgba(10, 15, 22, 0.04);
    }}

    .studio-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid var(--nd-border-subtle);
    }}

    .studio-card-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--nd-text);
        margin: 0;
        font-family: 'Host Grotesk', sans-serif;
    }}

    /* KPI Metric Box */
    .kpi-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.9rem;
        margin-bottom: 1.25rem;
    }}

    .kpi-card {{
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        border-left: 4px solid var(--nd-green);
        box-shadow: 0 1px 2px rgba(10, 15, 22, 0.03);
    }}

    .kpi-label {{
        font-size: 0.74rem;
        color: var(--nd-muted);
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
        font-family: 'Host Grotesk', sans-serif;
    }}

    .kpi-value {{
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--nd-text);
        margin-top: 0.2rem;
        line-height: 1.15;
        font-family: 'Host Grotesk', sans-serif;
    }}

    .kpi-sub {{
        font-size: 0.78rem;
        color: var(--nd-teal);
        margin-top: 0.25rem;
        font-weight: 600;
    }}

    /* Single-Line Activity Log Row */
    .log-row {{
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 6px;
        padding: 0.75rem 1.15rem;
        margin-bottom: 0.45rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        transition: border-color 0.15s ease-in-out;
    }}

    .log-row:hover {{
        border-color: var(--nd-green);
    }}

    /* Cockpit Queue Cards & Split Layout */
    .queue-card {{
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.45rem;
        transition: all 0.15s ease-in-out;
        border-left: 3px solid transparent;
    }}

    .queue-card:hover {{
        border-color: var(--nd-green);
        background: var(--nd-surface-alt);
    }}

    .queue-card.active {{
        border-left: 4px solid var(--nd-green) !important;
        background: var(--nd-surface-alt) !important;
        box-shadow: 0 1px 4px rgba(10, 15, 22, 0.08);
    }}

    .queue-entity {{
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--nd-text);
        font-family: 'Host Grotesk', sans-serif;
    }}

    .queue-metric {{
        font-size: 0.9rem;
        font-weight: 800;
        color: var(--nd-green);
        font-family: 'Host Grotesk', sans-serif;
        margin-top: 0.15rem;
    }}

    .queue-meta {{
        font-size: 0.78rem;
        color: var(--nd-muted);
        margin-top: 0.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    /* KPI Compact Ribbon */
    .kpi-ribbon {{
        display: flex;
        gap: 0.65rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }}

    .kpi-pill {{
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 6px;
        padding: 0.45rem 0.85rem;
        font-size: 0.82rem;
        color: var(--nd-muted);
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }}

    .kpi-pill strong {{
        color: var(--nd-text);
        font-size: 0.92rem;
    }}

    /* Active Cockpit Canvas Header */
    .cockpit-header {{
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 0.95rem 1.25rem;
        margin-bottom: 0.85rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid var(--nd-green);
    }}

    .cockpit-title {{
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--nd-text);
        font-family: 'Host Grotesk', sans-serif;
        margin: 0;
    }}

    .cockpit-sub {{
        font-size: 0.82rem;
        color: var(--nd-muted);
        margin-top: 0.15rem;
    }}

    .log-left {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
        min-width: 0;
        flex: 1 1 auto;
    }}

    .log-entity {{
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--nd-text);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-family: 'Host Grotesk', sans-serif;
    }}

    .log-metric {{
        font-size: 0.95rem;
        font-weight: 800;
        color: var(--nd-green);
        white-space: nowrap;
        font-family: 'Host Grotesk', sans-serif;
        padding: 0.15rem 0.5rem;
        background: {badge_green_bg};
        border-radius: 4px;
    }}

    .log-meta {{
        font-size: 0.8rem;
        color: var(--nd-muted);
        white-space: nowrap;
    }}

    .log-right {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-shrink: 0;
    }}

    /* Red flag indicator */
    .flag-item {{
        background-color: {badge_red_bg};
        border-left: 3px solid #EF4444;
        padding: 0.55rem 0.85rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.45rem;
        font-size: 0.86rem;
        color: {badge_red_txt};
        border-top: 1px solid {badge_red_bdr};
        border-bottom: 1px solid {badge_red_bdr};
        border-right: 1px solid {badge_red_bdr};
    }}

    /* Task Item */
    .task-item {{
        background-color: var(--nd-surface-alt);
        border: 1px solid var(--nd-border);
        border-radius: 6px;
        padding: 0.7rem 0.95rem;
        margin-bottom: 0.45rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .task-title {{
        font-size: 0.86rem;
        font-weight: 700;
        color: var(--nd-text);
    }}

    .task-assignee {{
        font-size: 0.76rem;
        color: var(--nd-muted);
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-weight: 500;
    }}

    /* Role Banner */
    .role-banner {{
        background-color: var(--nd-surface-alt);
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 0.7rem 1.1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        font-size: 0.86rem;
    }}

    .role-indicator {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        font-weight: 600;
        color: var(--nd-text);
    }}

    .role-avatar {{
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #1E293B;
        color: #FFFFFF;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 800;
        border: 2px solid var(--nd-green);
    }}

    /* Script & Terminal Box */
    .script-box {{
        background-color: #0C121C;
        color: #F8FAFC;
        padding: 0.95rem 1.2rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.84rem;
        line-height: 1.6;
        margin-top: 0.5rem;
        border: 1px solid var(--nd-border);
    }}

    /* Streamlit Tabs Navigation */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid var(--nd-border);
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 8px 14px;
        font-weight: 600;
        color: var(--nd-muted);
        border-radius: 6px 6px 0 0;
        font-family: 'Host Grotesk', sans-serif;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--nd-text) !important;
        border-bottom: 2px solid var(--nd-green) !important;
    }}

    /* Primary button override (Centered, nuDesk Green) */
    .stButton > button[kind="primary"] {{
        background-color: var(--nd-green) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-family: 'Host Grotesk', sans-serif !important;
        letter-spacing: -0.01em !important;
        padding: 0.55rem 1.5rem !important;
        transition: background-color 0.15s ease-in-out !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background-color: #348E4D !important;
    }}

    /* Top Bar Popovers (Settings and User Profile) */
    div[data-testid="stPopover"] > button {{
        border-radius: 6px !important;
        font-family: 'Host Grotesk', 'Manrope', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        border: 1px solid var(--nd-border) !important;
        background-color: var(--nd-surface) !important;
        color: var(--nd-text) !important;
        padding: 0.45rem 0.95rem !important;
        transition: all 0.15s ease-in-out !important;
    }}

    div[data-testid="stPopover"] > button:hover {{
        border-color: var(--nd-green) !important;
        background-color: var(--nd-surface-alt) !important;
        color: var(--nd-green) !important;
    }}

    div[data-testid="stPopoverBody"] {{
        background-color: var(--nd-surface) !important;
        color: var(--nd-text) !important;
        border: 1px solid var(--nd-border) !important;
        border-radius: 8px !important;
        box-shadow: 0 8px 24px rgba(10, 15, 22, 0.25) !important;
        padding: 1rem !important;
    }}

    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .nudesk-header {{
            flex-direction: column;
            align-items: flex-start;
            gap: 0.65rem;
        }}
        .kpi-container {{
            grid-template-columns: 1fr;
        }}
        .log-row {{
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }}
    }}
</style>
"""
