"""Generate DEMO_SCRIPT.pdf - plain text only, no timestamps."""

from fpdf import FPDF


TITLE = "YouTube Viral Advisor - Demo Script"

SECTIONS = [
    {
        "heading": "Problem Overview",
        "body": (
            "Every YouTuber faces the same question before hitting publish: "
            '"Is this video actually going to reach people?"\n\n'
            "The problem is that most creators guess - wrong title length, wrong upload time, "
            "wrong number of tags. We built YouTube Viral Advisor to turn that guesswork into "
            "a data-driven prediction, using real trending data from 11 countries and 178,000 "
            "videos collected in 2026."
        ),
    },
    {
        "heading": "Data & Solution",
        "body": (
            "The foundation is a multi-country trending dataset - US, UK, Japan, Brazil, and 7 more. "
            "After cleaning, we have 178,267 videos across 15 categories, each enriched with features "
            "we engineered ourselves:\n\n"
            "  Like ratio and comment ratio - proxies for engagement quality.\n"
            "  Title NLP features - character length, word count, ALL-CAPS ratio, presence of numbers, "
            "questions, and exclamation marks.\n"
            "  Timing features - publish hour and day of week.\n"
            "  Tag count - how many tags the creator applied.\n\n"
            "The Dashboard gives creators an instant read of the landscape. We can see that Pets & Animals "
            "dominates with a median of 1.2 million views, that publishing around 13:00 to 21:00 UTC "
            "consistently outperforms other windows, and that viral videos cluster in a specific tag count "
            "and title length range - which we use in the predictor."
        ),
    },
    {
        "heading": "Viral Advisor Demo",
        "body": (
            "This is the core product. A creator fills in four things they know before uploading: "
            "title, category, number of tags, and publish time.\n\n"
            'Let\'s test a real scenario: title is "Top 10 BEST Moments of 2026", category Entertainment, '
            "15 tags, publishing Friday at 15:00 UTC.\n\n"
            "The model returns a virality score - a calibrated probability that this video lands in the "
            "top 25% of trending videos.\n\n"
            "Below the score, we get a Benchmark Comparison table - a side-by-side of the creator's inputs "
            "against what viral videos actually look like in the data. Each row has a clear status indicator: "
            "green dot for on-target, red for off.\n\n"
            "Then Recommendations - specific, data-driven suggestions. Not generic tips, but insights like: "
            '"Your title is 34 characters - viral videos use 34 to 66." Or: '
            '"Try publishing at 13:00, 15:00, or 21:00 UTC."\n\n'
            "The Viral Keywords panel is where NLP comes in. We computed a lift score for every word in the "
            "dataset - lift measures how much more likely a word is to appear in viral titles versus average "
            "titles. Words already in the title are highlighted. The rest become suggestions.\n\n"
            "Finally, a live Views by Publish Hour chart marks the creator's chosen hour in red so they can "
            "see exactly where they stand versus the average."
        ),
    },
    {
        "heading": "Model Insights",
        "body": (
            "The Model Insights page is for full transparency.\n\n"
            "The classifier is a Histogram Gradient Boosting model - faster and more accurate than a "
            "standard Random Forest on tabular data. It is wrapped in a Calibrated Cross-Validator using "
            "isotonic regression, which ensures the percentages we show are statistically meaningful "
            "probabilities, not raw scores.\n\n"
            "Key results on the held-out test set of 35,000 videos:\n\n"
            "  ROC AUC: 0.853 - the model correctly ranks a viral video above a non-viral one 85% of the time.\n"
            "  5-fold CV AUC: 0.797 plus or minus 0.005 - stable across folds, no overfitting.\n"
            "  Brier Score: 0.124 - well-calibrated probabilities.\n\n"
            "The permutation feature importance chart shows that category and country are the strongest "
            "predictors, followed by tag count, title length, and publish hour - which aligns with "
            "intuition and validates the feature engineering."
        ),
    },
    {
        "heading": "Closing",
        "body": (
            "YouTube Viral Advisor turns a creator's pre-upload decisions into a single, explainable score - "
            "backed by 178,000 real trending videos, a calibrated ML model, and NLP keyword analysis.\n\n"
            "The goal is not to predict the future perfectly. "
            "The goal is to give creators one honest data point before they publish - "
            "so the next video is not a guess."
        ),
    },
]


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "YouTube Viral Advisor", align="R")
        self.ln(4)
        self.set_draw_color(220, 220, 220)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(160, 160, 160)
        self.cell(0, 8, f"{self.page_no()}", align="C")


def build_pdf(out_path: str = "rq2_project/DEMO_SCRIPT.pdf") -> None:
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=22, top=18, right=22)
    pdf.add_page()

    # Title block
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(15, 23, 42)   # slate-900
    pdf.multi_cell(0, 10, TITLE, align="L")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)  # slate-500
    pdf.cell(0, 6, "Demo script - plain text, ~555 words, ~4 minutes at 140 wpm", align="L")
    pdf.ln(10)

    # Divider
    pdf.set_draw_color(226, 232, 240)  # slate-200
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10)

    for i, sec in enumerate(SECTIONS, 1):
        # Section number + heading
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(148, 163, 184)  # slate-400
        pdf.cell(0, 5, f"{i:02d}", align="L")
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 8, sec["heading"], align="L")
        pdf.ln(2)

        # Body
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(71, 85, 105)   # slate-600
        pdf.multi_cell(0, 6.5, sec["body"], align="L")
        pdf.ln(10)

        # Thin rule between sections
        if i < len(SECTIONS):
            pdf.set_draw_color(241, 245, 249)  # slate-100
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(10)

    pdf.output(out_path)
    print(f"PDF saved -> {out_path}")


if __name__ == "__main__":
    build_pdf()
