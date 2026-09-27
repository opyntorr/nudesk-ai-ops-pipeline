"""
nuDesk MX Design System & Theme Engine
Supports High-Contrast Minimalist Light Mode (Default) and Enterprise Dark Mode.
Color tokens derived directly from https://nudesk.ai:
- Primary Brand Green: #059669 / #10B981 (Heritage Green)
- Neutral Deep Black/Navy: #0F172A / #1E293B
- Minimalist Pure Surfaces: #FFFFFF / #F8FAFC
- Accent Mint / Emerald: #ECFDF5 / #34D399
- Strict WCAG AAA Contrast Compliance
"""

def get_nudesk_css(theme: str = "light") -> str:
    """Generate dynamic CSS tokens based on selected theme mode."""
    is_dark = (theme == "dark")

    # Dynamic variables
    bg_body = "#0B0F17" if is_dark else "#F8FAFC"
    bg_surface = "#161E2E" if is_dark else "#FFFFFF"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_muted = "#94A3B8" if is_dark else "#475569"
    border_color = "#27354A" if is_dark else "#E2E8F0"
    border_strong = "#334155" if is_dark else "#CBD5E1"
    header_gradient = "linear-gradient(135deg, #0B0F17 0%, #161E2E 100%)" if is_dark else "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)"
    kpi_bg = "#161E2E" if is_dark else "#FFFFFF"
    task_bg = "#1A2333" if is_dark else "#F8FAFC"
    banner_bg = "#161E2E" if is_dark else "#F1F5F9"
    brand_green = "#10B981" if is_dark else "#059669"
    script_bg = "#070B12" if is_dark else "#0F172A"

    badge_green_bg = "#064E3B" if is_dark else "#ECFDF5"
    badge_green_txt = "#6EE7B7" if is_dark else "#065F46"
    badge_green_bdr = "#047857" if is_dark else "#A7F3D0"

    badge_navy_bg = "#1E293B" if is_dark else "#F1F5F9"
    badge_navy_txt = "#E2E8F0" if is_dark else "#0F172A"
    badge_navy_bdr = "#334155" if is_dark else "#CBD5E1"

    badge_amber_bg = "#451A03" if is_dark else "#FFFBEB"
    badge_amber_txt = "#FCD34D" if is_dark else "#92400E"
    badge_amber_bdr = "#B45309" if is_dark else "#FDE68A"

    badge_red_bg = "#450A0A" if is_dark else "#FEF2F2"
    badge_red_txt = "#FCA5A5" if is_dark else "#991B1B"
    badge_red_bdr = "#DC2626" if is_dark else "#FECACA"

    return f"""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        --nd-bg: {bg_body};
        --nd-surface: {bg_surface};
        --nd-text: {text_primary};
        --nd-muted: {text_muted};
        --nd-border: {border_color};
        --nd-border-strong: {border_strong};
        --nd-green: {brand_green};
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--nd-bg) !important;
        color: var(--nd-text) !important;
    }}

    /* Streamlit top header bar */
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
        height: 2.2rem;
    }}

    /* Main container padding */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1240px !important;
    }}

    /* Brand Header Banner */
    .nudesk-header {{
        background: {header_gradient};
        border-radius: 8px;
        padding: 1.25rem 1.75rem;
        color: #FFFFFF;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 20px -4px rgba(15, 23, 42, 0.25);
        border-bottom: 3px solid var(--nd-green);
    }}

    .nudesk-header h1 {{
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
    }}

    .nudesk-header .subtitle {{
        font-size: 0.85rem;
        color: #94A3B8 !important;
        margin-top: 0.25rem;
        font-weight: 500;
    }}

    /* Badges */
    .nudesk-badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.65rem;
        border-radius: 4px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }}

    .badge-green {{
        background-color: {badge_green_bg} !important;
        color: {badge_green_txt} !important;
        border: 1px solid {badge_green_bdr} !important;
    }}

    .badge-amber {{
        background-color: {badge_amber_bg} !important;
        color: {badge_amber_txt} !important;
        border: 1px solid {badge_amber_bdr} !important;
    }}

    .badge-red {{
        background-color: {badge_red_bg} !important;
        color: {badge_red_txt} !important;
        border: 1px solid {badge_red_bdr} !important;
    }}

    .badge-navy {{
        background-color: {badge_navy_bg} !important;
        color: {badge_navy_txt} !important;
        border: 1px solid {badge_navy_bdr} !important;
    }}

    /* Studio Card */
    .studio-card {{
        background-color: var(--nd-surface);
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 1.35rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .studio-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid var(--nd-border);
    }}

    .studio-card-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--nd-text);
        margin: 0;
    }}

    /* KPI Metric Box */
    .kpi-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.25rem;
    }}

    .kpi-card {{
        background: {kpi_bg};
        border: 1px solid var(--nd-border);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        border-left: 4px solid var(--nd-green);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}

    .kpi-label {{
        font-size: 0.75rem;
        color: var(--nd-muted);
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
    }}

    .kpi-value {{
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--nd-text);
        margin-top: 0.25rem;
        line-height: 1.2;
    }}

    .kpi-sub {{
        font-size: 0.8rem;
        color: var(--nd-green);
        margin-top: 0.2rem;
        font-weight: 600;
    }}

    /* Clean Bullet items */
    .bullet-item {{
        display: flex;
        align-items: flex-start;
        padding: 0.45rem 0;
        border-bottom: 1px dashed var(--nd-border);
    }}

    .bullet-item:last-child {{
        border-bottom: none;
    }}

    .bullet-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: var(--nd-green);
        margin-top: 0.55rem;
        margin-right: 0.65rem;
        flex-shrink: 0;
    }}

    .bullet-text {{
        font-size: 0.9rem;
        color: var(--nd-text);
        line-height: 1.5;
    }}

    /* Red flag indicator */
    .flag-item {{
        background-color: {badge_red_bg};
        border-left: 3px solid #EF4444;
        padding: 0.6rem 0.9rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.5rem;
        font-size: 0.88rem;
        color: {badge_red_txt};
        border-top: 1px solid {badge_red_bdr};
        border-bottom: 1px solid {badge_red_bdr};
        border-right: 1px solid {badge_red_bdr};
    }}

    /* Task Item */
    .task-item {{
        background-color: {task_bg};
        border: 1px solid var(--nd-border);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .task-title {{
        font-size: 0.88rem;
        font-weight: 700;
        color: var(--nd-text);
    }}

    .task-assignee {{
        font-size: 0.78rem;
        color: var(--nd-muted);
        background: var(--nd-surface);
        border: 1px solid var(--nd-border-strong);
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-weight: 500;
    }}

    /* Role Banner */
    .role-banner {{
        background-color: {banner_bg};
        border: 1px solid var(--nd-border-strong);
        border-radius: 8px;
        padding: 0.75rem 1.15rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        font-size: 0.88rem;
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
        background-color: #0F172A;
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
        background-color: {script_bg};
        color: #F8FAFC;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        margin-top: 0.5rem;
        border: 1px solid var(--nd-border);
    }}

    /* Google SSO Button Styling */
    .google-signin-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        background-color: #FFFFFF;
        color: #1F2937 !important;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        padding: 0.45rem 0.9rem;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: background-color 0.15s ease-in-out;
    }}

    .google-signin-btn:hover {{
        background-color: #F9FAFB;
        border-color: #9CA3AF;
    }}

    /* Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid var(--nd-border);
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 8px 14px;
        font-weight: 600;
        color: var(--nd-muted);
        border-radius: 6px 6px 0 0;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--nd-text) !important;
        border-bottom: 2px solid var(--nd-green) !important;
    }}

    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .nudesk-header {{
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
        }}
        .kpi-container {{
            grid-template-columns: 1fr;
        }}
    }}
</style>
"""
