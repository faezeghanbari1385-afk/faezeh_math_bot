from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import pytesseract, openai, os, re, sympy as sp

OPENAI_API_KEY = "کلید_OpenAI_خودت"
TELEGRAM_TOKEN = "توکن_تلگرام_خودت"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

def ocr_from_image(path):
    img = Image.open(path).convert("L")
    text = pytesseract.image_to_string(img, lang="eng")
    return text

def parse_question(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    options, question = [], []
    for l in lines:
        if re.match(r"^[A-D]\b|^[A-D]\.|^\d\)", l):
            options.append(l)
        else:
            question.append(l)
    return " ".join(question), options

def ask_ai(question, options):
    sysmsg = "تو یک حل‌کننده تست ریاضی دقیق هستی. فقط برچسب گزینه درست را برگردان (مثل A یا 2)."
    usermsg = f"سؤال: {question}\nگزینه‌ها:\n" + "\n".join(options)
    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sysmsg},
            {"role": "user", "content": usermsg}
        ],
        max_tokens=5,
        temperature=0
    )
    return r["choices"][0]["message"]["content"].strip()

def solve_question(question, options):
    try:
        x = sp.symbols("x")
        m = re.search(r"(.+)=\s*(.+)", question)
        if m:
            sol = sp.solve(sp.Eq(sp.sympify(m.group(1)), sp.sympify(m.group(2))), x)
            for s in sol:
                for o in options:
                    if str(s) in o:
                        return o
    except Exception:
        pass
    return ask_ai(question, options)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام فائزۀ عزیز 🌸 عکس تست رو بفرست تا جواب درست رو بگم 😎")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    path = "temp.jpg"
    await file.download_to_drive(path)
    text = ocr_from_image(path)
    question, options = parse_question(text)
    if not options:
        await update.message.reply_text("نتونستم گزینه‌ها رو بخونم 😔 لطفاً عکس واضح‌تر بفرست 🌿")
        return
    answer = solve_question(question, options)
    await update.message.reply_text(f"پاسخ: {answer}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("✅ بات در حال اجراست...")
app.run_polling()
