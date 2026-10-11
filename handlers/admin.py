from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline_kb import admin_menu_kb, delete_kb, back_kb, order_status_kb
from database import db
import os

router = Router()

# ========== FSM States ==========

class AdminServiceState(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()

class AdminPortfolioState(StatesGroup):
    title = State()
    description = State()
    image = State()

class AdminContactState(StatesGroup):
    type = State()
    value = State()

# ========== Admin tekshiruvi ==========

def is_admin(user_id):
    admin_id = os.getenv("ADMIN_ID")
    return str(user_id) == str(admin_id)

# ========== Admin menyu ==========

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("👑 Admin panelga xush kelibsiz!", reply_markup=admin_menu_kb())
    else:
        await message.answer("Sizda admin huquqlari yo'q.")

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q!", show_alert=True)
    await state.clear()
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer("👑 Admin panel:", reply_markup=admin_menu_kb())
    else:
        await callback.message.edit_text("👑 Admin panel:", reply_markup=admin_menu_kb())
    await callback.answer()

# ========== Xizmat qo'shish ==========

@router.callback_query(F.data == "admin_add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text(
        "➕ <b>Yangi xizmat qo'shish</b>\n\nXizmat nomini kiriting:",
        reply_markup=back_kb("admin_menu"), parse_mode="HTML"
    )
    await state.set_state(AdminServiceState.name)
    await callback.answer()

@router.message(AdminServiceState.name)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Xizmat haqida ma'lumot (description) kiriting:")
    await state.set_state(AdminServiceState.description)

@router.message(AdminServiceState.description)
async def add_service_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 Xizmat narxini kiriting (masalan: 100,000 so'm):")
    await state.set_state(AdminServiceState.price)

@router.message(AdminServiceState.price)
async def add_service_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("🖼 Xizmat uchun rasm yuboring (yoki rasmsiz davom etish uchun /skip bosing):")
    await state.set_state(AdminServiceState.image)

@router.message(AdminServiceState.image)
async def add_service_image(message: Message, state: FSMContext):
    data = await state.get_data()
    image_url = None
    
    if message.photo:
        image_url = message.photo[-1].file_id
    elif message.text == "/skip":
        pass
    else:
        await message.answer("Iltimos, rasm yuboring yoki /skip tugmasini bosing.")
        return
        
    await db.add_service(data['name'], data['description'], data['price'], image_url)
    await message.answer("✅ Xizmat muvaffaqiyatli qo'shildi!", reply_markup=admin_menu_kb())
    await state.clear()

# ========== Xizmatlarni boshqarish ==========

@router.callback_query(F.data == "admin_manage_services")
async def manage_services(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    services = await db.get_services(active_only=False)
    if not services:
        await callback.message.edit_text("Xizmatlar ro'yxati bo'sh.", reply_markup=back_kb("admin_menu"))
        await callback.answer()
        return
    
    text = "🛠 <b>Xizmatlarni boshqarish:</b>\n\n"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for s in services:
        status = "✅" if s['is_active'] else "❌"
        builder.button(text=f"{status} {s['name']}", callback_data=f"admin_service_{s['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_service_"))
async def admin_service_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    service_id = int(callback.data.split("_")[2])
    service = await db.get_service(service_id)
    if not service:
        await callback.answer("Xizmat topilmadi!", show_alert=True)
        return
    
    status = "Faol ✅" if service['is_active'] else "Nofaol ❌"
    text = (f"🛠 <b>{service['name']}</b>\n\n"
            f"📝 {service['description']}\n"
            f"💰 Narxi: {service['price']}\n"
            f"📌 Holati: {status}")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    if service['is_active']:
        builder.button(text="❌ O'chirish (nofaol)", callback_data=f"toggle_service_{service_id}_0")
    else:
        builder.button(text="✅ Yoqish (faol)", callback_data=f"toggle_service_{service_id}_1")
    builder.button(text="🗑 O'chirish (butunlay)", callback_data=f"delete_services_{service_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_manage_services")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_service_"))
async def toggle_service(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    parts = callback.data.split("_")
    service_id = int(parts[2])
    new_status = int(parts[3])
    await db.update_service(service_id, is_active=new_status)
    status_text = "faol ✅" if new_status else "nofaol ❌"
    await callback.answer(f"Xizmat {status_text} qilindi!", show_alert=True)
    # Sahifani yangilash
    await admin_service_detail(callback)

@router.callback_query(F.data.startswith("delete_services_"))
async def delete_service_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    service_id = int(callback.data.split("_")[2])
    await db.delete_service(service_id)
    await callback.answer("🗑 Xizmat o'chirildi!", show_alert=True)
    await manage_services(callback)

# ========== Buyurtmalarni boshqarish ==========

@router.callback_query(F.data == "admin_orders")
async def admin_orders_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    orders = await db.get_orders()
    if not orders:
        await callback.message.edit_text("📦 Buyurtmalar yo'q.", reply_markup=back_kb("admin_menu"))
        await callback.answer()
        return
    
    status_emoji = {
        "new": "🆕",
        "in_progress": "🟡",
        "completed": "✅",
        "cancelled": "❌"
    }
    
    text = "📦 <b>Oxirgi buyurtmalar:</b>\n\n"
    for o in orders[:15]:
        emoji = status_emoji.get(o['status'], '❓')
        text += (f"{emoji} <b>#{o['id']}</b> | {o['service_name']}\n"
                 f"   👤 {o['user_name']} | 📞 {o['user_phone']}\n"
                 f"   📅 {o['created_at']}\n\n")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for o in orders[:10]:
        builder.button(text=f"#{o['id']} - {o['service_name']}", callback_data=f"admin_order_{o['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_order_"))
async def admin_order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    order_id = int(callback.data.split("_")[2])
    orders = await db.get_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        await callback.answer("Buyurtma topilmadi!", show_alert=True)
        return
    
    status_text = {
        "new": "🆕 Yangi",
        "in_progress": "🟡 Jarayonda",
        "completed": "✅ Yakunlandi",
        "cancelled": "❌ Bekor qilindi"
    }.get(order['status'], order['status'])
    
    text = (f"📦 <b>Buyurtma #{order['id']}</b>\n\n"
            f"🛠 Xizmat: {order['service_name']}\n"
            f"👤 Mijoz: {order['user_name']}\n"
            f"📞 Telefon: {order['user_phone']}\n"
            f"📌 Status: {status_text}\n"
            f"📅 Sana: {order['created_at']}\n\n"
            f"Statusni o'zgartirish:")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🟡 Jarayonda", callback_data=f"status_in_progress_{order_id}")
    builder.button(text="✅ Yakunlandi", callback_data=f"status_completed_{order_id}")
    builder.button(text="❌ Bekor qilindi", callback_data=f"status_cancelled_{order_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_orders")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("status_"))
async def update_order_status_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    
    parts = callback.data.split("_")
    # status_in_progress_5 -> status=in_progress, order_id=5
    # status_completed_5 -> status=completed, order_id=5
    if parts[1] == "in":
        status = "in_progress"
        order_id = int(parts[3])
    else:
        status = parts[1]
        order_id = int(parts[2])
        
    await db.update_order_status(order_id, status)
    
    status_text = {
        "in_progress": "🟡 Jarayonda",
        "completed": "✅ Yakunlandi",
        "cancelled": "❌ Bekor qilindi"
    }.get(status, status)
    
    await callback.answer(f"Status '{status_text}' ga o'zgartirildi!", show_alert=True)
    
    # Sahifani yangilash
    callback.data = f"admin_order_{order_id}"
    await admin_order_detail(callback)

# ========== Portfolio qo'shish ==========

@router.callback_query(F.data == "admin_add_portfolio")
async def add_portfolio_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text(
        "➕ <b>Yangi portfolio qo'shish</b>\n\nIsh nomini (sarlavha) kiriting:",
        reply_markup=back_kb("admin_menu"), parse_mode="HTML"
    )
    await state.set_state(AdminPortfolioState.title)
    await callback.answer()

@router.message(AdminPortfolioState.title)
async def add_portfolio_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Ish haqida qisqacha ma'lumot kiriting:")
    await state.set_state(AdminPortfolioState.description)

@router.message(AdminPortfolioState.description)
async def add_portfolio_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("🖼 Ish rasmi yuboring (yoki /skip bosing):")
    await state.set_state(AdminPortfolioState.image)

@router.message(AdminPortfolioState.image)
async def add_portfolio_image(message: Message, state: FSMContext):
    data = await state.get_data()
    image_file_id = None
    
    if message.photo:
        image_file_id = message.photo[-1].file_id
    elif message.text == "/skip":
        pass
    else:
        await message.answer("Iltimos, rasm yuboring yoki /skip bosing.")
        return
    
    await db.add_portfolio(data['title'], data['description'], image_file_id)
    await message.answer("✅ Portfolio muvaffaqiyatli qo'shildi!", reply_markup=admin_menu_kb())
    await state.clear()

# ========== Portfolioni boshqarish ==========

@router.callback_query(F.data == "admin_manage_portfolio")
async def manage_portfolio(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    items = await db.get_portfolio()
    if not items:
        await callback.message.edit_text("Portfolio bo'sh.", reply_markup=back_kb("admin_menu"))
        await callback.answer()
        return
    
    text = "🖼 <b>Portfolioni boshqarish:</b>\n\n"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=f"🖼 {item['title']}", callback_data=f"admin_portfolio_{item['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_portfolio_"))
async def admin_portfolio_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    item = await db.get_portfolio_item(item_id)
    if not item:
        await callback.answer("Topilmadi!", show_alert=True)
        return
    
    text = (f"🖼 <b>{item['title']}</b>\n\n"
            f"📝 {item['description']}\n"
            f"📅 {item['created_at']}")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"delete_portfolio_{item_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_manage_portfolio")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("delete_portfolio_"))
async def delete_portfolio_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    item_id = int(callback.data.split("_")[2])
    await db.delete_portfolio(item_id)
    await callback.answer("🗑 Portfolio o'chirildi!", show_alert=True)
    await manage_portfolio(callback)

# ========== Aloqa qo'shish ==========

@router.callback_query(F.data == "admin_add_contact")
async def add_contact_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Telefon", callback_data="contact_type_phone")
    builder.button(text="✈️ Telegram", callback_data="contact_type_telegram")
    builder.button(text="📷 Instagram", callback_data="contact_type_instagram")
    builder.button(text="📍 Manzil", callback_data="contact_type_address")
    builder.button(text="🌐 Veb-sayt", callback_data="contact_type_website")
    builder.button(text="⬅️ Orqaga", callback_data="admin_menu")
    builder.adjust(2, 2, 1, 1)
    
    await callback.message.edit_text(
        "➕ <b>Yangi aloqa qo'shish</b>\n\nAloqa turini tanlang:",
        reply_markup=builder.as_markup(), parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contact_type_"))
async def contact_type_selected(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    contact_type = callback.data.split("_")[2]
    await state.update_data(contact_type=contact_type)
    
    hints = {
        "phone": "Telefon raqamingizni kiriting (masalan: +998901234567):",
        "telegram": "Telegram havolangizni kiriting (masalan: https://t.me/username):",
        "instagram": "Instagram havolangizni kiriting (masalan: https://instagram.com/username):",
        "address": "Manzilingizni kiriting:",
        "website": "Veb-sayt manzilini kiriting (masalan: https://example.com):"
    }
    
    await callback.message.edit_text(hints.get(contact_type, "Qiymatini kiriting:"),
                                      reply_markup=back_kb("admin_menu"))
    await state.set_state(AdminContactState.value)
    await callback.answer()

@router.message(AdminContactState.value)
async def add_contact_value(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_contact(data['contact_type'], message.text)
    await message.answer("✅ Aloqa ma'lumoti muvaffaqiyatli qo'shildi!", reply_markup=admin_menu_kb())
    await state.clear()

# ========== Aloqalarni boshqarish ==========

@router.callback_query(F.data == "admin_manage_contacts")
async def manage_contacts(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    contacts = await db.get_contacts()
    if not contacts:
        await callback.message.edit_text("Aloqa ma'lumotlari yo'q.", reply_markup=back_kb("admin_menu"))
        await callback.answer()
        return
    
    type_emoji = {
        "phone": "📞",
        "telegram": "✈️",
        "instagram": "📷",
        "address": "📍",
        "website": "🌐"
    }
    
    text = "📞 <b>Aloqa ma'lumotlarini boshqarish:</b>\n\n"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for c in contacts:
        emoji = type_emoji.get(c['type'], '📎')
        builder.button(text=f"{emoji} {c['type']}: {c['value'][:30]}", callback_data=f"admin_contact_{c['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_contact_"))
async def admin_contact_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    contact_id = int(callback.data.split("_")[2])
    contacts = await db.get_contacts()
    contact = next((c for c in contacts if c['id'] == contact_id), None)
    if not contact:
        await callback.answer("Topilmadi!", show_alert=True)
        return
    
    type_names = {
        "phone": "📞 Telefon",
        "telegram": "✈️ Telegram",
        "instagram": "📷 Instagram",
        "address": "📍 Manzil",
        "website": "🌐 Veb-sayt"
    }
    
    text = (f"<b>{type_names.get(contact['type'], contact['type'])}</b>\n\n"
            f"📎 Qiymat: {contact['value']}")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"delete_contact_{contact_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_manage_contacts")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("delete_contact_"))
async def delete_contact_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    contact_id = int(callback.data.split("_")[2])
    await db.delete_contact(contact_id)
    await callback.answer("🗑 Aloqa ma'lumoti o'chirildi!", show_alert=True)
    await manage_contacts(callback)
