from typing import Dict, List, Optional, Union
import numpy as np


def plot_model_strengths(
    model_data: Optional[Dict[str, Dict[str, float]]] = None,
    tasks: Optional[List[str]] = None,
    models: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    figsize: tuple = (14, 10),
    title: str = "AI Model Strengths Comparison by Task"
) -> None:
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
    except ImportError as e:
        missing_lib = str(e).split("'")[1]
        raise ImportError(f"Required library '{missing_lib}' not installed. "
                         f"Run: pip install matplotlib seaborn pandas")

    if model_data is None:
        model_data = _get_default_model_data()

    if models is None:
        models = list(model_data.keys())
    if tasks is None:
        tasks = list(next(iter(model_data.values())).keys()) if model_data else []

    strength_matrix = []
    for model in models:
        if model in model_data:
            row = [model_data[model].get(task, 0.0) for task in tasks]
            strength_matrix.append(row)
        else:
            strength_matrix.append([0.0] * len(tasks))

    df = pd.DataFrame(strength_matrix, index=models, columns=tasks)

    plt.figure(figsize=figsize)
    sns.heatmap(
        df,
        annot=True,
        cmap='RdYlGn',
        center=5.0,
        vmin=0,
        vmax=10,
        fmt='.1f',
        cbar_kws={'label': 'Strength Score (0-10)'},
        linewidths=0.5
    )

    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Task Categories', fontsize=12, fontweight='bold')
    plt.ylabel('AI Models', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()


def _get_default_model_data() -> Dict[str, Dict[str, float]]:
    return {
        'GPT-4.1': {
            'Code Explanation': 9.0,
            'Documentation': 8.5,
            'Error Diagnosis': 8.5,
            'Small Code Generation': 9.0,
            'Multilingual Support': 8.5,
            'Complex Reasoning': 6.0,
            'Large Refactoring': 6.0,
            'Architecture Analysis': 6.0,
            'Performance Analysis': 5.5,
            'Visual Input': 5.0
        },
        'GPT-4o': {
            'Code Explanation': 8.5,
            'Documentation': 8.0,
            'Error Diagnosis': 8.0,
            'Small Code Generation': 8.5,
            'Multilingual Support': 8.0,
            'Complex Reasoning': 6.0,
            'Large Refactoring': 6.0,
            'Architecture Analysis': 6.0,
            'Performance Analysis': 5.5,
            'Visual Input': 7.5
        },
        'GPT-4.5': {
            'Code Explanation': 7.5,
            'Documentation': 9.0,
            'Error Diagnosis': 8.0,
            'Small Code Generation': 8.0,
            'Multilingual Support': 7.5,
            'Complex Reasoning': 8.5,
            'Large Refactoring': 8.5,
            'Architecture Analysis': 8.5,
            'Performance Analysis': 7.0,
            'Visual Input': 5.0
        },
        'o1': {
            'Code Explanation': 7.0,
            'Documentation': 7.0,
            'Error Diagnosis': 8.5,
            'Small Code Generation': 7.5,
            'Multilingual Support': 7.0,
            'Complex Reasoning': 9.5,
            'Large Refactoring': 9.0,
            'Architecture Analysis': 9.0,
            'Performance Analysis': 9.5,
            'Visual Input': 4.0
        },
        'o3': {
            'Code Explanation': 7.5,
            'Documentation': 7.5,
            'Error Diagnosis': 9.0,
            'Small Code Generation': 8.0,
            'Multilingual Support': 7.5,
            'Complex Reasoning': 10.0,
            'Large Refactoring': 9.5,
            'Architecture Analysis': 9.5,
            'Performance Analysis': 10.0,
            'Visual Input': 4.0
        },
        'o3-mini': {
            'Code Explanation': 8.5,
            'Documentation': 6.5,
            'Error Diagnosis': 7.5,
            'Small Code Generation': 8.5,
            'Multilingual Support': 7.0,
            'Complex Reasoning': 5.0,
            'Large Refactoring': 4.0,
            'Architecture Analysis': 4.0,
            'Performance Analysis': 5.0,
            'Visual Input': 4.0
        },
        'o4-mini': {
            'Code Explanation': 8.5,
            'Documentation': 6.5,
            'Error Diagnosis': 7.5,
            'Small Code Generation': 8.5,
            'Multilingual Support': 7.0,
            'Complex Reasoning': 5.5,
            'Large Refactoring': 4.5,
            'Architecture Analysis': 4.5,
            'Performance Analysis': 5.5,
            'Visual Input': 4.0
        },
        'Claude 3.5 Sonnet': {
            'Code Explanation': 8.5,
            'Documentation': 8.5,
            'Error Diagnosis': 8.0,
            'Small Code Generation': 8.5,
            'Multilingual Support': 7.5,
            'Complex Reasoning': 6.0,
            'Large Refactoring': 6.0,
            'Architecture Analysis': 6.0,
            'Performance Analysis': 6.0,
            'Visual Input': 4.0
        },
        'Claude 3.7 Sonnet': {
            'Code Explanation': 8.0,
            'Documentation': 8.5,
            'Error Diagnosis': 8.5,
            'Small Code Generation': 8.0,
            'Multilingual Support': 8.0,
            'Complex Reasoning': 9.0,
            'Large Refactoring': 9.5,
            'Architecture Analysis': 9.5,
            'Performance Analysis': 8.0,
            'Visual Input': 4.0
        },
        'Claude Sonnet 4': {
            'Code Explanation': 8.5,
            'Documentation': 9.0,
            'Error Diagnosis': 9.0,
            'Small Code Generation': 8.5,
            'Multilingual Support': 8.5,
            'Complex Reasoning': 9.5,
            'Large Refactoring': 9.5,
            'Architecture Analysis': 9.5,
            'Performance Analysis': 8.5,
            'Visual Input': 5.0
        },
        'Claude Opus 4': {
            'Code Explanation': 9.0,
            'Documentation': 9.5,
            'Error Diagnosis': 9.5,
            'Small Code Generation': 9.0,
            'Multilingual Support': 9.0,
            'Complex Reasoning': 10.0,
            'Large Refactoring': 10.0,
            'Architecture Analysis': 10.0,
            'Performance Analysis': 9.0,
            'Visual Input': 6.0
        },
        'Gemini 2.0 Flash': {
            'Code Explanation': 7.5,
            'Documentation': 7.0,
            'Error Diagnosis': 8.0,
            'Small Code Generation': 8.5,
            'Multilingual Support': 7.0,
            'Complex Reasoning': 6.0,
            'Large Refactoring': 5.5,
            'Architecture Analysis': 5.5,
            'Performance Analysis': 6.0,
            'Visual Input': 9.0
        },
        'Gemini 2.5 Pro': {
            'Code Explanation': 8.0,
            'Documentation': 8.0,
            'Error Diagnosis': 8.5,
            'Small Code Generation': 8.0,
            'Multilingual Support': 8.0,
            'Complex Reasoning': 8.5,
            'Large Refactoring': 8.5,
            'Architecture Analysis': 8.5,
            'Performance Analysis': 9.0,
            'Visual Input': 7.0
        }
    }


def compare_models_by_task(
    task: str,
    model_data: Optional[Dict[str, Dict[str, float]]] = None,
    top_n: int = 5,
    save_path: Optional[str] = None
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib not installed. Run: pip install matplotlib")

    if model_data is None:
        model_data = _get_default_model_data()

    task_scores = []
    for model, tasks in model_data.items():
        if task in tasks:
            task_scores.append((model, tasks[task]))

    task_scores.sort(key=lambda x: x[1], reverse=True)
    top_models = task_scores[:top_n]

    models, scores = zip(*top_models)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(models, scores, color='steelblue', alpha=0.7)
    
    for bar, score in zip(bars, scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{score:.1f}', ha='center', va='bottom', fontweight='bold')

    plt.title(f'Top {top_n} Models for {task}', fontsize=14, fontweight='bold')
    plt.xlabel('AI Models', fontsize=12)
    plt.ylabel('Strength Score', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 10.5)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()


def plot_model_radar(
    models: Union[str, List[str]],
    model_data: Optional[Dict[str, Dict[str, float]]] = None,
    save_path: Optional[str] = None
) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        missing_lib = str(e).split("'")[1]
        raise ImportError(f"Required library '{missing_lib}' not installed. "
                         f"Run: pip install matplotlib numpy")

    if model_data is None:
        model_data = _get_default_model_data()

    if isinstance(models, str):
        models = [models]

    tasks = list(next(iter(model_data.values())).keys())
    num_tasks = len(tasks)

    angles = np.linspace(0, 2 * np.pi, num_tasks, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']

    for i, model in enumerate(models):
        if model in model_data:
            values = [model_data[model][task] for task in tasks]
            values += values[:1]

            ax.plot(angles, values, 'o-', linewidth=2, 
                   label=model, color=colors[i % len(colors)])
            ax.fill(angles, values, alpha=0.15, color=colors[i % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(tasks, fontsize=10)
    ax.set_ylim(0, 10)
    ax.set_yticks(range(0, 11, 2))
    ax.set_yticklabels(range(0, 11, 2), fontsize=8)
    ax.grid(True)

    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
    plt.title('AI Model Capabilities Radar Chart', size=16, fontweight='bold', pad=20)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()