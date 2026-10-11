# Telegram Xizmatlar Boti

Bu Telegram bot turli xizmat ko'rsatish sohalari (masalan, tozalash, ta'mirlash, dizayn, va hk) uchun mo'ljallangan. U orqali mijozlar xizmatlar bilan tanishishi, portfolioni ko'rishi va buyurtma berishi mumkin.

## 🛠 Texnologiyalar
- Python 3.10+
- aiogram 3.x
- aiosqlite (SQLite)
- python-dotenv

## ⚙️ O'rnatish bo'yicha qo'llanma

### 1. BotFather'dan token olish
1. Telegramda `@BotFather` ni toping.
2. `/newbot` buyrug'ini yuboring.
3. Bot nomini (Name) va username (masalan, `mening_xizmat_bot`) kiriting.
4. BotFather sizga **HTTP API Token** beradi. Uni nusxalab oling.

### 2. Loyihani sozlash
1. Repozitoriyni klonlang yoki arxivni yuklab oling.
2. Loyiha papkasida `.env` faylini yarating (`.env.example` dan nusxa olishingiz mumkin).
3. `.env` fayliga ma'lumotlarni kiriting:
```
BOT_TOKEN=BotFather_dan_olingan_token
ADMIN_ID=Sizning_telegram_id_raqamingiz
```
*Eslatma: O'z ID raqamingizni bilish uchun Telegramda `@userinfobot` kabi botlardan foydalanishingiz mumkin.*

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Ishga tushirish
```bash
python bot.py
```

## 👑 Admin panel qo'llanmasi
Botga admin sifatida kirganingizdan so'ng, `/admin` buyrug'ini yuborish orqali boshqaruv paneliga kirasiz.
Admin panel imkoniyatlari:
- **Xizmat qo'shish:** Yangi xizmat nomi, narxi, izohi va rasmini yuklash.
- **Buyurtmalar:** Mijozlar tomonidan kelib tushgan buyurtmalarni ko'rish va ularning statusini o'zgartirish (Jarayonda, Yakunlandi, Bekor qilindi).
- **Portfolio:** Qilingan ishlarni qo'shish.
- **Aloqa:** Ijtimoiy tarmoqlar yoki telefon raqamlarni qo'shish.

## 🌟 Bot imkoniyatlari ro'yxati
- 🛠 **Xizmatlar katalogi** (Rasm, ma'lumot va narx bilan)
- 📝 **Buyurtma berish** (Ism va telefon raqamini yig'ib olish)
- 🖼 **Portfolio** (Qilingan ishlar namunalarini ko'rish)
- 📞 **Aloqa** (Kompaniya bilan bog'lanish ma'lumotlari)
- 👑 **Admin panel** (Barcha ma'lumotlarni Telegram orqali boshqarish)
