from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline_kb import confirm_kb, back_kb, services_list_kb, order_status_kb
from database import db
import os

router = Router()

class OrderState(StatesGroup):
    choosing_service = State()
    waiting_name = State()
    waiting_phone = State()
    confirm = State()

@router.callback_query(F.data == "make_order")
async def start_make_order(callback: CallbackQuery, state: FSMContext):
    services = await db.get_services(active_only=True)
    if not services:
        await callback.answer("Hozircha xizmatlar mavjud emas.", show_alert=True)
        return
        
    text = "Buyurtma berish uchun quyidagi xizmatlardan birini tanlang:"
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=services_list_kb(services))
    else:
        await callback.message.edit_text(text, reply_markup=services_list_kb(services))
    await state.set_state(OrderState.choosing_service)
    await callback.answer()

@router.callback_query(F.data.startswith("order_"))
async def start_order(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    service = await db.get_service(service_id)
    
    if not service:
        await callback.answer("Xizmat topilmadi!", show_alert=True)
        return
        
    await state.update_data(service_id=service_id, service_name=service['name'], service_price=service['price'])
    
    text = f"Siz <b>{service['name']}</b> xizmatini tanladingiz.\n\nIltimos, ismingizni kiriting:"
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, parse_mode="HTML")
        
    await state.set_state(OrderState.waiting_name)
    await callback.answer()

@router.message(OrderState.waiting_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await message.answer("Rahmat! Endi telefon raqamingizni kiriting (masalan: +998901234567):")
    await state.set_state(OrderState.waiting_phone)

@router.message(OrderState.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(user_phone=message.text)
    data = await state.get_data()
    
    text = (f"📋 <b>Buyurtma ma'lumotlari:</b>\n\n"
            f"🛠 Xizmat: {data['service_name']}\n"
            f"💰 Narxi: {data['service_price']}\n"
            f"👤 Ism: {data['user_name']}\n"
            f"📞 Telefon: {data['user_phone']}\n\n"
            f"Barcha ma'lumotlar to'g'rimi? Tasdiqlaysizmi?")
            
    await message.answer(text, reply_markup=confirm_kb("order"), parse_mode="HTML")
    await state.set_state(OrderState.confirm)

@router.callback_query(OrderState.confirm, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    
    order_id = await db.add_order(
        user_id=user_id,
        user_name=data['user_name'],
        user_phone=data['user_phone'],
        service_id=data['service_id']
    )
    
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        admin_text = (f"🆕 <b>Yangi buyurtma!</b> #{order_id}\n\n"
                      f"🛠 Xizmat: {data['service_name']}\n"
                      f"👤 Mijoz: {data['user_name']}\n"
                      f"📞 Telefon: {data['user_phone']}\n\n"
                      f"Telegram profile: <a href='tg://user?id={user_id}'>Profilga o'tish</a>")
        try:
            await callback.bot.send_message(
                chat_id=admin_id, 
                text=admin_text, 
                reply_markup=order_status_kb(order_id),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Adminga xabar yuborishda xatolik: {e}")

    await callback.message.edit_text("✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.", reply_markup=back_kb("main_menu"))
    await state.clear()
    await callback.answer()

@router.callback_query(OrderState.confirm, F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=back_kb("main_menu"))
    await state.clear()
    await callback.answer()
