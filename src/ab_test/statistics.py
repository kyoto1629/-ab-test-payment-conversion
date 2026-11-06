"""Тест разности ratio-метрик с кластерной дисперсией по user_id."""
import numpy as np
from scipy.stats import norm
from .config import ALPHA, GROUPS

def cluster_test(user_stats, alpha=ALPHA):
    if not 0 < alpha < 1:
        raise ValueError('alpha должна находиться между 0 и 1')
    groups = {}
    for group in GROUPS:
        data = user_stats.loc[user_stats['group'] == group]
        n = len(data)
        attempts = int(data['attempts'].sum())
        if n < 2 or attempts == 0:
            raise ValueError(f'Группа {group}: нужны минимум два пользователя и одна попытка')
        cr = float(data['successes'].sum() / attempts)
        residuals = data['successes'] - cr * data['attempts']
        variance = float(n / (n - 1) * (residuals ** 2).sum() / attempts ** 2)
        groups[group] = {'cr': cr, 'variance': variance}
    cr_a, cr_b = groups['A']['cr'], groups['B']['cr']
    delta = cr_b - cr_a
    se_delta = float(np.sqrt(groups['A']['variance'] + groups['B']['variance']))
    if se_delta == 0:
        raise ValueError('Нулевая стандартная ошибка: нормальная аппроксимация неприменима')
    z_stat = delta / se_delta
    p_value = float(2 * norm.sf(abs(z_stat)))
    critical = float(norm.ppf(1 - alpha / 2))
    return dict(cr_a=cr_a, cr_b=cr_b, delta=delta, se_delta=se_delta,
                z_stat=z_stat, p_value=p_value, ci_lower=delta-critical*se_delta,
                ci_upper=delta+critical*se_delta, alpha=alpha,
                relative_uplift=(cr_b/cr_a-1)*100 if cr_a else None,
                group_stats=groups)
