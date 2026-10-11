from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline_kb import services_list_kb, service_detail_kb, back_kb
from database import db

router = Router()

@router.callback_query(F.data == "services")
async def show_services(callback: CallbackQuery):
    services = await db.get_services(active_only=True)
    if not services:
        text = "Hozircha xizmatlar mavjud emas. 😔"
        await callback.message.edit_text(text, reply_markup=back_kb("main_menu"))
    else:
        text = "🛠 <b>Xizmatlar ro'yxati:</b>\nO'zingizga kerakli xizmatni tanlang:"
        await callback.message.edit_text(text, reply_markup=services_list_kb(services), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("service_"))
async def show_service_detail(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    service = await db.get_service(service_id)
    
    if not service:
        await callback.answer("Xizmat topilmadi!", show_alert=True)
        return
        
    text = (f"🛠 <b>{service['name']}</b>\n\n"
            f"📝 <b>Ma'lumot:</b> {service['description']}\n\n"
            f"💰 <b>Narxi:</b> {service['price']}")
            
    if service['image_url']:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=service['image_url'], 
            caption=text, 
            reply_markup=service_detail_kb(service_id),
            parse_mode="HTML"
        )
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=service_detail_kb(service_id), parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=service_detail_kb(service_id), parse_mode="HTML")
            
    await callback.answer()
