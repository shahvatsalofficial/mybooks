"""
Production Chart De-Rendering Pipeline
Converts visual line/bar charts into structured Pandas-compatible JSON.
Author: Vatsal Shah, Enterprise AI Architect
"""
from pydantic import BaseModel, Field
from typing import List, Dict
from openai import OpenAI

client = OpenAI()

class DataPoint(BaseModel):
    x_value: str = Field(description="Category or timestamp along the X-axis.")
    y_value: float = Field(description="Calculated numeric value along the Y-axis.")

class ChartSeries(BaseModel):
    series_name: str = Field(description="Legend label of the data series.")
    data_points: List[DataPoint] = Field(description="Reconstructed coordinate points.")

class DeRenderedChart(BaseModel):
    chart_title: str = Field(description="Title text of the chart.")
    x_axis_label: str = Field(description="Label and units of the X-axis.")
    y_axis_label: str = Field(description="Label and units of the Y-axis.")
    series: List[ChartSeries] = Field(description="Extracted data series arrays.")

def derender_visual_chart(image_b64: str) -> DeRenderedChart:
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert computational visual chart de-rendering engine. "
                    "Analyze the visual plot, determine exact numerical axis calibrations, "
                    "and reverse-engineer the underlying data series into structured JSON."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all numerical data series from this chart."},
                    {"type": "image_url", {"url": "data:image/jpeg;base64," + image_b64, "detail": "high"}}
                ]
            }
        ],
        response_format=DeRenderedChart,
        temperature=0.0
    )
    return completion.choices[0].message.parsed
