#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from examples.models.plot import (
    plot_model_strengths,
    compare_models_by_task,
    plot_model_radar
)


def main():
    print("AI Model Strengths Comparison Demo")
    print("=" * 40)
    
    print("\n1. Generating comprehensive heatmap of all models and tasks...")
    plot_model_strengths(
        title="GitHub Copilot AI Models - Strength Comparison",
        save_path="model_strengths_heatmap.png"
    )
    
    '''
    print("\n2. Comparing top models for Complex Reasoning...")
    compare_models_by_task(
        task="Complex Reasoning",
        top_n=5,
        save_path="complex_reasoning_comparison.png"
    )
    
    print("\n3. Comparing top models for Visual Input processing...")
    compare_models_by_task(
        task="Visual Input",
        top_n=5,
        save_path="visual_input_comparison.png"
    )
    '''
    
    print("\n4. Creating radar chart for top reasoning models...")
    plot_model_radar(
        models=["o3", "o1", "Claude 3.7 Sonnet", "GPT-4.5"],
        save_path="reasoning_models_radar.png"
    )
    
    print("\n5. Creating radar chart for fast response models...")
    plot_model_radar(
        models=["GPT-4.1", "o4-mini", "o3-mini", "Claude 3.5 Sonnet"],
        save_path="fast_models_radar.png"
    )
    
    print("\n6. Creating radar chart for multimodal models...")
    plot_model_radar(
        models=["GPT-4o", "Gemini 2.0 Flash", "Gemini 2.5 Pro"],
        save_path="multimodal_models_radar.png"
    )
    
    print("\n7. Creating radar chart for balanced models...")
    plot_model_radar(
        models=["GPT-4.1", "Claude 3.7 Sonnet", "Gemini 2.5 Pro"],
        save_path="balanced_models_radar.png"
    )
    
    print("\n8. Creating radar chart for next-generation models...")
    plot_model_radar(
        models=["Claude Opus 4", "Claude Sonnet 4", "o3"],
        save_path="next_gen_models_radar.png"
    )
     
    print("\nDemo completed! Check the generated PNG files for visualizations.")


if __name__ == "__main__":
    main()
