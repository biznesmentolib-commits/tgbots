from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards.inline_kb import main_menu_kb, back_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
            "Bizning xizmatlar botimizga xush kelibsiz. \n"
            "Quyidagi menyudan kerakli bo'limni tanlang:")
    await message.answer(text, reply_markup=main_menu_kb())

@router.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery):
    text = ("Bosh menyu 🏠\n"
            "Quyidagi bo'limlardan birini tanlang:")
    if callback.message.text:
        await callback.message.edit_text(text, reply_markup=main_menu_kb())
    else:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "about")
async def process_about(callback: CallbackQuery):
    text = ("ℹ️ <b>Biz haqimizda</b>\n\n"
            "Biz mijozlarimizga eng yaxshi xizmatlarni taqdim etamiz. "
            "Sifatli ish va hamyonbop narxlar - bizning ustuvor vazifamizdir.\n\n"
            "Bot orqali xizmatlar bilan tanishishingiz va buyurtma berishingiz mumkin.")
    
    if callback.message.text:
        await callback.message.edit_text(text, reply_markup=back_kb("main_menu"), parse_mode="HTML")
    else:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=back_kb("main_menu"), parse_mode="HTML")
    await callback.answer()
