# -*- coding: utf-8 -*-
# Compact, recognizable inline SVG flags (18x12 viewBox) for the 10 countries present
# in this dataset. Simplified (no emblems/seals) but color-accurate, so they render
# identically on every platform instead of relying on the OS's emoji font (Windows
# shows flag emoji as plain "US"/"MX" letter codes, not pictures).

FLAGS = {}

def svg(inner):
    return f'<svg class="flag-svg" viewBox="0 0 18 12" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'

# USA: simplified stripes + blue canton
FLAGS['US'] = svg(
    '<rect width="18" height="12" fill="#B22234"/>'
    '<rect y="0.92" width="18" height="0.92" fill="#fff"/>'
    '<rect y="2.77" width="18" height="0.92" fill="#fff"/>'
    '<rect y="4.62" width="18" height="0.92" fill="#fff"/>'
    '<rect y="6.46" width="18" height="0.92" fill="#fff"/>'
    '<rect y="8.31" width="18" height="0.92" fill="#fff"/>'
    '<rect y="10.15" width="18" height="0.92" fill="#fff"/>'
    '<rect width="8" height="6.46" fill="#3C3B6E"/>'
)

# Mexico: vertical green/white/red
FLAGS['MX'] = svg(
    '<rect width="6" height="12" fill="#006847"/>'
    '<rect x="6" width="6" height="12" fill="#fff"/>'
    '<rect x="12" width="6" height="12" fill="#CE1126"/>'
)

# Dominican Republic: white cross, blue/red quadrants
FLAGS['DO'] = svg(
    '<rect width="18" height="12" fill="#002D62"/>'
    '<rect x="7" width="4" height="12" fill="#fff"/>'
    '<rect y="4" width="18" height="4" fill="#fff"/>'
    '<rect width="7" height="4" fill="#CE1126"/>'
    '<rect x="11" width="7" height="4" fill="#002D62"/>'
    '<rect y="8" width="7" height="4" fill="#002D62"/>'
    '<rect x="11" y="8" width="7" height="4" fill="#CE1126"/>'
)

# Venezuela: yellow/blue/red horizontal tricolor
FLAGS['VE'] = svg(
    '<rect width="18" height="4" fill="#FFCC00"/>'
    '<rect y="4" width="18" height="4" fill="#00247D"/>'
    '<rect y="8" width="18" height="4" fill="#CF142B"/>'
)

# Puerto Rico: red/white stripes + blue triangle + white star (simplified)
FLAGS['PR'] = svg(
    '<rect width="18" height="12" fill="#fff"/>'
    '<rect y="0" width="18" height="2.4" fill="#ED1C24"/>'
    '<rect y="4.8" width="18" height="2.4" fill="#ED1C24"/>'
    '<rect y="9.6" width="18" height="2.4" fill="#ED1C24"/>'
    '<polygon points="0,0 0,12 8,6" fill="#0050F0"/>'
    '<polygon points="3.4,6 4.1,4.1 4.9,6 4.1,7.9" fill="#fff"/>'
)

# Cuba: blue/white stripes + red triangle + white star (simplified)
FLAGS['CU'] = svg(
    '<rect width="18" height="12" fill="#fff"/>'
    '<rect y="0" width="18" height="2.4" fill="#002A8F"/>'
    '<rect y="4.8" width="18" height="2.4" fill="#002A8F"/>'
    '<rect y="9.6" width="18" height="2.4" fill="#002A8F"/>'
    '<polygon points="0,0 0,12 7,6" fill="#CF142B"/>'
    '<polygon points="2.6,6 3.3,4.1 4.1,6 3.3,7.9" fill="#fff"/>'
)

# Colombia: yellow (half) / blue / red
FLAGS['CO'] = svg(
    '<rect width="18" height="6" fill="#FCD116"/>'
    '<rect y="6" width="18" height="3" fill="#003893"/>'
    '<rect y="9" width="18" height="3" fill="#CE1126"/>'
)

# Nicaragua: blue/white/blue horizontal
FLAGS['NI'] = svg(
    '<rect width="18" height="4" fill="#0067C6"/>'
    '<rect y="4" width="18" height="4" fill="#fff"/>'
    '<rect y="8" width="18" height="4" fill="#0067C6"/>'
)

# Panama: quartered white/blue/red (simplified, no stars)
FLAGS['PA'] = svg(
    '<rect width="18" height="12" fill="#fff"/>'
    '<rect width="9" height="6" fill="#fff"/>'
    '<rect x="9" width="9" height="6" fill="#DA121A"/>'
    '<rect y="6" width="9" height="6" fill="#0033A0"/>'
    '<rect x="9" y="6" width="9" height="6" fill="#fff"/>'
)

# Canada: red/white/red vertical, simplified leaf as a small red diamond
FLAGS['CA'] = svg(
    '<rect width="18" height="12" fill="#fff"/>'
    '<rect width="4.5" height="12" fill="#FF0000"/>'
    '<rect x="13.5" width="4.5" height="12" fill="#FF0000"/>'
    '<polygon points="9,3 10,6 9,5.3 8,6" fill="#FF0000"/>'
    '<rect x="8.6" y="6" width="0.8" height="3" fill="#FF0000"/>'
)

print(len(FLAGS), "flags defined:", sorted(FLAGS.keys()))
