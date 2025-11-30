from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import re


def markdown_to_reportlab(text: str) -> str:
    """
    Convert simple markdown **bold** into <b>bold</b> for ReportLab.
    """
    # **something** -> <b>something</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def generate_pdf(input_file, output_file):
    # Read AI summary from file
    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Convert markdown bold (**text**) to <b>text</b>
    raw_text = markdown_to_reportlab(raw_text)

    # Create the PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    title_style = styles["Title"]

    story = []

    # Main title
    story.append(Paragraph("AI-Generated Sales Report Summary", title_style))
    story.append(Spacer(1, 20))

    # Split into paragraphs on blank lines
    paragraphs = raw_text.split("\n\n")

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Allow line breaks inside the paragraph
        para = para.replace("\n", "<br/>")

        story.append(Paragraph(para, normal_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    print("PDF generated:", output_file)


if __name__ == "__main__":
    generate_pdf("ai_summary.txt", "AI_Report.pdf")
