"""
Performance metrics analysis script for AI Cloud Storage platform.
"""
import json
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_metrics(metrics_file):
    """Load metrics from JSON file."""
    with open(metrics_file) as f:
        return json.load(f)

def process_pod_metrics(metrics):
    """Process pod metrics into a DataFrame."""
    data = []
    for item in metrics['items']:
        pod_name = item['metadata']['name']
        usage = item['containers'][0]['usage']
        
        # Convert memory to MB
        memory = int(usage['memory'].replace('Ki', '')) / 1024
        # Convert CPU to cores
        cpu = int(usage['cpu'].replace('n', '')) / 1000000
        
        data.append({
            'pod': pod_name,
            'memory_mb': memory,
            'cpu_cores': cpu
        })
    
    return pd.DataFrame(data)

def create_resource_graphs(df):
    """Create resource usage graphs."""
    output_dir = Path('performance_graphs')
    output_dir.mkdir(exist_ok=True)
    
    # Set style
    plt.style.use('seaborn')
    sns.set_palette("husl")
    
    # Memory usage by pod
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='pod', y='memory_mb')
    plt.title('Memory Usage by Pod')
    plt.xlabel('Pod Name')
    plt.ylabel('Memory Usage (MB)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / 'memory_usage.png')
    plt.close()
    
    # CPU usage by pod
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='pod', y='cpu_cores')
    plt.title('CPU Usage by Pod')
    plt.xlabel('Pod Name')
    plt.ylabel('CPU Usage (cores)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / 'cpu_usage.png')
    plt.close()
    
    # Resource correlation
    plt.figure(figsize=(8, 8))
    sns.scatterplot(data=df, x='memory_mb', y='cpu_cores')
    plt.title('Memory vs CPU Usage')
    plt.xlabel('Memory Usage (MB)')
    plt.ylabel('CPU Usage (cores)')
    plt.tight_layout()
    plt.savefig(output_dir / 'resource_correlation.png')
    plt.close()

def generate_performance_report(df):
    """Generate performance analysis report."""
    report = {
        'summary': {
            'total_pods': len(df),
            'total_memory_mb': df['memory_mb'].sum(),
            'total_cpu_cores': df['cpu_cores'].sum(),
            'avg_memory_per_pod': df['memory_mb'].mean(),
            'avg_cpu_per_pod': df['cpu_cores'].mean()
        },
        'memory_stats': {
            'min': df['memory_mb'].min(),
            'max': df['memory_mb'].max(),
            'mean': df['memory_mb'].mean(),
            'median': df['memory_mb'].median(),
            'p95': df['memory_mb'].quantile(0.95)
        },
        'cpu_stats': {
            'min': df['cpu_cores'].min(),
            'max': df['cpu_cores'].max(),
            'mean': df['cpu_cores'].mean(),
            'median': df['cpu_cores'].median(),
            'p95': df['cpu_cores'].quantile(0.95)
        },
        'high_resource_pods': {
            'memory': df.nlargest(3, 'memory_mb')['pod'].tolist(),
            'cpu': df.nlargest(3, 'cpu_cores')['pod'].tolist()
        }
    }
    
    with open('performance_report.json', 'w') as f:
        json.dump(report, f, indent=2)

def analyze_metrics(metrics_file):
    """Main analysis function."""
    # Load and process metrics
    metrics = load_metrics(metrics_file)
    df = process_pod_metrics(metrics)
    
    # Generate visualizations
    create_resource_graphs(df)
    
    # Generate report
    generate_performance_report(df)
    
    print("Analysis complete. Check performance_graphs/ for visualizations.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python analyze_metrics.py <metrics_file>")
        sys.exit(1)
    
    analyze_metrics(sys.argv[1])
