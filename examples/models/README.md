# AI Model Strengths Plotting Library

A Python library for visualizing and comparing AI model strengths across different tasks, based on the GitHub Copilot AI model documentation.

## Features

- **Comprehensive Heatmap**: Compare all models across all task categories
- **Task-Specific Rankings**: Show top models for specific tasks
- **Radar Charts**: Multi-dimensional capability visualization
- **Custom Data Support**: Use your own model performance data
- **Export Options**: Save plots as high-quality PNG files

## Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install required dependencies
pip install matplotlib seaborn pandas numpy
```

## Quick Start

```python
from examples.models.plot import plot_model_strengths, compare_models_by_task, plot_model_radar

# Create a heatmap of all model strengths
plot_model_strengths()

# Compare top models for a specific task
compare_models_by_task("Complex Reasoning")

# Create a radar chart for specific models
plot_model_radar(["o3", "GPT-4.5", "Claude 3.7 Sonnet"])
```

## API Reference

### `plot_model_strengths()`

Creates a comprehensive heatmap showing all models and their strengths across different tasks.

**Parameters:**
- `model_data` (Optional[Dict]): Custom model data. Uses default GitHub Copilot data if None.
- `tasks` (Optional[List[str]]): List of tasks to include. Uses all tasks if None.
- `models` (Optional[List[str]]): List of models to include. Uses all models if None.
- `save_path` (Optional[str]): Path to save the plot as PNG.
- `figsize` (tuple): Figure size as (width, height). Default: (14, 10).
- `title` (str): Plot title.

### `compare_models_by_task()`

Creates a bar chart comparing the top models for a specific task.

**Parameters:**
- `task` (str): The task to compare models for.
- `model_data` (Optional[Dict]): Custom model data.
- `top_n` (int): Number of top models to show. Default: 5.
- `save_path` (Optional[str]): Path to save the plot.

### `plot_model_radar()`

Creates a radar chart showing multi-dimensional capabilities of selected models.

**Parameters:**
- `models` (Union[str, List[str]]): Model name(s) to include.
- `model_data` (Optional[Dict]): Custom model data.
- `save_path` (Optional[str]): Path to save the plot.

## Model Categories

The library includes data for the following AI models from GitHub Copilot, organized into functional categories:

### Model Families

- **GPT Models**: GPT-4.1, GPT-4o, GPT-4.5
- **OpenAI o-series**: o1, o3, o3-mini, o4-mini
- **Claude Models**: Claude 3.5 Sonnet, Claude 3.7 Sonnet, Claude Sonnet 4, Claude Opus 4
- **Gemini Models**: Gemini 2.0 Flash, Gemini 2.5 Pro

### Functional Model Categories

Our demo script organizes models into these practical categories based on their documented strengths:

#### **Reasoning Models** 
*For deep logical reasoning and complex problem-solving*
- **Models**: o3, o1, Claude 3.7 Sonnet, GPT-4.5
- **Best for**: Multi-step algorithmic problems, debugging complex issues, performance optimization, architectural decisions
- **Key strengths**: Step-by-step analysis, identifying non-obvious improvements, handling complex logic chains

#### **Fast Response Models**
*For quick, efficient answers to common development tasks*
- **Models**: GPT-4.1, o4-mini, o3-mini, Claude 3.5 Sonnet
- **Best for**: Code explanations, basic documentation, simple code generation, iterative development
- **Key strengths**: Low latency, cost-effective, reliable for lightweight tasks

#### **Multimodal Models**
*For tasks involving visual input and real-time performance*
- **Models**: GPT-4o, Gemini 2.0 Flash, Gemini 2.5 Pro
- **Best for**: UI analysis, diagram interpretation, screenshot debugging, visual reasoning
- **Key strengths**: Image processing, cross-modal understanding, visual context integration

#### **Balanced Models**
*For general-purpose development with good cost-performance ratio*
- **Models**: GPT-4.1, Claude 3.7 Sonnet, Gemini 2.5 Pro
- **Best for**: Everyday coding tasks, broad knowledge requirements, mixed complexity work
- **Key strengths**: Versatility, consistent performance across task types, good default choices

#### **Next-Generation Models**
*Latest models with cutting-edge capabilities (currently in preview)*
- **Models**: Claude Opus 4, Claude Sonnet 4, o3
- **Best for**: Most demanding tasks, state-of-the-art performance requirements
- **Key strengths**: Enhanced reasoning, improved accuracy, latest architectural improvements

## Task Categories

Each model is evaluated across these task categories:

- **Code Explanation**: Understanding and explaining code logic
- **Documentation**: Writing clear documentation and comments
- **Error Diagnosis**: Identifying and explaining errors
- **Small Code Generation**: Creating small, reusable code pieces
- **Multilingual Support**: Working with non-English content
- **Complex Reasoning**: Multi-step logical reasoning
- **Large Refactoring**: Handling complex code restructuring
- **Architecture Analysis**: Analyzing system structure and patterns
- **Performance Analysis**: Optimizing performance-critical code
- **Visual Input**: Processing diagrams, screenshots, and images

## Usage Examples

### Basic Heatmap
```python
plot_model_strengths()
```

### Custom Title and Save
```python
plot_model_strengths(
    title="My Custom Model Comparison",
    save_path="my_comparison.png"
)
```

### Task-Specific Comparison
```python
compare_models_by_task("Performance Analysis", top_n=3)
```

### Categorical Model Comparisons
The demo script includes radar chart comparisons for each model category:

```python
# Compare reasoning powerhouses
plot_model_radar(["o3", "o1", "Claude 3.7 Sonnet", "GPT-4.5"])

# Compare fast, efficient models
plot_model_radar(["GPT-4.1", "o4-mini", "o3-mini", "Claude 3.5 Sonnet"])

# Compare multimodal capabilities
plot_model_radar(["GPT-4o", "Gemini 2.0 Flash", "Gemini 2.5 Pro"])

# Compare balanced, general-purpose models
plot_model_radar(["GPT-4.1", "Claude 3.7 Sonnet", "Gemini 2.5 Pro"])

# Compare next-generation models
plot_model_radar(["Claude Opus 4", "Claude Sonnet 4", "o3"])
```

### Radar Chart for Reasoning Models
```python
plot_model_radar(["o3", "o1", "Claude 3.7 Sonnet"])
```

### Custom Data
```python
custom_data = {
    "Model A": {
        "Speed": 8.0,
        "Accuracy": 6.0,
        "Cost": 9.0
    },
    "Model B": {
        "Speed": 6.0,
        "Accuracy": 9.0,
        "Cost": 5.0
    }
}

plot_model_strengths(
    model_data=custom_data,
    title="Custom Model Comparison"
)
```

## Data Sources

The default model strength scores are derived from the official GitHub documentation:
- [Choosing the right AI model for your task](https://docs.github.com/en/enterprise-cloud@latest/copilot/using-github-copilot/ai-models/choosing-the-right-ai-model-for-your-task)

Scores are normalized on a 0-10 scale based on the documented strengths and use cases for each model.

## Running Examples

```bash
# Run the demo script
python examples/models/example.py

# Or run the comprehensive demo
python examples/models/demo.py
```
