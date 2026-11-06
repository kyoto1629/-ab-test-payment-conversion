"""Загрузка, диагностика и явная политика очистки исходных данных."""
import pandas as pd
from .config import DEFAULT_INPUT, STEPS, GROUPS

def load_data(path=DEFAULT_INPUT):
    with pd.ExcelFile(path) as book:
        users = pd.read_excel(book, sheet_name='Пользователи')
        payments = pd.read_excel(book, sheet_name='Платежи')
    required_users = {'user_id', 'group', 'age', 'city', 'device_type'}
    required_payments = {'payment_id', 'user_id', 'group', *STEPS}
    for name, frame, required in [('users', users, required_users), ('payments', payments, required_payments)]:
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f'{name}: отсутствуют столбцы {sorted(missing)}')
    for step in STEPS:
        payments[step] = pd.to_datetime(payments[step], errors='raise')
    return users, payments

def validate_ids(users, payments):
    for frame, key in [(users, 'user_id'), (payments, 'payment_id')]:
        if frame[key].isna().any() or frame[key].duplicated().any():
            raise ValueError(f'{key}: идентификатор отсутствует или дублируется')

def audit_data(users, payments):
    validate_ids(users, payments)
    joined = payments.merge(users[['user_id', 'group']], on='user_id', how='left',
                            suffixes=('_payment', '_user'), validate='many_to_one')
    matched = joined['user_id'].isin(users['user_id'])
    mismatch = matched & joined['group_user'].isin(GROUPS) & (
        joined['group_payment'].fillna('') != joined['group_user'].fillna(''))
    return {
        'raw_users': len(users), 'raw_payments': len(payments),
        'excluded_users': int((~users['group'].isin(GROUPS)).sum()),
        'payments_missing_user_id': int(payments['user_id'].isna().sum()),
        'payments_unknown_user': int((payments['user_id'].notna() & ~payments['user_id'].isin(users['user_id'])).sum()),
        'group_mismatches': int(mismatch.sum()),
        'abnormal_age': int(((users['age'] < 0) | (users['age'] > 110)).sum()),
        'missing_city': int(users['city'].isna().sum()),
        'duplicate_users': int(users['user_id'].duplicated().sum()),
        'duplicate_payments': int(payments['payment_id'].duplicated().sum()),
    }

def funnel_errors(payments):
    return {f'{prev} -> {nxt}': int(((payments[nxt].notna() & payments[prev].isna()) |
             (payments[nxt] < payments[prev])).sum()) for prev, nxt in zip(STEPS, STEPS[1:])}

def prepare_data(users, payments):
    audit = audit_data(users, payments)
    users_clean = users.loc[users['group'].isin(GROUPS)].copy()
    payments_clean = payments.merge(
        users_clean[['user_id', 'group', 'age', 'city', 'device_type']].rename(columns={'group': 'assigned_group'}),
        on='user_id', how='inner', validate='many_to_one')
    payments_clean['group'] = payments_clean.pop('assigned_group')
    if payments_clean[STEPS[0]].isna().any():
        raise ValueError('Для каждой попытки требуется событие открытия формы')
    errors = funnel_errors(payments_clean)
    if any(errors.values()):
        raise ValueError(f'Нарушена последовательность воронки: {errors}')
    if set(users_clean['group']) != set(GROUPS):
        raise ValueError('Для анализа нужны обе группы A и B')
    payments_clean['success'] = payments_clean[STEPS[-1]].notna().astype(int)
    audit.update(clean_users=len(users_clean), clean_payments=len(payments_clean),
                 excluded_payments=len(payments) - len(payments_clean), funnel_errors=errors)
    return users_clean, payments_clean, audit
