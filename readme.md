### Install globally @ https://github.com/antvis/mcp-server-chart?tab=readme-ov-file#-run-with-sse-or-streamable-transport
npm install -g @antv/mcp-server-chart



# geenrate image flow
source .venv/bin/activate
uv pip install -r requirements.txt
python agent/flow_image_gen.py

# to run
python agent/main.py


Running on local URL:  http://0.0.0.0:7860


uv add "mcp" httpx

setup:
source .venv/bin/activate
uv pip install -r requirements.txt
uv add "mcp" httpx

mcp tools :
memory
https://github.com/modelcontextprotocol/servers/tree/main/src/memory

tavily search :
https://docs.tavily.com/documentation/mcp

Chart/Graph custom generator: 

documentaion client adapater and custom server (csv_generator)
https://docs.langchain.com/oss/python/langchain/mcp



git add -f database/data-collection/crops_state\ \(1\).csv

