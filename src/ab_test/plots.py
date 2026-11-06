"""Графики исходного анализа без зависимости от состояния ноутбука."""
from .metrics import compare_segments

def build_figures(funnel, device_results, city_results, statistics, figures_dir):
    delta = statistics["delta"]
    ci_lower = statistics["ci_lower"]
    ci_upper = statistics["ci_upper"]
    import matplotlib.pyplot as plt
    from pathlib import Path

    # Папка для графиков
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Оформление
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 11

    colors = {
        'A': '#94A3B8',
        'B': '#0D9488'
    }

    # Конверсия относительно первого этапа
    funnel_pct = (
        funnel
        .div(funnel['step1_opened'], axis=0)
        .mul(100)
        .T
    )

    # Переименуем этапы
    funnel_pct.index = [
        'Открытие формы',
        'Ввод реквизитов',
        'Подтверждение',
        'Успешная оплата'
    ]

    # Строим график
    fig, ax = plt.subplots(figsize=(10, 5))

    funnel_pct.plot(
        kind='barh',
        ax=ax,
        color=[colors['A'], colors['B']],
        width=0.7
    )

    ax.invert_yaxis()

    ax.set_title(
        'Воронка оплаты ЖКХ: A vs B',
        fontsize=15,
        fontweight='bold',
        pad=20
    )

    ax.set_xlabel('Конверсия от открытия формы, %')
    ax.set_ylabel('')
    ax.set_xlim(0, 115)

    ax.legend(title='Группа')

    # Подписи значений
    for container in ax.containers:
        ax.bar_label(
            container,
            fmt='%.1f%%',
            padding=4,
            fontsize=9
        )

    plt.tight_layout()

    plt.savefig(
        figures_dir / 'funnel.png',
        dpi=300,
        bbox_inches='tight'
    )

    plt.close(fig)

    # Подготовим данные
    device_comparison = compare_segments(device_results)
    city_comparison = compare_segments(city_results)

    fig, axes = plt.subplots(
        1, 2,
        figsize=(13, 5)
    )

    segments = [
        (device_comparison, 'По устройствам'),
        (city_comparison, 'По городам')
    ]

    for ax, (data, title) in zip(axes, segments):

        data[['A', 'B']].plot(
            kind='bar',
            ax=ax,
            color=[colors['A'], colors['B']],
            width=0.7,
            rot=0
        )

        ax.set_title(
            title,
            fontsize=13,
            fontweight='bold'
        )

        ax.set_xlabel('')
        ax.set_ylabel('Конверсия, %')
        ax.set_ylim(0, 115)

        ax.legend(title='Группа')

        for container in ax.containers:
            ax.bar_label(
                container,
                fmt='%.1f%%',
                padding=3,
                fontsize=9
            )

    fig.suptitle(
        'Конверсия в успешную оплату по сегментам',
        fontsize=16,
        fontweight='bold'
    )

    plt.tight_layout()

    plt.savefig(
        figures_dir / 'segments.png',
        dpi=300,
        bbox_inches='tight'
    )

    plt.close(fig)

    # Переводим значения в процентные пункты
    effect = delta * 100
    lower = ci_lower * 100
    upper = ci_upper * 100

    fig, ax = plt.subplots(figsize=(9, 3))

    # Доверительный интервал
    ax.hlines(
        y=0,
        xmin=lower,
        xmax=upper,
        color=colors['B'],
        linewidth=5
    )

    # Точечная оценка эффекта
    ax.scatter(
        effect,
        0,
        color=colors['B'],
        s=120,
        zorder=3
    )

    # Границы интервала
    ax.vlines(
        [lower, upper],
        ymin=-0.08,
        ymax=0.08,
        color=colors['B'],
        linewidth=2
    )

    # Линия отсутствия эффекта
    ax.axvline(
        0,
        color='gray',
        linestyle='--',
        alpha=0.7
    )

    # Подписи
    ax.annotate(
        f'{effect:+.2f} п.п.',
        (effect, 0),
        xytext=(0, 18),
        textcoords='offset points',
        ha='center',
        fontweight='bold'
    )

    for value in [lower, upper]:
        ax.annotate(
            f'{value:.2f}',
            (value, 0),
            xytext=(0, -25),
            textcoords='offset points',
            ha='center'
        )

    ax.set_xlim(min(0, lower) - 3, max(0, upper) + 5)
    ax.set_ylim(-0.5, 0.6)
    ax.set_yticks([])

    ax.set_xlabel('Изменение конверсии, п.п.')

    ax.set_title(
        f'Изменение конверсии B относительно A: {(1-statistics["alpha"])*100:.0f}% ДИ',
        fontsize=14,
        fontweight='bold'
    )

    plt.tight_layout()

    plt.savefig(
        figures_dir / 'confidence_interval.png',
        dpi=300,
        bbox_inches='tight'
    )

    plt.close(fig)