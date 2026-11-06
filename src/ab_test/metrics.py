"""Описательные метрики: попытки, воронка и сегменты."""
import pandas as pd
from .config import STEPS, GROUPS

def calculate_funnel(payments):
    funnel = payments.groupby('group')[STEPS].count().reindex(GROUPS, fill_value=0)
    if (funnel[STEPS[0]] == 0).any():
        raise ValueError('В одной из групп нет открытий формы')
    rates = pd.DataFrame(index=funnel.index)
    for i, (prev, nxt) in enumerate(zip(STEPS, STEPS[1:]), start=1):
        rates[f'{i} → {i+1}'] = funnel[nxt] / funnel[prev].replace(0, float('nan')) * 100
    return funnel, rates

def aggregate_users(users, payments):
    totals = payments.groupby('user_id').agg(attempts=('payment_id', 'count'), successes=('success', 'sum')).reset_index()
    result = users[['user_id', 'group']].merge(totals, on='user_id', how='left', validate='one_to_one')
    result[['attempts', 'successes']] = result[['attempts', 'successes']].fillna(0).astype(int)
    return result

def segment_analysis(df, segment):
    result = df.dropna(subset=[segment]).groupby([segment, 'group']).agg(
        attempts=('payment_id', 'count'), successes=('success', 'sum'))
    result['cr'] = result['successes'] / result['attempts'] * 100
    return result

def compare_segments(results):
    comparison = results['cr'].unstack('group').reindex(columns=GROUPS)
    comparison['uplift_pp'] = comparison['B'] - comparison['A']
    return comparison.round(2)
