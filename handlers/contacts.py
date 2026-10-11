from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline_kb import contacts_list_kb, back_kb
from database import db

router = Router()

@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    contacts = await db.get_contacts()
    
    if not contacts:
        text = "Hozircha aloqa ma'lumotlari kiritilmagan."
        await callback.message.edit_text(text, reply_markup=back_kb("main_menu"))
    else:
        text = "📞 <b>Biz bilan bog'lanish:</b>\nQuyidagi vositalar orqali biz bilan bog'lanishingiz mumkin:"
        
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=contacts_list_kb(contacts), parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=contacts_list_kb(contacts), parse_mode="HTML")
            
    await callback.answer()
