from pydantic import BaseModel, Field
from typing import  List

class EvaluationSchema(BaseModel):
    confidence_score: float = Field(description="Confidence score 0.0-1.0 based on retrieved data quality")
    feedback: str = Field(description="Feedback for answer improvement if needs_improvement is True")
      

class AnswerGenerationSchema(BaseModel):
    answer: str = Field(description="Final response text to user. Include data tables when CSV/chart flags are True.")
    csv_export_required: bool = Field(default=False, 
        description="TRUE when user requests CSV export AND relevant data exists in retrieved_docs. FALSE otherwise or when csv_output_results is present.")
    chart_image_required: bool = Field(default=False, 
        description="TRUE when user requests chart/visualization AND relevant data exists in retrieved_docs. FALSE otherwise or when chart_output_results is present.")
    online_search_required: bool = Field(
        default=False, 
        description="TRUE when: (1) data insufficient/irrelevant AND asking user to confirm search, OR (2) user confirms search with yes/ok/sure. FALSE when search_results is present.")
    
# for chart generator node schema mcp
class ChartDataset(BaseModel):
    label: str = Field(description="Dataset label")
    data: List[float] = Field(description="Data values")

class ChartConfig(BaseModel):
    chart_url: str = Field(description="Chart URL of the chart image, URL in HTML hyperlink")
    chart_type: str = Field(description="Chart type: bar, line, pie, doughnut")
    labels: List[str] = Field(description="X-axis labels")
    datasets: List[ChartDataset] = Field(description="List of datasets") # pass the data ChartDataset schema here
    title: str = Field(description="Chart title")   

# tavily search node schema mcp    
class OnlineSearchResult(BaseModel):
    title: str = Field(description="Title of the search")
    url: str = Field(description="URL of the search")
    content: str = Field(description="Content of the search or snippet of the search or summary of the search")
    source_type: str = Field(description="Source type: website, blog, news, etc.")
    
class TavilySearchSchema(BaseModel):
    tavily_results: List[OnlineSearchResult] = Field(description="List of results from Tavily search")


# CSV export node schema mcp
class CsvExportResult(BaseModel):
    filename: str = Field(description="Filename of the CSV export created/generated")

class GuardRailSchemaMessages(BaseModel):
    safety_flag_messages: bool = Field(default=False, description="Flag: TRUE = violating guidelines, FALSE =  within guidelines and safe")
    
class GuardRailSchemaAnswer(BaseModel):
    safety_flag_answer: bool = Field(default=False, description="Flag: TRUE = violating guidelines, FALSE =  within guidelines and safe")
    
#setelkan scehama file untuk guard rail answer, csv
#setelkan nodes chart, csv, save past context
#setelkan nak simpan past context dekat  ConversationEntry state. and untuk generate id dan timestamp, sebab benda tu simpan as session state memory, so camne nak save state gna pydantic lain tu  haaa.
#setelkan logic graph
#setelkan main file
# setelekan camna nak save 
 
class HallucinationResult(BaseModel):
    hallucination_score: float = Field(description="Confidence score 0.0-1.0 on how well the answer aligns with data (1.0 = fully factual)")
   