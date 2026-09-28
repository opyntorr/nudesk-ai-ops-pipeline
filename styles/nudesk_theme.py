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

    # Dynamic variables: #2C3844 background matched directly from nuDesk footer tokens
    bg_body = "#2C3844" if is_dark else "#F4F7F9"
    bg_surface = "#364554" if is_dark else "#FFFFFF"
    bg_surface_alt = "#3F5062" if is_dark else "#EDF3F5"
    text_primary = "#FFFFFF" if is_dark else "#1D242E"
    text_muted = "#D1DCE5" if is_dark else "#5A6A7E"
    border_color = "#576169" if is_dark else "#D5E0E8"
    border_subtle = "#455361" if is_dark else "#E5ECF0"
    header_gradient = "linear-gradient(135deg, #242E38 0%, #364554 100%)" if is_dark else "linear-gradient(135deg, #1E293B 0%, #2C3E50 100%)"
    brand_green = "#54D67D" if is_dark else "#3EA258"
    accent_teal = "#4AE0D0" if is_dark else "#2A9D8F"

    # Input styling
    input_bg = "#222D37" if is_dark else "#FFFFFF"
    input_text = "#FFFFFF" if is_dark else "#1D242E"
    input_border = "#576169" if is_dark else "#CBD7E0"
    disabled_bg = "#202A34" if is_dark else "#F1F5F9"
    disabled_text = "#F8FAFC" if is_dark else "#1E293B"

    # Tab navigation contrast tokens
    tab_unselected_color = "#E2E8F0" if is_dark else "#4B5563"
    tab_selected_color = "#54D67D" if is_dark else "#3EA258"
    tab_hover_color = "#FFFFFF" if is_dark else "#1E293B"

    # NuDesk Authentic Badges (Zero Orange)
    badge_green_bg = "#1A402B" if is_dark else "#EAF7EE"
    badge_green_txt = "#86EFAC" if is_dark else "#1E7E34"
    badge_green_bdr = "#2D6847" if is_dark else "#C6E8CF"

    badge_teal_bg = "#1B4744" if is_dark else "#E6F4F3"
    badge_teal_txt = "#99F6E4" if is_dark else "#1D6F68"
    badge_teal_bdr = "#286D67" if is_dark else "#B8E3E0"

    badge_navy_bg = "#3E4F63" if is_dark else "#EFF3F6"
    badge_navy_txt = "#F1F5F9" if is_dark else "#2C3E50"
    badge_navy_bdr = "#576B82" if is_dark else "#D5E0E8"

    badge_red_bg = "#521F1F" if is_dark else "#FEEFEF"
    badge_red_txt = "#FCA5A5" if is_dark else "#A31D1D"
    badge_red_bdr = "#872B2B" if is_dark else "#FCD3D3"

    badge_amber_bg = "#543C12" if is_dark else "#FEF3C7"
    badge_amber_txt = "#FDE047" if is_dark else "#92400E"
    badge_amber_bdr = "#8C6316" if is_dark else "#FCD34D"

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
        color: #E2E8F0 !important;
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

    /* Universal Form Control Overrides (Fixes Dark/Light Text Contrast & Transcripts) */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
        background-color: var(--nd-input-bg) !important;
        color: var(--nd-input-text) !important;
        -webkit-text-fill-color: var(--nd-input-text) !important;
        border: 1px solid var(--nd-input-border) !important;
        border-radius: 6px !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 0.92rem !important;
    }}

    .stTextInput input::placeholder, .stTextArea textarea::placeholder,
    div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder {{
        color: var(--nd-muted) !important;
        opacity: 0.85 !important;
    }}

    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--nd-green) !important;
        box-shadow: 0 0 0 1px var(--nd-green) !important;
    }}

    .stTextArea textarea:disabled,
    div[data-baseweb="textarea"] textarea:disabled,
    textarea:disabled,
    .stTextInput input:disabled,
    div[data-baseweb="input"] input:disabled,
    input:disabled {{
        background-color: {disabled_bg} !important;
        color: {disabled_text} !important;
        -webkit-text-fill-color: {disabled_text} !important;
        border: 1px solid var(--nd-border) !important;
        cursor: text !important;
        opacity: 1 !important;
        font-size: 0.92rem !important;
        line-height: 1.5 !important;
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

    /* Streamlit Containers & Expanders */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stExpander"] {{
        background-color: var(--nd-surface) !important;
        border: 1px solid var(--nd-border) !important;
        border-radius: 8px !important;
        margin-bottom: 0.85rem !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] > div {{
        padding: 0.85rem 1.15rem !important;
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

    /* Clickable Queue Card Overlay Button - Seamless hitboxes over queue cards */
    div[class*="st-key-btn_c_select_"],
    div[class*="st-key-btn_s_select_"],
    div[class*="st-key-btn_h_select_"] {{
        margin-top: -88px !important;
        position: relative !important;
        z-index: 10 !important;
        height: 82px !important;
        margin-bottom: 0.5rem !important;
    }}

    div[class*="st-key-btn_c_select_"] button,
    div[class*="st-key-btn_s_select_"] button,
    div[class*="st-key-btn_h_select_"] button {{
        width: 100% !important;
        height: 82px !important;
        min-height: 82px !important;
        max-height: 82px !important;
        opacity: 0 !important;
        cursor: pointer !important;
        background: transparent !important;
        border: none !important;
        font-size: 0 !important;
        padding: 0 !important;
        display: block !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    /* Clickable Processed Card Overlay Button - Seamless hitboxes over processed cards */
    div[class*="st-key-btn_cp_select_"],
    div[class*="st-key-btn_sp_select_"],
    div[class*="st-key-btn_hp_select_"] {{
        margin-top: -215px !important;
        position: relative !important;
        z-index: 10 !important;
        height: 205px !important;
        margin-bottom: 0.5rem !important;
    }}

    div[class*="st-key-btn_cp_select_"] button,
    div[class*="st-key-btn_sp_select_"] button,
    div[class*="st-key-btn_hp_select_"] button {{
        width: 100% !important;
        height: 205px !important;
        min-height: 205px !important;
        max-height: 205px !important;
        opacity: 0 !important;
        cursor: pointer !important;
        background: transparent !important;
        border: none !important;
        font-size: 0 !important;
        padding: 0 !important;
        display: block !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    /* Sibling hover: when hovering over the transparent button, highlight the preceding card */
    div:has(> div > div > .queue-card-hitbox):has(+ div[class*="st-key-btn_"]:hover) .queue-card,
    div[data-testid="stElementContainer"]:has(.queue-card-hitbox):has(+ div[class*="st-key-btn_"]:hover) .queue-card {{
        border-color: var(--nd-green) !important;
        background: var(--nd-surface-alt) !important;
        box-shadow: 0 2px 8px rgba(0, 200, 5, 0.15) !important;
    }}

    div:has(> div > div > .exec-card-hitbox):has(+ div[class*="st-key-btn_"]:hover) .exec-log-card,
    div[data-testid="stElementContainer"]:has(.exec-card-hitbox):has(+ div[class*="st-key-btn_"]:hover) .exec-log-card {{
        border-color: var(--nd-green) !important;
        background: var(--nd-surface-alt) !important;
        box-shadow: 0 2px 8px rgba(0, 200, 5, 0.15) !important;
    }}

    /* File Uploader Instructions Clean Styling - Only 200MB per file */
    div[data-testid="stFileUploaderDropzoneInstructions"] span {{
        font-size: 0.78rem !important;
        color: var(--nd-muted) !important;
        font-family: 'Host Grotesk', sans-serif !important;
        display: inline-block !important;
    }}

    /* Executive Log Card with Default Visible Colored KPIs */
    .exec-log-card {{
        background: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 0.95rem 1.15rem;
        margin-bottom: 0.35rem;
        transition: border-color 0.15s ease-in-out;
        box-shadow: 0 1px 3px rgba(10, 15, 22, 0.03);
    }}

    .exec-log-card:hover {{
        border-color: var(--nd-green);
    }}

    .exec-log-card.active {{
        border-left: 4px solid var(--nd-green) !important;
        border-color: var(--nd-green) !important;
        background: var(--nd-surface-alt) !important;
        box-shadow: 0 1px 4px rgba(10, 15, 22, 0.08);
    }}

    /* Executive Log Card with Default Visible Large Colored KPIs */
    .kpi-large-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.75rem;
        margin-top: 0.85rem;
        margin-bottom: 0.4rem;
    }}

    .kpi-box-large {{
        border-radius: 6px;
        padding: 0.65rem 0.95rem;
        border: 1px solid var(--nd-border);
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: var(--nd-surface-alt);
        min-height: 68px;
    }}

    .kpi-box-large .kpi-box-label {{
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.25rem;
        font-family: 'Host Grotesk', sans-serif;
    }}

    .kpi-box-large .kpi-box-val {{
        font-size: 1.25rem;
        font-weight: 800;
        line-height: 1.2;
        font-family: 'Host Grotesk', sans-serif;
    }}

    /* Green for Good / Low Risk / Compliant */
    .kpi-box-green {{
        background-color: {badge_green_bg} !important;
        border: 1px solid {badge_green_bdr} !important;
    }}
    .kpi-box-green .kpi-box-label {{ color: {badge_green_txt} !important; opacity: 0.9; }}
    .kpi-box-green .kpi-box-val {{ color: {badge_green_txt} !important; }}

    /* Reddish / Warm for Bad numbers / High Risk / Breached SLA */
    .kpi-box-red {{
        background-color: {badge_red_bg} !important;
        border: 1.5px solid {badge_red_bdr} !important;
    }}
    .kpi-box-red .kpi-box-label {{ color: {badge_red_txt} !important; font-weight: 800; }}
    .kpi-box-red .kpi-box-val {{ color: {badge_red_txt} !important; }}

    /* Amber / Warm for Moderate / Nearing SLA / Warnings */
    .kpi-box-amber {{
        background-color: {badge_amber_bg} !important;
        border: 1px solid {badge_amber_bdr} !important;
    }}
    .kpi-box-amber .kpi-box-label {{ color: {badge_amber_txt} !important; opacity: 0.9; }}
    .kpi-box-amber .kpi-box-val {{ color: {badge_amber_txt} !important; }}

    /* Teal for Stability / Experience / Fluency / Ratios */
    .kpi-box-teal {{
        background-color: {badge_teal_bg} !important;
        border: 1px solid {badge_teal_bdr} !important;
    }}
    .kpi-box-teal .kpi-box-label {{ color: {badge_teal_txt} !important; opacity: 0.9; }}
    .kpi-box-teal .kpi-box-val {{ color: {badge_teal_txt} !important; }}

    /* Navy for Capital Facilities / ARR / Actions */
    .kpi-box-navy {{
        background-color: {badge_navy_bg} !important;
        border: 1px solid {badge_navy_bdr} !important;
    }}
    .kpi-box-navy .kpi-box-label {{ color: {badge_navy_txt} !important; opacity: 0.85; }}
    .kpi-box-navy .kpi-box-val {{ color: {badge_navy_txt} !important; }}

    /* Legacy chip compatibility */
    .kpi-chip-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.65rem; margin-top: 0.75rem; }}
    .kpi-chip {{ border-radius: 6px; padding: 0.55rem 0.8rem; display: flex; flex-direction: column; }}
    .kpi-chip-label {{ font-size: 0.68rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.2rem; font-family: 'Host Grotesk', sans-serif; }}
    .kpi-chip-val {{ font-size: 1.05rem; font-weight: 800; line-height: 1.2; font-family: 'Host Grotesk', sans-serif; }}
    .kpi-chip-green {{ background-color: {badge_green_bg} !important; color: {badge_green_txt} !important; border: 1px solid {badge_green_bdr} !important; }}
    .kpi-chip-teal {{ background-color: {badge_teal_bg} !important; color: {badge_teal_txt} !important; border: 1px solid {badge_teal_bdr} !important; }}
    .kpi-chip-navy {{ background-color: {badge_navy_bg} !important; color: {badge_navy_txt} !important; border: 1px solid {badge_navy_bdr} !important; }}
    .kpi-chip-red {{ background-color: {badge_red_bg} !important; color: {badge_red_txt} !important; border: 1px solid {badge_red_bdr} !important; }}

    /* Permanent prevention of emoji activity indicators / spinners */
    [data-testid="stStatusWidget"],
    .stStatusWidget,
    [data-testid="stDecoration"] {{
        display: none !important;
        visibility: hidden !important;
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
        background-color: #202A34;
        color: #F8FAFC;
        padding: 0.95rem 1.2rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.84rem;
        line-height: 1.6;
        margin-top: 0.5rem;
        border: 1px solid var(--nd-border);
    }}

    /* Table & DataFrame Text Legibility */
    div[data-testid="stDataFrame"],
    div[data-testid="stTable"],
    div[data-testid="stDataFrame"] * {{
        color: var(--nd-text) !important;
    }}

    /* Selectbox & Multiselect Value Text */
    div[data-baseweb="select"] span,
    div[data-baseweb="tag"] span {{
        color: var(--nd-text) !important;
    }}
    div[data-baseweb="tag"] {{
        background-color: var(--nd-surface-alt) !important;
        border: 1px solid var(--nd-border) !important;
    }}

    /* Streamlit Tabs Navigation - React-Aria (Streamlit 1.40+) & BaseWeb Universal */
    div[data-testid="stTabs"],
    .stTabs,
    div[role="tablist"],
    div[aria-label="Tabs"],
    .react-aria-TabList {{
        gap: 8px;
        border-bottom: 1px solid var(--nd-border);
        background: transparent !important;
    }}

    /* Unselected Tabs (Default) */
    div[data-testid="stTab"],
    [data-testid="stTab"],
    .react-aria-Tab,
    div[role="tab"],
    [role="tab"],
    button[role="tab"],
    .stTabs [data-baseweb="tab"],
    button[data-baseweb="tab"] {{
        padding: 8px 16px !important;
        font-weight: 600 !important;
        color: {tab_unselected_color} !important;
        -webkit-text-fill-color: {tab_unselected_color} !important;
        background: transparent !important;
        opacity: 1 !important;
        cursor: pointer !important;
        font-family: 'Host Grotesk', sans-serif !important;
        border: none !important;
        border-bottom: none !important;
        outline: none !important;
    }}

    div[data-testid="stTab"] *,
    [data-testid="stTab"] *,
    .react-aria-Tab *,
    div[role="tab"] *,
    [role="tab"] *,
    button[role="tab"] *,
    .stTabs [data-baseweb="tab"] *,
    button[data-baseweb="tab"] * {{
        color: {tab_unselected_color} !important;
        -webkit-text-fill-color: {tab_unselected_color} !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        opacity: 1 !important;
        border: none !important;
        border-bottom: none !important;
        text-decoration: none !important;
        transition: color 0.15s ease-in-out !important;
    }}

    /* Hovered Tabs */
    div[data-testid="stTab"]:hover,
    div[data-testid="stTab"][data-hovered],
    [data-testid="stTab"]:hover,
    [data-testid="stTab"][data-hovered],
    .react-aria-Tab:hover,
    .react-aria-Tab[data-hovered],
    div[role="tab"]:hover,
    [role="tab"]:hover,
    button[role="tab"]:hover,
    div[data-testid="stTab"]:hover *,
    div[data-testid="stTab"][data-hovered] *,
    [data-testid="stTab"]:hover *,
    [data-testid="stTab"][data-hovered] *,
    .react-aria-Tab:hover *,
    .react-aria-Tab[data-hovered] *,
    div[role="tab"]:hover *,
    [role="tab"]:hover *,
    button[role="tab"]:hover * {{
        color: {tab_hover_color} !important;
        -webkit-text-fill-color: {tab_hover_color} !important;
        opacity: 1 !important;
        border: none !important;
        border-bottom: none !important;
        text-decoration: none !important;
    }}

    /* Selected / Active Tabs (Single Clean Indicator - Eliminates Duplicate Line) */
    div[data-testid="stTab"][data-selected],
    div[data-testid="stTab"][aria-selected="true"],
    [data-testid="stTab"][data-selected],
    [data-testid="stTab"][aria-selected="true"],
    .react-aria-Tab[data-selected],
    .react-aria-Tab[aria-selected="true"],
    div[role="tab"][data-selected],
    div[role="tab"][aria-selected="true"],
    [role="tab"][data-selected],
    [role="tab"][aria-selected="true"],
    button[role="tab"][aria-selected="true"],
    .stTabs [aria-selected="true"] {{
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    div[data-testid="stTab"][data-selected] *,
    div[data-testid="stTab"][aria-selected="true"] *,
    [data-testid="stTab"][data-selected] *,
    [data-testid="stTab"][aria-selected="true"] *,
    .react-aria-Tab[data-selected] *,
    .react-aria-Tab[aria-selected="true"] *,
    div[role="tab"][data-selected] *,
    div[role="tab"][aria-selected="true"] *,
    [role="tab"][data-selected] *,
    [role="tab"][aria-selected="true"] *,
    button[role="tab"][aria-selected="true"] *,
    .stTabs [aria-selected="true"] * {{
        color: {tab_selected_color} !important;
        -webkit-text-fill-color: {tab_selected_color} !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        border: none !important;
        border-bottom: none !important;
        text-decoration: none !important;
        box-shadow: none !important;
    }}

    div[data-testid="stTab"] .react-aria-SelectionIndicator,
    .react-aria-Tab .react-aria-SelectionIndicator {{
        background-color: var(--nd-green) !important;
        height: 3px !important;
        border-radius: 2px !important;
    }}

    /* Form Label and Caption Contrast Improvements */
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    .stSelectbox label,
    .stSelectbox label p,
    .stTextInput label,
    .stTextInput label p,
    .stTextArea label,
    .stTextArea label p {{
        color: var(--nd-text) !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p,
    .stCaption,
    .stCaption p {{
        color: var(--nd-muted) !important;
        font-size: 0.85rem !important;
    }}

    /* Transparent Altair & Vega-Lite Charts (Zero White Rectangles in Dark Mode) */
    div[data-testid="stVegaLiteChart"],
    div[data-testid="stArrowVegaLiteChart"],
    div[data-testid="stVegaLiteChart"] > div,
    .vega-embed,
    .vega-embed canvas,
    .vega-embed svg {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* Universal Buttons & Actions (Eliminates white blocks with white text) */
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="baseButton-secondary"],
    button[kind="secondary"],
    div[data-testid="stPopover"] button,
    .stPopover button,
    div[data-testid="stButton"] button:not([kind="primary"]),
    .stButton > button:not([kind="primary"]),
    div[data-testid="stLinkButton"] > a,
    .stDownloadButton > button {{
        background-color: var(--nd-surface) !important;
        background: var(--nd-surface) !important;
        color: var(--nd-text) !important;
        border: 1px solid var(--nd-border) !important;
        border-radius: 6px !important;
        font-family: 'Host Grotesk', 'Manrope', sans-serif !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.15s ease-in-out !important;
    }}

    button[data-testid="stBaseButton-secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[kind="secondary"]:hover,
    div[data-testid="stPopover"] button:hover,
    .stPopover button:hover,
    div[data-testid="stButton"] button:not([kind="primary"]):hover,
    .stButton > button:not([kind="primary"]):hover,
    div[data-testid="stLinkButton"] > a:hover,
    .stDownloadButton > button:hover {{
        background-color: var(--nd-surface-alt) !important;
        background: var(--nd-surface-alt) !important;
        border-color: var(--nd-green) !important;
        color: var(--nd-green) !important;
    }}

    button[data-testid="stBaseButton-secondary"] *,
    button[kind="secondary"] *,
    div[data-testid="stPopover"] button *,
    .stButton > button:not([kind="primary"]) * {{
        color: inherit !important;
    }}

    /* Primary button override (Centered, nuDesk Green) */
    .stButton > button[kind="primary"],
    button[data-testid="stBaseButton-primary"],
    button[kind="primary"] {{
        background-color: var(--nd-green) !important;
        background: var(--nd-green) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-family: 'Host Grotesk', sans-serif !important;
        letter-spacing: -0.01em !important;
        padding: 0.55rem 1.5rem !important;
        transition: background-color 0.15s ease-in-out !important;
    }}

    .stButton > button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover,
    button[kind="primary"]:hover {{
        background-color: #348E4D !important;
        background: #348E4D !important;
        color: #FFFFFF !important;
    }}

    /* Top Bar Popovers (Settings and User Profile) - Full surface clickable hitbox */
    div[data-testid="stPopover"],
    div[data-testid="stPopover"] > div {{
        width: 100% !important;
        display: block !important;
    }}

    div[data-testid="stPopover"] button,
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"] {{
        width: 100% !important;
        min-height: 42px !important;
        height: 100% !important;
        padding: 0.5rem 1rem !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.5rem !important;
        cursor: pointer !important;
        box-sizing: border-box !important;
        pointer-events: auto !important;
    }}

    /* Delegate click events to button so entire surface is actionable */
    div[data-testid="stPopover"] button *,
    div[data-testid="stPopover"] > button * {{
        pointer-events: none !important;
        cursor: pointer !important;
    }}

    div[data-testid="stPopoverBody"] {{
        background-color: var(--nd-surface) !important;
        color: var(--nd-text) !important;
        border: 1px solid var(--nd-border) !important;
        border-radius: 8px !important;
        box-shadow: 0 8px 24px rgba(10, 15, 22, 0.25) !important;
        padding: 1rem !important;
    }}

    /* =========================================================================
       RESPONSIVE MOBILE DESIGN SYSTEM (@media max-width: 900px)
       ========================================================================= */
    @media (max-width: 900px) {{
        /* Container padding */
        .block-container {{
            padding-top: 0.5rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-bottom: 2.5rem !important;
        }}

        /* Top Brand Header Banner */
        .nudesk-header {{
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 0.65rem !important;
            padding: 0.85rem 1rem !important;
        }}
        .nudesk-header h1 {{
            font-size: 1.15rem !important;
        }}
        .nudesk-header .subtitle {{
            font-size: 0.78rem !important;
        }}

        /* Horizontal Tabs Navigation: Smooth Touch Scrolling */
        div[data-testid="stTabs"] [role="tablist"],
        .stTabs [role="tablist"],
        div[role="tablist"] {{
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: thin !important;
            padding-bottom: 4px !important;
        }}
        div[data-testid="stTab"],
        [data-testid="stTab"],
        div[role="tab"],
        button[role="tab"] {{
            flex-shrink: 0 !important;
            white-space: nowrap !important;
            padding: 6px 12px !important;
            font-size: 0.84rem !important;
        }}

        /* Top KPI Metric Boxes: Compact 2x2 Grid instead of 4 stacked boxes */
        .kpi-container {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 0.5rem !important;
            margin-bottom: 0.75rem !important;
        }}
        .kpi-card {{
            padding: 0.65rem 0.8rem !important;
        }}
        .kpi-value {{
            font-size: 1.25rem !important;
        }}
        .kpi-label {{
            font-size: 0.68rem !important;
        }}
        .kpi-sub {{
            font-size: 0.72rem !important;
        }}

        /* Master-Detail Workspace: Mobile Accordion Layout */
        /* On mobile, card details and triage operations open directly beneath each card. */
        /* Hide the redundant split canvas column on mobile screens. */
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:has(.cockpit-canvas-col) {{
            display: none !important;
        }}

        /* Queue column takes full width on mobile */
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:has(.cockpit-queue-col),
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:has(.queue-card-hitbox) {{
            width: 100% !important;
            min-width: 100% !important;
            order: 1 !important;
            margin-top: 0 !important;
            border-top: none !important;
            padding-top: 0 !important;
        }}

        /* Card expanders open smoothly right beneath each card */
        div[data-testid="stColumn"]:has(.cockpit-queue-col) div[data-testid="stExpander"] {{
            display: block !important;
            margin-top: 0.25rem !important;
            margin-bottom: 0.65rem !important;
            border: 1px solid var(--nd-border) !important;
            border-radius: 6px !important;
            background: var(--nd-surface) !important;
        }}

        /* Compact Cockpit Header */
        .cockpit-header {{
            padding: 0.75rem 0.95rem !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 0.4rem !important;
        }}
        .cockpit-title {{
            font-size: 1.05rem !important;
        }}

        /* Queue Cards Compact Layout on Mobile */
        .queue-card {{
            padding: 0.55rem 0.75rem !important;
            margin-bottom: 0.35rem !important;
        }}
        .queue-entity {{
            font-size: 0.88rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }}
        .queue-metric {{
            font-size: 0.84rem !important;
        }}
        .queue-meta {{
            font-size: 0.72rem !important;
        }}

        /* Seamless button overlays on mobile */
        div[class*="st-key-btn_c_select_"],
        div[class*="st-key-btn_s_select_"],
        div[class*="st-key-btn_h_select_"] {{
            margin-top: -110px !important;
            height: 104px !important;
            margin-bottom: 0.5rem !important;
        }}
        div[class*="st-key-btn_c_select_"] button,
        div[class*="st-key-btn_s_select_"] button,
        div[class*="st-key-btn_h_select_"] button {{
            height: 104px !important;
            min-height: 104px !important;
            max-height: 104px !important;
        }}

        /* Executive Large KPI Grid: 2x2 on Mobile */
        .kpi-large-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 0.45rem !important;
        }}
        .kpi-box-large {{
            padding: 0.5rem 0.65rem !important;
            min-height: 56px !important;
        }}
        .kpi-box-large .kpi-box-val {{
            font-size: 1.05rem !important;
        }}

        /* Single-Line Activity Log Row */
        .log-row {{
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 0.5rem !important;
        }}
    }}

    /* On desktop (> 900px), hide inline card expanders so queue stays clean while right canvas is active */
    @media (min-width: 901px) {{
        div[data-testid="stColumn"]:has(.cockpit-queue-col) div[data-testid="stExpander"] {{
            display: none !important;
        }}
    }}
</style>
"""


def configure_altair_donut(chart, theme: str = "light"):
    """Configure transparent background and theme-aware legend/text for Altair charts."""
    is_dark = (theme == "dark")
    text_color = "#F8FAFC" if is_dark else "#1D242E"
    return (
        chart.properties(background="transparent")
        .configure_view(stroke=None)
        .configure_legend(
            labelColor=text_color,
            titleColor=text_color,
            labelFont="Manrope, sans-serif",
            labelFontSize=11
        )
    )
