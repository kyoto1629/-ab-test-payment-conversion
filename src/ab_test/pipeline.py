"""Полный воспроизводимый запуск без Jupyter."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .config import DEFAULT_INPUT, DEFAULT_OUTPUT, ALPHA
from .data import load_data, prepare_data
from .metrics import calculate_funnel, aggregate_users, segment_analysis, compare_segments
from .statistics import cluster_test

def analyze(input_path=DEFAULT_INPUT, alpha=ALPHA):
    users, payments = load_data(input_path)
    users_clean, payments_clean, audit = prepare_data(users, payments)
    funnel, step_rates = calculate_funnel(payments_clean)
    user_stats = aggregate_users(users_clean, payments_clean)
    statistics = cluster_test(user_stats, alpha)
    return dict(users=users_clean, payments=payments_clean, audit=audit,
                funnel=funnel, step_rates=step_rates, user_stats=user_stats,
                statistics=statistics, device_results=segment_analysis(payments_clean, 'device_type'),
                city_results=segment_analysis(payments_clean, 'city'))

def run(input_path=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT, alpha=ALPHA):
    import matplotlib
    matplotlib.use('Agg')
    from .plots import build_figures
    from .reporting import build_report
    result = analyze(input_path, alpha)
    output_dir = Path(output_dir)
    tables = output_dir / 'tables'
    figures = output_dir / 'figures'
    tables.mkdir(parents=True, exist_ok=True)
    processed = output_dir.parent / 'data' / 'processed' if output_dir == DEFAULT_OUTPUT else output_dir / 'processed'
    processed.mkdir(parents=True, exist_ok=True)
    for name in ['users', 'payments']:
        result[name].to_csv(processed / f'{name}_clean.csv', index=False, encoding='utf-8-sig')
    result['user_stats'].to_csv(processed / 'user_stats.csv', index=False, encoding='utf-8-sig')
    for name in ['funnel', 'step_rates', 'device_results', 'city_results']:
        result[name].to_csv(tables / f'{name}.csv', encoding='utf-8-sig')
    for segment in ['device', 'city']:
        compare_segments(result[f'{segment}_results']).to_csv(tables / f'{segment}_comparison.csv', encoding='utf-8-sig')
    (output_dir / 'results.json').write_text(json.dumps(
        dict(statistics=result['statistics'], audit=result['audit']), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    build_figures(result['funnel'], result['device_results'], result['city_results'], result['statistics'], figures)
    build_report(result['statistics'], result['step_rates'], result['audit'], figures, output_dir / 'AB_test_report.pdf')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--alpha', type=float, default=ALPHA)
    args = parser.parse_args()
    result = run(args.input, args.output, args.alpha)
    print(f"Отчёт: {args.output.resolve() / 'AB_test_report.pdf'}")
    print(f"Изменение: {result['statistics']['delta'] * 100:+.2f} п.п.")

if __name__ == '__main__':
    main()
