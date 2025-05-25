# Data Visualization with Python Tutorial

## Introduction
Data visualization is the graphical representation of information and data. It helps users understand complex data patterns, trends, and insights through visual elements. This tutorial covers popular Python libraries for creating effective visualizations.

## Getting Started with Matplotlib

### Basic Line Plot
```python
import matplotlib.pyplot as plt
import numpy as np

# Create data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('Simple Sine Wave')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.grid(True)
plt.show()
```

### Bar Chart Example
```python
categories = ['A', 'B', 'C', 'D']
values = [4, 7, 2, 10]

plt.bar(categories, values)
plt.title('Simple Bar Chart')
plt.show()
```

## Advanced Visualizations with Seaborn

Seaborn is built on top of Matplotlib and provides a higher-level interface for drawing attractive statistical graphics.

```python
import seaborn as sns
import pandas as pd

# Load a sample dataset
tips = sns.load_dataset('tips')

# Create a scatter plot with regression line
plt.figure(figsize=(10, 6))
sns.regplot(x='total_bill', y='tip', data=tips)
plt.title('Relationship between Bill Amount and Tip')
plt.show()
```

## Interactive Visualizations with Plotly

Plotly allows you to create interactive plots that can be embedded in web applications.

```python
import plotly.express as px
import plotly.graph_objects as go

# Create a scatter plot
fig = px.scatter(tips, x='total_bill', y='tip', color='day', 
                size='size', hover_data=['sex', 'time'])
fig.update_layout(title='Interactive Scatter Plot')
fig.show()
```

## Dashboard Creation with Dash

Dash is a Python framework for building analytical web applications without JavaScript.

```python
from dash import Dash, dcc, html
import plotly.express as px

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard Example"),
    dcc.Graph(
        id='example-graph',
        figure=px.scatter(tips, x="total_bill", y="tip", color="day")
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
```

## Best Practices for Data Visualization

1. **Choose the right visualization type** for your data and message
2. **Simplify** - avoid chart junk and unnecessary decorations
3. **Use color effectively** - be consistent and consider accessibility
4. **Label clearly** - include descriptive titles, axis labels, and legends
5. **Tell a story** - guide the viewer through the insights in your data

## Resources for Further Learning

- Official documentation for [Matplotlib](https://matplotlib.org/), [Seaborn](https://seaborn.pydata.org/), and [Plotly](https://plotly.com/python/)
- [Python Graph Gallery](https://python-graph-gallery.com/) for visualization inspiration
- [Data Visualization Society](https://www.datavisualizationsociety.org/) for community resources