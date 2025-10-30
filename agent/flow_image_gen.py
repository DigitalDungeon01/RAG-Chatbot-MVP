import asyncio
from graph import create_graph

async def generate_flow_image(output_path="agent/img/graph_flow.png"):
    try:
        print("Creating graph...")
        graph = await create_graph()  # Add await here
        
        print("Generating flow diagram image...")
        png_data = graph.get_graph().draw_mermaid_png()
        
        with open(output_path, "wb") as f:
            f.write(png_data)
        
        print(f"Flow diagram saved to {output_path}")
    except Exception as e:
        print(f"Error generating image: {e}")

if __name__ == "__main__":
    asyncio.run(generate_flow_image())  # Run async function properly