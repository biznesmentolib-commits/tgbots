from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline_kb import portfolio_list_kb, back_kb
from database import db

router = Router()

@router.callback_query(F.data == "portfolio")
async def show_portfolio_list(callback: CallbackQuery):
    items = await db.get_portfolio()
    if not items:
        text = "Hozircha portfolio mavjud emas. 😔"
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=back_kb("main_menu"))
        else:
            await callback.message.edit_text(text, reply_markup=back_kb("main_menu"))
    else:
        text = "🖼 <b>Bizning ishlarimiz (Portfolio):</b>\nKo'rish uchun birortasini tanlang:"
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=portfolio_list_kb(items), parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=portfolio_list_kb(items), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("portfolio_"))
async def show_portfolio_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    item = await db.get_portfolio_item(item_id)
    
    if not item:
        await callback.answer("Ma'lumot topilmadi!", show_alert=True)
        return
        
    text = (f"🖼 <b>{item['title']}</b>\n\n"
            f"📝 {item['description']}")
            
    if item['image_file_id']:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=item['image_file_id'], 
            caption=text, 
            reply_markup=back_kb("portfolio"),
            parse_mode="HTML"
        )
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=back_kb("portfolio"), parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=back_kb("portfolio"), parse_mode="HTML")
            
    await callback.answer()
