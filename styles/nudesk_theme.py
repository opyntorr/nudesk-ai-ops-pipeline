"""
nuDesk MX Design System & Styling Tokens
Derived directly from https://nudesk.ai design tokens:
- Primary / Soft Navy: #2C3E50 / #1E293B
- Heritage Green / Accent: #3EA258 / #44B36C
- Background: #FAFAFA / #F8FAFC
- Foreground: #1D242E
- Radius: 4px
"""

def get_nudesk_css() -> str:
    return """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --nudesk-navy: #2C3E50;
        --nudesk-navy-dark: #1E293B;
        --nudesk-green: #3EA258;
        --nudesk-green-light: #E8F5E9;
        --nudesk-bg: #FAFAFA;
        --nudesk-card-bg: #FFFFFF;
        --nudesk-border: #E2E8F0;
        --nudesk-text: #1D242E;
        --nudesk-text-muted: #64748B;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--nudesk-text);
    }

    /* Streamlit top header bar minimization */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 2.5rem;
    }

    /* Main container padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* Brand Header Banner */
    .nudesk-header {
        background: linear-gradient(135deg, #1E293B 0%, #2C3E50 100%);
        border-radius: 6px;
        padding: 1.25rem 1.75rem;
        color: #FFFFFF;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px -4px rgba(30, 41, 59, 0.2);
    }

    .nudesk-header h1 {
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }

    .nudesk-header .subtitle {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-top: 0.2rem;
    }

    .nudesk-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.65rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .badge-green {
        background-color: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #C8E6C9;
    }

    .badge-amber {
        background-color: #FEF3C7;
        color: #B45309;
        border: 1px solid #FDE68A;
    }

    .badge-red {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }

    .badge-navy {
        background-color: #F1F5F9;
        color: #1E293B;
        border: 1px solid #E2E8F0;
    }

    /* Studio Card */
    .studio-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .studio-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #F1F5F9;
    }

    .studio-card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1E293B;
        margin: 0;
    }

    /* KPI Metric Box */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 1.25rem;
    }

    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1rem 1.25rem;
        border-left: 4px solid var(--nudesk-green);
    }

    .kpi-label {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.04em;
    }

    .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1E293B;
        margin-top: 0.25rem;
        line-height: 1.2;
    }

    .kpi-sub {
        font-size: 0.8rem;
        color: #10B981;
        margin-top: 0.2rem;
        font-weight: 500;
    }

    /* Clean Bullet items */
    .bullet-item {
        display: flex;
        align-items: flex-start;
        padding: 0.4rem 0;
        border-bottom: 1px dashed #F1F5F9;
    }

    .bullet-item:last-child {
        border-bottom: none;
    }

    .bullet-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: var(--nudesk-green);
        margin-top: 0.55rem;
        margin-right: 0.65rem;
        flex-shrink: 0;
    }

    .bullet-text {
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.5;
    }

    /* Red flag indicator */
    .flag-item {
        background-color: #FEF2F2;
        border-left: 3px solid #EF4444;
        padding: 0.6rem 0.9rem;
        border-radius: 0 4px 4px 0;
        margin-bottom: 0.5rem;
        font-size: 0.88rem;
        color: #991B1B;
    }

    /* Task Item */
    .task-item {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .task-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #1E293B;
    }

    .task-assignee {
        font-size: 0.78rem;
        color: #64748B;
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        padding: 0.15rem 0.45rem;
        border-radius: 3px;
    }

    /* Role Banner */
    .role-banner {
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        font-size: 0.85rem;
    }

    .role-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        color: #1E293B;
    }

    .role-avatar {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: var(--nudesk-navy);
        color: #FFFFFF;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
    }

    /* Code & Script Box */
    .script-box {
        background-color: #0F172A;
        color: #F8FAFC;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        margin-top: 0.5rem;
        border: 1px solid #1E293B;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .nudesk-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
        .kpi-container {
            grid-template-columns: 1fr;
        }
    }
</style>
"""
