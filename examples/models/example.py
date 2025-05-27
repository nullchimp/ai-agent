#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from examples.models.plot import (
    plot_model_strengths,
    compare_models_by_task,
    plot_model_radar
)


def example_usage():
    print("AI Model Plotting Library Examples")
    print("=" * 40)
    
    # Example 1: Basic heatmap
    print("\nExample 1: Creating a heatmap of all model strengths")
    plot_model_strengths()
    
    # Example 2: Task-specific comparison
    print("\nExample 2: Comparing models for a specific task")
    compare_models_by_task("Performance Analysis")
    
    # Example 3: Radar chart for specific models
    print("\nExample 3: Radar chart comparing reasoning models")
    plot_model_radar(["o3", "GPT-4.5", "Claude 3.7 Sonnet"])
    
    # Example 4: Custom data
    print("\nExample 4: Using custom model data")
    custom_data = {
        "Model A": {
            "Speed": 8.0,
            "Accuracy": 6.0,
            "Cost Efficiency": 9.0
        },
        "Model B": {
            "Speed": 6.0,
            "Accuracy": 9.0,
            "Cost Efficiency": 5.0
        }
    }
    plot_model_strengths(
        model_data=custom_data,
        title="Custom Model Comparison"
    )


if __name__ == "__main__":
    example_usage()
