"""SongMatch brand colors shared by the lab's charts."""
PURPLE = "#A78BFA"
FUCHSIA = "#E879F9"
METHOD_COLORS = {"Random": "#8B849C", "Genre match": "#7C3AED", "Musical features": PURPLE}

def style_chart(figure):
    figure.update_layout(
        template="plotly_dark",
        font=dict(color="#EDE9FE",family="Arial, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#C4B5FD")),
        hoverlabel=dict(bgcolor="#1F1F28",bordercolor="#A78BFA",font=dict(color="#FFFFFF")),
    )
    figure.update_xaxes(showgrid=False,zeroline=False,color="#C4B5FD")
    figure.update_yaxes(gridcolor="rgba(167,139,250,0.14)",zeroline=False,color="#C4B5FD")
    return figure
