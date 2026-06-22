import streamlit as st

def inject_custom_css():
    """
    Injects custom CSS to style the Streamlit app with modern typography, 
    glassmorphism cards, and refined UI elements.
    """
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Force Font Family globally */
    html, body, [class*="css"], .stMarkdown, .stText, button {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Force main block container to take full width */
    .block-container, [data-testid="stMainBlockContainer"] {
        max-width: 95% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Force chat messages and chat input container to take full width */
    [data-testid="stChatMessage"], [data-testid="stChatInput"], .stChatMessage, .stChatInput {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Global Page Styling overrides */
    .reportview-container {
        background: #0f111a;
    }
    
    /* Glassmorphism Metric Cards */
    .kpi-card {
        background: rgba(25, 30, 48, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        margin-bottom: 20px;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(0, 212, 255, 0.4);
        box-shadow: 0 12px 40px 0 rgba(0, 212, 255, 0.15);
    }
    
    .kpi-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #a0aec0;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.1;
        margin: 5px 0;
    }
    
    .kpi-delta {
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 10px;
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        border-radius: 6px;
    }
    
    .delta-positive {
        color: #48bb78;
        background: rgba(72, 187, 120, 0.1);
        border: 1px solid rgba(72, 187, 120, 0.2);
    }
    
    .delta-negative {
        color: #f56565;
        background: rgba(245, 101, 101, 0.1);
        border: 1px solid rgba(245, 101, 101, 0.2);
    }
    
    .delta-neutral {
        color: #a0aec0;
        background: rgba(160, 174, 192, 0.1);
        border: 1px solid rgba(160, 174, 192, 0.2);
    }
    
    /* Premium Title Headers */
    .dashboard-header {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 10px;
    }
    
    /* Subtitle Styling */
    .dashboard-subtitle {
        color: #a0aec0;
        font-size: 1.1rem;
        margin-bottom: 30px;
        font-weight: 300;
    }
    
    /* Table Styling Overrides */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Alert cards custom styles */
    .info-panel {
        background: rgba(0, 114, 255, 0.08);
        border-left: 5px solid #0072ff;
        padding: 15px;
        border-radius: 4px 12px 12px 4px;
        color: #e2e8f0;
        margin-bottom: 20px;
    }

    .success-panel {
        background: rgba(72, 187, 120, 0.08);
        border-left: 5px solid #48bb78;
        padding: 15px;
        border-radius: 4px 12px 12px 4px;
        color: #e2e8f0;
        margin-bottom: 20px;
    }
    
    .warning-panel {
        background: rgba(236, 201, 75, 0.08);
        border-left: 5px solid #ecc94b;
        padding: 15px;
        border-radius: 4px 12px 12px 4px;
        color: #e2e8f0;
        margin-bottom: 20px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_kpi_card(title, value, change=None, change_direction="up", icon="📈"):
    """
    Renders a custom designed glassmorphism KPI card.
    """
    delta_class = "delta-positive" if change_direction == "up" else "delta-negative" if change_direction == "down" else "delta-neutral"
    delta_prefix = "+" if change_direction == "up" else "-" if change_direction == "down" else ""
    
    delta_html = ""
    if change is not None:
        delta_html = f'<div class="kpi-delta {delta_class}">{delta_prefix}{change}</div>'
        
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_panel(message, type="info"):
    """
    Renders custom styled message panels (info, success, warning).
    """
    if type == "success":
        panel_html = f'<div class="success-panel">💡 <b>Insight:</b> {message}</div>'
    elif type == "warning":
        panel_html = f'<div class="warning-panel">⚠️ <b>Warning:</b> {message}</div>'
    else:
        panel_html = f'<div class="info-panel">ℹ️ <b>Analysis:</b> {message}</div>'
        
    st.markdown(panel_html, unsafe_allow_html=True)

def get_plotly_layout(fig, title_text=None, x_title=None, y_title=None, show_legend=True):
    """
    Applies custom styling to a Plotly figure to fit the premium dark/glass theme.
    """
    layout_args = {
        'paper_bgcolor': 'rgba(15, 17, 26, 0.4)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font_family': "Outfit, sans-serif",
        'font_color': "#cbd5e0",
        'showlegend': show_legend,
        'xaxis': {
            'title': x_title,
            'showgrid': True,
            'gridcolor': 'rgba(255, 255, 255, 0.05)',
            'linecolor': 'rgba(255, 255, 255, 0.1)',
            'tickfont': {'size': 12}
        },
        'yaxis': {
            'title': y_title,
            'showgrid': True,
            'gridcolor': 'rgba(255, 255, 255, 0.05)',
            'linecolor': 'rgba(255, 255, 255, 0.1)',
            'tickfont': {'size': 12}
        },
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.2,
            'xanchor': 'center',
            'x': 0.5
        } if show_legend else None,
        'margin': dict(l=40, r=40, t=50, b=40),
        'hoverlabel': dict(
            bgcolor="#1a202c",
            font_size=13,
            font_family="Outfit, sans-serif"
        )
    }
    
    current_title = title_text
    if current_title is None and fig.layout.title:
        if isinstance(fig.layout.title, dict):
            current_title = fig.layout.title.get('text')
        elif hasattr(fig.layout.title, 'text'):
            current_title = fig.layout.title.text
            
    if current_title:
        layout_args['title'] = {
            'text': current_title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16, 'color': '#ffffff', 'family': 'Outfit'}
        }
        
    fig.update_layout(**layout_args)
    return fig
