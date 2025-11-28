from graphviz import Digraph
import os

def generate_architecture_diagram():
    dot = Digraph(comment='Delivery Tracker System Architecture')
    
    # Professional Research Paper Settings
    dot.attr(dpi='300')
    dot.attr(rankdir='TB')
    dot.attr(size='8,8')   # Larger Square canvas
    dot.attr(ratio='1')    # Force 1:1 aspect ratio
    dot.attr(splines='spline')
    dot.attr(nodesep='0.5')
    dot.attr(ranksep='0.5')
    dot.attr(fontname='Helvetica')
    
    # Color Palette (Professional & Clean)
    colors = {
        'gui': '#E3F2FD',      # Light Blue
        'logic': '#F3E5F5',    # Light Purple
        'ml': '#E8F5E9',       # Light Green
        'data': '#FFF3E0',     # Light Orange
        'ext': '#ECEFF1'       # Light Grey
    }
    
    # Default Node Style
    dot.attr('node', shape='note', style='filled, rounded', fontname='Helvetica', fontsize='10', penwidth='1.5')
    dot.attr('edge', fontname='Helvetica', fontsize='9', color='#455A64', penwidth='1.2')

    # Main Application Flow (Vertical Backbone)
    
    # GUI
    dot.node('GUI', 'GUI / Presentation\n(Tkinter)', fillcolor=colors['gui'], color='#1565C0')

    # Logic / Services
    with dot.subgraph(name='cluster_logic') as c:
        c.attr(label='Core Logic', style='dashed', fontcolor='#6A1B9A')
        c.node('Assignment', 'Assignment Service', fillcolor=colors['logic'], color='#6A1B9A')
        c.node('Routing', 'Routing Engine\n(A* / Dijkstra)', fillcolor=colors['logic'], color='#6A1B9A')

    # ML Components
    with dot.subgraph(name='cluster_ml') as c:
        c.attr(label='AI / ML Module', style='dashed', fontcolor='#2E7D32')
        c.node('ML', 'Predictors\n(Time & Demand)', fillcolor=colors['ml'], color='#2E7D32')

    # Data / Models
    with dot.subgraph(name='cluster_data') as c:
        c.attr(label='Data Layer', style='dashed', fontcolor='#EF6C00')
        c.node('Graph', 'Graph Network', fillcolor=colors['data'], color='#EF6C00')
        c.node('Entities', 'Entities\n(Drivers/Orders)', fillcolor=colors['data'], color='#EF6C00')

    # External / Utils
    dot.node('Ext', 'External Services\n(OSM / Maps)', shape='component', fillcolor=colors['ext'], color='#455A64')

    # Edges - Enforce vertical flow
    dot.edge('GUI', 'Assignment')
    dot.edge('GUI', 'Routing')
    dot.edge('GUI', 'ML')
    
    dot.edge('Assignment', 'Entities')
    dot.edge('Routing', 'Graph')
    
    dot.edge('ML', 'Graph', style='dashed', label='features')
    
    dot.edge('GUI', 'Ext', style='dotted')

    # Output
    output_path = 'system_architecture'
    dot.render(output_path, view=False, format='png')
    print(f"Architecture diagram generated: {os.path.abspath(output_path + '.png')}")

if __name__ == '__main__':
    try:
        generate_architecture_diagram()
    except ImportError:
        print("Error: graphviz library is not installed.")
        print("Please install it using: pip install graphviz")
        print("Note: You also need to have Graphviz installed on your system and in your PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")
