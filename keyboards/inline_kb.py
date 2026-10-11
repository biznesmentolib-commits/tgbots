from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛠 Xizmatlar", callback_data="services")
    builder.button(text="📝 Buyurtma berish", callback_data="make_order")
    builder.button(text="🖼 Portfolio", callback_data="portfolio")
    builder.button(text="📞 Aloqa", callback_data="contacts")
    builder.button(text="ℹ️ Biz haqimizda", callback_data="about")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def services_list_kb(services) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(text=service['name'], callback_data=f"service_{service['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def service_detail_kb(service_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Buyurtma berish", callback_data=f"order_{service_id}")
    builder.button(text="⬅️ Orqaga", callback_data="services")
    builder.adjust(1)
    return builder.as_markup()

def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Xizmat qo'shish", callback_data="admin_add_service")
    builder.button(text="🛠 Xizmatlarni boshqarish", callback_data="admin_manage_services")
    builder.button(text="📦 Buyurtmalar", callback_data="admin_orders")
    builder.button(text="➕ Portfolio qo'shish", callback_data="admin_add_portfolio")
    builder.button(text="🖼 Portfolioni boshqarish", callback_data="admin_manage_portfolio")
    builder.button(text="➕ Aloqa qo'shish", callback_data="admin_add_contact")
    builder.button(text="📞 Aloqalarni boshqarish", callback_data="admin_manage_contacts")
    builder.adjust(1)
    return builder.as_markup()

def order_status_kb(order_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Jarayonda", callback_data=f"status_in_progress_{order_id}")
    builder.button(text="Yakunlandi", callback_data=f"status_completed_{order_id}")
    builder.button(text="Bekor qilindi", callback_data=f"status_cancelled_{order_id}")
    builder.adjust(1)
    return builder.as_markup()

def back_kb(callback="main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data=callback)
    return builder.as_markup()

def confirm_kb(action) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"confirm_{action}")
    builder.button(text="❌ Bekor qilish", callback_data=f"cancel_{action}")
    builder.adjust(2)
    return builder.as_markup()

def portfolio_list_kb(portfolio_items) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in portfolio_items:
        builder.button(text=item['title'], callback_data=f"portfolio_{item['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def contacts_list_kb(contacts) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for contact in contacts:
        if contact['type'] == 'telegram':
            builder.button(text="Telegram", url=contact['value'])
        elif contact['type'] == 'instagram':
            builder.button(text="Instagram", url=contact['value'])
        else:
            builder.button(text=f"{contact['type']}: {contact['value']}", callback_data="none")
    builder.button(text="⬅️ Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def delete_kb(item_type, item_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 O'chirish", callback_data=f"delete_{item_type}_{item_id}")
    builder.button(text="⬅️ Orqaga", callback_data=f"admin_manage_{item_type}")
    builder.adjust(1)
    return builder.as_markup()
