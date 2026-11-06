"""PDF: оформление исходного отчёта, актуальные показатели из расчётов."""
def build_report(statistics, step_rates, audit, figures_dir, output_path):
    cr_a = statistics["cr_a"]
    cr_b = statistics["cr_b"]
    delta = statistics["delta"]
    relative_uplift = statistics["relative_uplift"]
    z_stat = statistics["z_stat"]
    p_value = statistics["p_value"]
    ci_lower = statistics["ci_lower"]
    ci_upper = statistics["ci_upper"]
    alpha = statistics["alpha"]

    from pathlib import Path
    import matplotlib

    from reportlab.lib import colors as pdf_colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Image,
        Table,
        TableStyle,
        PageBreak
    )


    # 1. НАСТРОЙКА ШРИФТОВ


    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"

    pdfmetrics.registerFont(
        TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf"))
    )

    pdfmetrics.registerFont(
        TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf"))
    )

    pdfmetrics.registerFontFamily(
        "DejaVu",
        normal="DejaVu",
        bold="DejaVu-Bold"
    )


    # 2. НАСТРОЙКА ДОКУМЕНТА


    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=38,
        leftMargin=38,
        topMargin=35,
        bottomMargin=40
    )

    navy = pdf_colors.HexColor("#17304D")
    teal = pdf_colors.HexColor("#0D9488")
    gray = pdf_colors.HexColor("#64748B")


    # 3. СТИЛИ ТЕКСТА


    styles = {
        "title": ParagraphStyle(
            "TitleCustom",
            fontName="DejaVu-Bold",
            fontSize=19,
            leading=25,
            textColor=navy,
            spaceAfter=12
        ),

        "heading": ParagraphStyle(
            "HeadingCustom",
            fontName="DejaVu-Bold",
            fontSize=12,
            leading=18,
            textColor=navy,
            spaceBefore=12,
            spaceAfter=8
        ),

        "body": ParagraphStyle(
            "BodyCustom",
            fontName="DejaVu",
            fontSize=10,
            leading=15,
            textColor=navy,
            spaceAfter=8
        ),

        "small": ParagraphStyle(
            "SmallCustom",
            fontName="DejaVu",
            fontSize=8.5,
            leading=13,
            textColor=gray,
            spaceAfter=8
        )
    }


    # 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ


    def P(text, style="body"):
        return Paragraph(text, styles[style])


    def add_chart(filename, max_width=515, max_height=250):

        path = figures_dir / filename

        width, height = ImageReader(str(path)).getSize()

        scale = min(
            max_width / width,
            max_height / height
        )

        return Image(
            str(path),
            width=width * scale,
            height=height * scale
        )


    def styled_table(data, widths):

        table = Table(
            data,
            colWidths=widths,
            hAlign="LEFT"
        )

        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
            ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),

            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), pdf_colors.white),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [pdf_colors.whitesmoke, pdf_colors.white]),

            ("FONTSIZE", (0, 0), (-1, -1), 9),

            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))

        return table


    def footer(canvas, document):

        canvas.saveState()

        canvas.setFont("DejaVu", 8)
        canvas.setFillColor(gray)

        canvas.drawString(
            38, 25,
            "A/B-тест формы оплаты ЖКХ"
        )

        canvas.drawRightString(
            A4[0] - 38,
            25,
            f"Страница {document.page}"
        )

        canvas.restoreState()


    story = []


    # СТРАНИЦА 1. ОСНОВНЫЕ РЕЗУЛЬТАТЫ


    story.append(
        P("A/B-тест новой формы оплаты ЖКХ", "title")
    )

    story.append(
        P("Период по описанию исходного эксперимента: 1-30 апреля 2024 года", "small")
    )

    # Основные показатели

    story.append(
        P("Основные результаты", "heading")
    )

    kpi_data = [
        [
            "Группа A",
            "Группа B",
            "Прирост",
            "Относит. прирост"
        ],
        [
            f"{cr_a:.2%}",
            f"{cr_b:.2%}",
            f"{delta * 100:+.2f} п.п.",
            (f"{relative_uplift:+.2f}%" if relative_uplift is not None else "не определён")
        ]
    ]

    story.append(
        styled_table(kpi_data, [125, 125, 135, 130])
    )

    story.append(Spacer(1, 10))

    # Описание эксперимента

    story.append(P(
        "В эксперименте группа A использовала действующую "
        "форму оплаты ЖКХ, группа B — новую форму с "
        "упрощённым заполнением реквизитов. "
        "Основная метрика — конверсия из открытия формы "
        "в успешную оплату, рассчитанная по попыткам платежей."
    ))

    # Воронка

    story.append(
        P("Воронка оплаты", "heading")
    )

    story.append(
        add_chart(
            "funnel.png",
            max_height=260
        )
    )

    # Конверсии между этапами

    story.append(
        P("Конверсии между этапами", "heading")
    )

    transition_names = [
        "Открытие → реквизиты",
        "Реквизиты → подтверждение",
        "Подтверждение → оплата"
    ]

    transition_data = [
        ["Переход", "A", "B", "Разница"]
    ]

    for i, name in enumerate(transition_names):

        a = step_rates.loc["A"].iloc[i]
        b = step_rates.loc["B"].iloc[i]

        transition_data.append([
            name,
            f"{a:.1f}%",
            f"{b:.1f}%",
            f"{b - a:+.2f} п.п."
        ])

    story.append(
        styled_table(
            transition_data,
            [210, 85, 85, 135]
        )
    )

    story.append(Spacer(1, 8))

    # Описание очистки

    story.append(P(
        f"<b>EDA и очистка данных.</b> Исходно: {audit['raw_users']} пользователей и "
        f"{audit['raw_payments']} попыток. После очистки: {audit['clean_users']} пользователей "
        f"и {audit['clean_payments']} попыток. Исключено пользователей без группы A/B: "
        f"{audit['excluded_users']}; платежей вне очищенной выборки: {audit['excluded_payments']}. "
        f"Исправлено несоответствий групп: {audit['group_mismatches']}. "
        f"Аномальных возрастов: {audit['abnormal_age']}; пропусков города: {audit['missing_city']}. "
        "Возраст и город не используются для исключения из основной метрики. "
        "Дубликаты идентификаторов и нарушения порядка этапов проверены; при их наличии запуск останавливается.",
        "small"
    ))


    # СТРАНИЦА 2. СТАТИСТИКА И ВЫВОДЫ


    story.append(PageBreak())

    story.append(
        P("Статистика и продуктовые выводы", "title")
    )

    # Проверка гипотезы

    story.append(
        P("Проверка гипотезы", "heading")
    )

    story.append(P(
        "Нулевая гипотеза: конверсии групп A и B равны. "
        "Поскольку рандомизация проводилась на уровне "
        "клиентов, а один клиент мог совершить несколько "
        "попыток оплаты, использован двусторонний z-тест "
        "с кластерно-робастной стандартной ошибкой "
        "по пользователям."
    ))

    story.append(P(
        f"<b>Z = {z_stat:.2f}; "
        f"p-value = {p_value:.2e}.</b> "
        f"Прирост конверсии составил "
        f"<b>{delta * 100:+.2f} п.п.</b> "
        f"{(1-alpha)*100:.0f}% доверительный интервал: "
        f"[{ci_lower * 100:.2f}; "
        f"{ci_upper * 100:.2f}] п.п."
    ))

    # График доверительного интервала

    story.append(
        add_chart(
            "confidence_interval.png",
            max_height=165
        )
    )

    # Сегментный анализ

    story.append(
        P("Анализ сегментов", "heading")
    )

    story.append(
        add_chart(
            "segments.png",
            max_height=195
        )
    )

    story.append(P(
        "Точечные оценки конверсии по устройствам и городам показаны на графике. "
        "Сегментный анализ носит описательный характер: статистическая значимость "
        "различий между сегментами отдельно не проверялась."
    ))
    story.append(P("Рекомендация", "heading"))
    recommendation = (
        "Результат поддерживает поэтапное внедрение формы B с контролем защитных метрик."
        if p_value < alpha and delta > 0 else
        "Результат не даёт оснований рекомендовать форму B как улучшение основной метрики."
    )
    story.append(P(
        f"<b>{recommendation}</b> Изменение конверсии: {delta * 100:+.2f} п.п.; "
        f"p-value = {p_value:.2e}, уровень значимости {alpha:.2f}. "
        "При запуске следует контролировать технические ошибки, повторные списания и обращения в поддержку."
    ))

    # Ограничения

    story.append(Spacer(1, 5))

    story.append(P(
        "<b>Ограничения.</b> Дизайн и период перенесены из исходного описания; автоматически не проверяются. "
        "Отсутствуют данные о суммах платежей, комиссиях, "
        "возвратах и технических сбоях. "
        "Поэтому полный финансовый эффект внедрения "
        "не оценён.",
        "small"
    ))


    # 5. СОЗДАНИЕ PDF


    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )

    return output_path
