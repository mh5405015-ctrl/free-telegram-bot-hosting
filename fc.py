import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# টেলিগ্রাম টোকেন এখানে বসাও
TOKEN = "8805661599:AAH_x4-RFP2GhksvCQvQFK-0-8zpACpNEVY"

# লোগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# মেনু বাটন জেনারেটর (নিচের বা স্থায়ী মেনু বাটনগুলোর জন্য)
def get_main_menu_keyboard():
  keyboard = [
      [
          InlineKeyboardButton("🔍 নতুন EIIN সার্চ", callback_data="menu_search"),
          InlineKeyboardButton("📢 ECSF Team", url="https://t.me/ecsf_team"),
      ],
      [
          InlineKeyboardButton(
              "🌐 Telegram Channel", url="https://t.me/bdincomehub1"
          )
      ],
  ]
  return InlineKeyboardMarkup(keyboard)


# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  welcome_text = (
      "🛡️ **ELITE CYBER SECURITY FORCE**\n"
      "CREATOR: EMON KHAN\n\n"
      "স্বাগতম! শিক্ষা প্রতিষ্ঠানের EIIN নম্বর দিয়ে শিক্ষক ও প্রতিষ্ঠানের তথ্য জানতে নিচের অপশনগুলো ব্যবহার করুন।"
  )
  await update.message.reply_text(
      welcome_text,
      reply_markup=get_main_menu_keyboard(),
      parse_mode="Markdown",
  )


# বাটন ক্লিক ও মেনু হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  data = query.data

  if data == "menu_search":
    context.user_data["waiting_for_eiin"] = True
    await query.message.reply_text(
        "📝 অনুগ্রহ করে শিক্ষা প্রতিষ্ঠানের **EIIN নম্বর** দিন (যেমন: `132096`):",
        parse_mode="Markdown",
    )

  elif data.startswith("nav_"):
    # পেজিনেশন নেভিগেশন (Next / Previous)
    parts = data.split("_")
    index = int(parts[1])

    teachers = context.user_data.get("teachers", [])
    eiin = context.user_data.get("current_eiin", "")
    institute_name = context.user_data.get("institute_name", "")

    if not teachers:
      await query.message.edit_text(
          "⚠️ সেশন মেয়াদোত্তীর্ণ হয়ে গেছে। দয়া করে আবার সার্চ করুন।"
      )
      return

    await send_teacher_page(query.message, teachers, index, eiin, institute_name, edit=True)


# নির্দিষ্ট শিক্ষকের পেজ এবং নেভিগেশন বাটনসহ মেসেজ পাঠানোর ফাংশন
async def send_teacher_page(
    message, teachers, index, eiin, institute_name, edit=False
):
  total = len(teachers)
  t = teachers[index]

  name_en = t.get("FullName", "N/A")
  name_bn = t.get("FullNameBn", "")
  desig = t.get("DesignationNameBn", "N/A")
  subject = t.get("SubjectName", "-")
  dob = str(t.get("DateofBirth", "-")).strip("'")
  mobile = t.get("MobileNo", "-")
  email = t.get("Email", "-")
  emp_id = t.get("EmpId", "-")
  img_url = t.get("image_url", "")

  caption = (
      f"🏫 **প্রতিষ্ঠান:** {institute_name}\n"
      f"🆔 **EIIN:** `{eiin}`\n\n"
      f"👤 **শিক্ষক ({index + 1} / {total})**\n"
      f"• **নাম:** {name_en} ({name_bn})\n"
      f"• **পদবি:** `{desig}`\n"
      f"• **বিষয়:** {subject}\n"
      f"• **জন্মতারিখ:** {dob}\n"
      f"• **মোবাইল:** `{mobile}`\n"
      f"• **ইমেইল:** {email}\n"
      f"• **Emp ID:** `{emp_id}`"
  )

  # নেভিগেশন বাটন তৈরি (Previous / Next)
  nav_buttons = []
  if index > 0:
    nav_buttons.append(
        InlineKeyboardButton("⬅️ Previous", callback_data=f"nav_{index - 1}")
    )
  if index < total - 1:
    nav_buttons.append(
        InlineKeyboardButton("Next ➡️", callback_data=f"nav_{index + 1}")
    )

  # নিচে মেনু অপশনগুলোও যুক্ত করা
  keyboard = []
  if nav_buttons:
    keyboard.append(nav_buttons)

  keyboard.append([InlineKeyboardButton("🔍 নতুন সার্চ", callback_data="menu_search")])
  reply_markup = InlineKeyboardMarkup(keyboard)

  try:
    if img_url:
      if edit:
        # আগের মেসেজ ডিলিট করে ছবিসহ নতুন পাঠানো কারণ টেলিগ্রাম টেক্সট থেকে ফটোতে সরাসরি এডিট করতে দেয় না
        await message.delete()
        await message.reply_photo(
            photo=img_url, caption=caption, reply_markup=reply_markup, parse_mode="Markdown"
        )
      else:
        await message.reply_photo(
            photo=img_url, caption=caption, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
      if edit:
        await message.edit_text(
            text=caption, reply_markup=reply_markup, parse_mode="Markdown"
        )
      else:
        await message.reply_text(
            text=caption, reply_markup=reply_markup, parse_mode="Markdown"
        )
  except Exception as e:
    logger.error(f"Error sending page: {e}")
    # ফেইল করলে শুধু টেক্সট পাঠাবে
    if edit:
      await message.edit_text(
          text=caption, reply_markup=reply_markup, parse_mode="Markdown"
      )
    else:
      await message.reply_text(
          text=caption, reply_markup=reply_markup, parse_mode="Markdown"
      )


# মেসেজ হ্যান্ডলার (EIIN নম্বর গ্রহণ এবং API কল)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not context.user_data.get("waiting_for_eiin", False):
    return

  text = update.message.text.strip()

  if not text.isdigit():
    await update.message.reply_text(
        "⚠️ শুধু সংখ্যা দিয়ে সঠিক EIIN লিখুন (যেমন: 132096)।"
    )
    return

  context.user_data["waiting_for_eiin"] = False
  loading_msg = await update.message.reply_text("⏳ তথ্য ও ছবি খোঁজা হচ্ছে, একটু অপেক্ষা করুন...")

  api_url = f"https://teacher-details-api.devbd.workers.dev/?eiin={text}"

  try:
    response = requests.get(api_url, timeout=30)
    data = response.json()

    if not data.get("success") or not data.get("data"):
      await context.bot.edit_message_text(
          chat_id=update.effective_chat.id,
          message_id=loading_msg.message_id,
          text=(
              f"❌ এই EIIN (`{text}`) এর কোনো তথ্য পাওয়া যায়নি বা সার্ভারে সমস্যা"
              " রয়েছে।"
          ),
          parse_mode="Markdown",
      )
      return

    teachers = data["data"]
    institute_name = teachers[0].get(
        "InstituteInstituteNameInBangla", "অজানা প্রতিষ্ঠান"
    )

    # ইউজারের ডাটাতে সেভ করে রাখা যাতে Next/Previous কাজ করে
    context.user_data["teachers"] = teachers
    context.user_data["current_eiin"] = text
    context.user_data["institute_name"] = institute_name

    # প্রথম শিক্ষকের তথ্য পাঠানো (index 0)
    await loading_msg.delete()
    await send_teacher_page(update.message, teachers, 0, text, institute_name, edit=False)

  except Exception as e:
    logger.error(f"Error: {e}")
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=loading_msg.message_id,
        text="🚫 সার্ভারের সাথে সংযোগ ব্যর্থ হয়েছে। দয়া করে আবার চেষ্টা করুন।",
    )


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CallbackQueryHandler(button_handler))
  app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

  print("🤖 বট সফলভাবে চালু হয়েছে...")
  app.run_polling()


if __name__ == "main":
  main()

