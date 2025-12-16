from ast import Delete
import nextcord, re, httpx, certifi
from nextcord.ext import commands
from typing import Literal
import aiohttp
import requests
import json
from re import match    
import config
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import re
import cv2
from pyzbar.pyzbar import decode
from PIL import Image
import io
import qrcode
import asyncio
import numpy as np
import time
from nextcord.ui import TextInput, Modal, View, Button
from promptpay import qrcode
import os
import datetime
import tempfile
import pathlib
import urllib.parse
import string
import random
from nextcord import Embed, SlashOption,  Interaction, ButtonStyle

USERS_FILE = "database/users.json"
LOG_CHANNEL_ID = getattr(config, "logtopup", None)
OWNERS = config.OWNERS
intents = nextcord.Intents.all()
intents.messages = True
intents.message_content = True
bot = commands.Bot(help_command=None, intents=intents)
        
class URLModal(Modal):
    def __init__(self, user_id: int):
        super().__init__(title="Upload")
        self.user_id = user_id

        self.url_box = TextInput(
            label="ลิงก์ไฟล์",
            placeholder="https://tinyurl.com/....",
            required=True
        )
        self.add_item(self.url_box)

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "ของคนกดเท่านั้นนะเว้ย 😑", ephemeral=True
            )

        url = self.url_box.value.strip()
        
        if not url.startswith("https://tinyurl.com/"):
            return await interaction.response.send_message("ไม่สำเร็จรบกวนตรวจสอบลิ้งใหม่", ephemeral=True)
        # ส่งข้อความสถานะก่อน
        status_msg = await interaction.response.send_message(
            "⏳ กำลังทำการแปลงลิงก์...", 
            ephemeral=True
        )

        try:
            link = await upload_to_0x0(url)
        except Exception as e:
            return await status_msg.edit(content=f"❌ พังจ้า:\n{e}")

        # เปลี่ยนข้อความโหลดเป็นลิงก์จริง
        await status_msg.edit(content=f"[ดาวน์โหลดไฟล์ที่นี่]({link})")

        # ส่ง DM พร้อมปุ่มดาวน์โหลด
        embed = nextcord.Embed(
            description=f"กดปุ่มด้านล่างเพื่อดาวน์โหลดไฟล์\n\n[คลิกตรงนี้เพื่อดาวโหลด]({link})",
            color=0x2ecc71
        )

        view = nextcord.ui.View()
        view.add_item(
            nextcord.ui.Button(
                label="ลิ้งก์ดาวน์โหลด",
                style=nextcord.ButtonStyle.link,
                url=link
            )
        )

        await interaction.user.send(embed=embed, view=view)

class URLModal2(Modal):
    def __init__(self, user_id: int):
        super().__init__(title="Upload")
        self.user_id = user_id

        self.url_box = TextInput(
            label="ลิงก์ไฟล์",
            placeholder="https://tinyurl.com/....",
            required=True
        )
        self.add_item(self.url_box)

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "ของคนกดเท่านั้นนะเว้ย 😑", ephemeral=True
            )

        url = self.url_box.value.strip()
        
        if not url.startswith("https://tinyurl.com/"):
            return await interaction.response.send_message("ไม่เร็จรบกวนตรวจสอบลิ้งใหม่", ephemeral=True)

        await interaction.response.send_message(
            "⏳ กำลังทำการแปลงลิงก์...", 
            ephemeral=True
        )
        status_msg = await interaction.original_message()

        try:
            link = await create_tinyurl(url)
        except Exception as e:
            return await status_msg.edit(content=f"❌ พังจ้า:\n{e}")

        # เปลี่ยนข้อความโหลดเป็นลิงก์จริง
        await status_msg.edit(content=f"[ดาวน์โหลดไฟล์ที่นี่]({link})")

        # ส่ง DM พร้อมปุ่มดาวน์โหลด
        embed = nextcord.Embed(
            description=f"กดปุ่มด้านล่างเพื่อดาวน์โหลดไฟล์",
            color=0x2ecc71
        )

        view = nextcord.ui.View()
        view.add_item(
            nextcord.ui.Button(
                label="ลิ้งก์ดาวน์โหลด",
                style=nextcord.ButtonStyle.link,
                url=link
            )
        )

        await interaction.user.send(embed=embed, view=view)

# ============================
# ปุ่มเดียวเปิด modal
# ============================
class OneButton(View):
    def __init__(self):
        super().__init__(timeout=None)

        btn = Button(
            label="",
            emoji='<:m_blinkhuh:1447124330730225667>',
            style=ButtonStyle.primary,
            custom_id="upload_0x0"
        )
        btn.callback = self.open_modal
        self.add_item(btn)

    async def open_modal(self, interaction: Interaction):

        try:
            with open("database/users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
        except:
            users = {}

        user_data = users.get(str(interaction.user.id))

        # ❌ ไม่มีประวัติ ไม่ให้เปิดฟอร์ม
        if not user_data or "buymarket" not in user_data or len(user_data["buymarket"]) == 0:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    description="<a:No:1447122053185409034>: คุณไม่เคยซื้อสินค้าใดๆจากบอท ไม่สามารถใช้ปุ่มได้",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return
        modal = URLModal(interaction.user.id)
        await interaction.response.send_modal(modal)


# ============================
# slash command ส่ง embed + ปุ่มเดียว
# ============================
@bot.slash_command(name="pixbutton")
async def pixeldrain_button(interaction: Interaction):

    # เช็กแอดมิน
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            "❌ มึงไม่ใช่แอดมิน", ephemeral=True
        )

    embed = nextcord.Embed(
       title="กดปุ่มด้านล่างเพื่อดำเนินการต่อ",
        color=0x5865F2
    )
    embed.set_image(url="https://example.com/image.png")

    await interaction.channel.send(embed=embed, view=OneButton())
    await interaction.response.send_message( "อีโง่อีสันดานหมา", ephemeral=True)



# ============================
# ฟังก์ชันอัปโหลดจริง
# ============================
# ฟังก์ชันย่อ URL ผ่าน TinyURL API
async def create_tinyurl(url: str) -> str:
    tinyurl_api = "https://api.tinyurl.com/create"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 3bWjcmE52NLlq0OnJQkvylEUPPHcybTA9xBFlVCfOm41HIm2KBpct1n7tIyD"  # ใส่ API Key ที่ได้รับจาก TinyURL
    }

    async with aiohttp.ClientSession() as session:
        data = {
            "url": url
        }
        async with session.post(tinyurl_api, json=data, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"ย่อ URL ล้มเหลว (HTTP {response.status})")
            
            # ตรวจสอบว่า response มีข้อมูลอะไรบ้าง
            result = await response.json()

            # แสดงข้อมูล response เพื่อตรวจสอบ
            print(result)  # แสดงข้อมูล response

            # ตรวจสอบว่า 'tiny_url' หรือ 'tinyurl' อยู่ใน response หรือไม่
            try:
                return result['data']['tiny_url']  # เปลี่ยนเป็น 'tiny_url' หรือ 'tinyurl' ตามที่ API ส่ง
            except KeyError:
                raise Exception("ไม่พบ URL ที่ย่อจาก TinyURL API")

async def upload_to_0x0(url: str) -> str:
    headers = {
        "User-Agent": "curl/7.83.1"
    }

    async with aiohttp.ClientSession(headers=headers) as session:

        # โหลดไฟล์จากลิงก์
        async with session.get(url) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"โหลดไฟล์ไม่ได้ (HTTP {resp.status})\n{text}")

            raw_name = pathlib.Path(url).name
            filename = raw_name.split("?")[0] or "file"

            tmpdir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmpdir, filename)

            with open(tmp_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 64):
                    f.write(chunk)

        # อัปโหลดไป 0x0.st
        with open(tmp_path, "rb") as file:
            form = aiohttp.FormData()
            form.add_field("file", file, filename=filename)

            async with aiohttp.ClientSession(headers=headers) as upload_sess:
                async with upload_sess.post("https://0x0.st", data=form) as up:
                    text = await up.text()

                    if up.status != 200:
                        raise Exception(text)

                    link = text.strip()

        os.remove(tmp_path)
        os.rmdir(tmpdir)

        # ย่อ URL ผ่าน TinyURL
        short_link = await create_tinyurl(link)
        return short_link
    
class topupModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title='เติมเงินซองอั๋งเป๋า', timeout=None, custom_id='topup-modal')
        self.link = TextInput(
            label='ลิ้งค์ซองอั่งเปา',
            placeholder='https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.add_item(self.link)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            link = str(self.link.value).strip()
            if not link:
                return await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="❌ ข้อผิดพลาด",
                        description="กรุณากรอกลิงก์ซองให้ถูกต้อง",
                        color=nextcord.Color.red()
                    ),
                    ephemeral=True
                )

            # ✅ เริ่มโหลด
            reply_me = await interaction.response.send_message(embed=config.loading, ephemeral=True)

            # ✅ เรียก API ตรวจสอบซอง
            data = {
                'keyapi': config.KEY_API,
                'phone': config.phone,
                'gift_link': link
            }

            res = requests.post(config.API_TRUEWAALECT, data=data)
            print("[API RAW RESPONSE]", res.text)

            if res.status_code != 200:
                return await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="❌ ไม่สามารถเชื่อมต่อ API ได้",
                        description=f"สถานะ HTTP {res.status_code}",
                        color=nextcord.Color.red()
                    ),
                    ephemeral=True
                )

            response_data = res.json()
            print("[API RESPONSE]", response_data)

            # ✅ ตรวจสอบผลลัพธ์จาก API
            if response_data.get("status") != "success":
                msg = response_data.get("message", "")
                if "ลิงค์ซองของขวัญไม่ถูกต้อง" in str(msg):
                    friendly_msg = "❌ ซองอั่งเปาอาจหมดอายุ หรือไม่ถูกต้อง กรุณาตรวจสอบลิงก์อีกครั้ง"
                else:
                    friendly_msg = f"⚠️ ตรวจสอบไม่ผ่าน: `{msg}`"

                return await reply_me.edit(
                    embed=nextcord.Embed(
                        title="ตรวจสอบซองไม่สำเร็จ",
                        description=friendly_msg,
                        color=nextcord.Color.red()
                    )
                )

            # ✅ อ่านข้อมูลที่ API ส่งมา
            amount_raw = response_data.get("amount", 0)
            try:
                amount = float(amount_raw)
            except:
                amount = 0.0

            if amount <= 0:
                return await reply_me.edit(
                    embed=nextcord.Embed(
                        title="⚠️ ตรวจสอบไม่ผ่าน",
                        description="จำนวนเงินในซองไม่ถูกต้อง หรือซองหมดอายุ",
                        color=nextcord.Color.red()
                    )
                )

            phone = response_data.get("phone", config.phone)
            gift_link = response_data.get("gift_link", link)
            time_api = response_data.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # ✅ โหลด users.json
            user_file = "database/users.json"
            if os.path.exists(user_file):
                with open(user_file, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
            else:
                user_data = {}

            user_id = str(interaction.user.id)
            point = int(amount)

            new_transaction = {
                "topup": {
                    "name": "เติมผ่านซองอั๋งเปา",
                    "url": gift_link,
                    "amount": amount,
                    "time": time_api,
                    "phone": phone
                }
            }

            if user_id in user_data:
                user_data[user_id]["point"] = str(float(user_data[user_id]["point"]) + point)
                user_data[user_id]["all-point"] = str(float(user_data[user_id]["all-point"]) + point)
                user_data[user_id]["transaction"].append(new_transaction)
            else:
                user_data[user_id] = {
                    "userId": int(user_id),
                    "point": str(point),
                    "all-point": str(point),
                    "historybuy": [],
                    "transaction": [new_transaction],
                    "buyrole": [],
                    "buymarket": []
                }

            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, indent=4, ensure_ascii=False)

            # ✅ แจ้งผลสำเร็จ
            embed = nextcord.Embed(
                description=f'✅ **เติมเงินสำเร็จ จำนวน {point} บาท**',
                color=nextcord.Color.green()
            )
            await reply_me.edit(embed=embed)

            # ✅ ส่ง log
            log_embed = nextcord.Embed(
                title="🏦 ระบบแจ้งเตือนการเติมเงิน",
                description=f"👤 {interaction.user.mention}\n💸 {point} บาท\n⭐ ระบบ : ซองอั๋งเปา\n🔗 ||`{gift_link}`||",
                color=nextcord.Color.blue()
            )
            log_embed.set_author(name="ระบบขายสินค้า นายกัน", icon_url=interaction.guild.icon)
            log_embed.set_footer(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            if interaction.user.avatar:
                log_embed.set_thumbnail(url=interaction.user.avatar.url)

            log_channel = bot.get_channel(config.logtopup)
            if log_channel:
                await log_channel.send(embed=log_embed)

        except Exception as e:
            print("[TOPUP ERROR]", e)
            try:
                await reply_me.edit(
                    embed=nextcord.Embed(
                        title="❌ เกิดข้อผิดพลาด",
                        description=f"{e}",
                        color=nextcord.Color.red()
                    )
                )
            except:
                pass
        
PLANARIA_API = "https://www.planariashop.com/api/checkslip.php"
PLANARIA_KEY = "273bdfe95844615a5ae960a14907b2f5" 
RECEIVER_NAME = config.receiver_name
REQUIRED_NOTE = config.required_note

@bot.event
async def on_message(message: nextcord.Message):
    if message.author.bot:
        return

    if message.channel.id != config.slip_channel:
        return

    if not message.attachments:
        return

    attachment = message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image/"):
        await message.reply("❌ กรุณาส่ง **รูปสลิปธนาคารเท่านั้น**", mention_author=False)
        return

    async with message.channel.typing():
        processing_msg = await message.reply("🔎 กำลังตรวจสอบสลิป...", mention_author=False)

    try:
        # โหลดภาพจาก Discord
        img_bytes = await attachment.read()
        img = Image.open(io.BytesIO(img_bytes))

        # ถอด QR Code จากภาพ
        qr_data = decode(img)
        if not qr_data:
            await processing_msg.edit(content="⚠️ ไม่พบ QR Code ในสลิป กรุณาอัพโหลดภาพใหม่")
            print("[DEBUG] ❌ ไม่พบ QR Code ในภาพ")
            return

        qrcode_text = qr_data[0].data.decode("utf-8").strip()
        print(f"[PlanariaAPI] 📷 QR Code Extracted: {qrcode_text[:60]}...")

        # เตรียมข้อมูลส่ง API
        payload = {
            "keyapi": PLANARIA_KEY,
            "qrcode_text": qrcode_text
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(PLANARIA_API, data=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    print(f"[PlanariaAPI] 🌐 Response Status: {resp.status}")
                    text = await resp.text()
            except asyncio.TimeoutError:
                await processing_msg.edit(content="❌ การเชื่อมต่อ API ใช้เวลานานเกินไป (Timeout)")
                print("[PlanariaAPI] ❌ Timeout — ไม่มีการตอบกลับภายใน 20 วิ")
                return

        print(f"\n[PlanariaAPI] RAW RESPONSE:\n{text}")

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            await processing_msg.edit(content="❌ API ส่งข้อมูลไม่ถูกต้อง (ไม่ใช่ JSON)")
            print("[PlanariaAPI] ❌ JSON Decode Error")
            return

        # ตรวจผลลัพธ์จาก API
        if result.get("status") == "success":
            amount_raw = float(result.get("amount", 0))
            amount = int(amount_raw)  # ตัดเศษ

            payer = result["sender"]["name"]
            receiver = result["receiver"]["name"]
            slip_time = result["slip_time"]
            txid = result["transactionId"]
            bankname = result["sender"]["bank_name"]

            print(f"\n[ตรวจสลิปสำเร็จ] จาก: {payer}")
            print(f"[ตรวจสลิปสำเร็จ] ถึง: {receiver}")
            print(f"[ตรวจสลิปสำเร็จ] ยอด: {amount}.0 บาท")
            log_channel = bot.get_channel(config.logapi)
            if log_channel:
             embed_log = nextcord.Embed(
                title="[Check] RESPONSE SLIP",
                description=f"[ตรวจสลิปสำเร็จ] จาก: {payer}\n[ตรวจสลิปสำเร็จ] ถึง: {receiver}\n[ตรวจสลิปสำเร็จ] ยอด: {amount}.05 บาท",
                color=nextcord.Color.green())
            await log_channel.send(embed=embed_log)

            # ----------------------------
            #     ระบบกันสลิปซ้ำ
            # ----------------------------
            try:
                with open('database/used_slips.json', 'r', encoding='utf-8') as f:
                    used_slips = json.load(f)
            except:
                used_slips = {}

            if txid in used_slips:
                embed = nextcord.Embed(description=f'**สลิปนี้เคยถูกใช้ไปแล้ว/หรือถ้าคิดว่าบัคติดต่อแอดมิน**',color=nextcord.Color.red())
                embed.set_footer(text=f"โดย {message.author}", icon_url=message.author.display_avatar.url)
                await processing_msg.edit(content=None, embed=embed)
                print(f"[DUPLICATE] ❌ TXID ซ้ำ: {txid}")
                return

            # ตรวจชื่อผู้รับ
            if receiver.strip() not in [name.strip() for name in RECEIVER_NAME]:
                await processing_msg.edit(
                    content=f"⚠️ ชื่อผู้รับในสลิปไม่ตรงกับระบบ\n📄 ในสลิป: `{receiver}`\n✅ ต้องเป็น: `{', '.join(RECEIVER_NAME)}``"
                )
                print(f"[ชื่อไม่ตรง] ❌ {receiver} != `{', '.join(RECEIVER_NAME)}`")
                return

            # เพิ่มเงินเข้าระบบ
            with open('database/users.json', 'r', encoding='utf-8') as f:
                user_data = json.load(f)

            user_id = str(message.author.id)
            new_transaction = {
                "topup": {
                    "name": "เติมผ่านสลิปธนาคาร",
                    "amount": f"{amount:.1f}",
                    "time": slip_time,
                    "method": "bank slip",
                    "transactionId": txid
                }
            }

            if user_id in user_data:
                user_data[user_id]['point'] = str(float(user_data[user_id]['point']) + amount)
                user_data[user_id]['all-point'] = str(float(user_data[user_id]['all-point']) + amount)
                user_data[user_id]['transaction'].append(new_transaction)
            else:
                user_data[user_id] = {
                    "userId": int(user_id),
                    "point": str(amount),
                    "all-point": str(amount),
                    "historybuy": [],
                    "transaction": [new_transaction],
                    "buyrole": [],
                    "buymarket": []
                }

            with open('database/users.json', 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=4, ensure_ascii=False)

            # ----------------------------
            #   บันทึก TXID ที่ใช้แล้ว
            # ----------------------------
            used_slips[txid] = {
                "user": user_id,
                "time": slip_time
            }
            with open('database/used_slips.json', 'w', encoding='utf-8') as f:
                json.dump(used_slips, f, indent=4, ensure_ascii=False)

            # แสดงผล
            embed = nextcord.Embed(
                description=f'✅﹒**เติมเงินสำเร็จ จำนวน {amount:.1f} บาท**',
                color=nextcord.Color.green()
            )
            embed.set_footer(text=f"โดย {message.author}", icon_url=message.author.display_avatar.url)
            await processing_msg.edit(content=None, embed=embed)

            print(f"[SUCCESS] 💰 {message.author} +{amount}.0 บาท (TXID: {txid})")

            # Log แจ้งแอดมิน
            log_embed = nextcord.Embed(
                title="🏦 ระบบแจ้งเตือนการเติมเงิน",
                description=(
                    f"✅ สถานะ : ตรวจสลิปผ่าน\n"
                    f"👤 ผู้ใช้ : {message.author.mention}\n"
                    f"💸 จำนวน : {amount:.1f} บาท\n"
                    f"⭐ ระบบ : สลิปธนาคาร `{bankname}`\n"
                    f"🧾 TXID : `{txid}`"
                ),
                color=nextcord.Color.red()
            )
            log_embed.set_author(icon_url=message.guild.icon, name="ระบบขายสินค้า นายกัน")
            log_embed.set_footer(
                icon_url=config.emojidev,
                text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            if message.author.avatar:
                log_embed.set_thumbnail(url=message.author.avatar.url)

            log_channel = bot.get_channel(config.logtopup)
            if log_channel:
                await log_channel.send(embed=log_embed)

        else:
            err_msg = result.get("message")
            if isinstance(err_msg, dict):
                err_msg = err_msg.get("massage_th", "ข้อมูลไม่ถูกต้อง")
            await processing_msg.edit(content=f"⚠️ ตรวจสอบไม่ผ่าน: `{err_msg}`")
            print(f"[PlanariaAPI] ❌ ตรวจสอบไม่ผ่าน: {err_msg}")

    except Exception as e:
        await processing_msg.edit(content=f"❌ เกิดข้อผิดพลาด: `{e}`")
        print(f"[ERROR] {e}")

    await bot.process_commands(message)

class sellmarketui(nextcord.ui.Select):
  
  def __init__(self):
    options = []
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    for role in IDJSON:
      options.append(
          nextcord.SelectOption(label=IDJSON[role]['name'],
                                description=IDJSON[role]['description'],
                                value=role,
                                emoji=IDJSON[role]['emoji']))
    super().__init__(custom_id='sellmarketui',
                     placeholder='[ 🛒 สินค้าสำเร็จรูป ]',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=3)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed = nextcord.Embed()
      embed.description = f'''
E {IDJSON[selected]['name']}**
'''
      await message.edit(content=None,
                         embed=embed,
                         view=sellmarket(message=message, value=selected))
    else:
      
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed=nextcord.Embed(title=IDJSON[selected]['title'], description=f"```{IDJSON[selected]['embeddes']}```\n\nราคา: {IDJSON[selected]['price']}" , color=nextcord.Color.green()).set_image(url=IDJSON[selected]['image']).set_author(icon_url=interaction.guild.icon, name="ระบบขายสินค้า By PERXIO SHOP").set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await message.edit(content="รายละเอียดสินค้า",
                         embed=embed,
                         view=sellmarket(message=message, value=selected))
class sellmarket(nextcord.ui.View):
  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(
    label='',
    emoji='<:1505_yes:1447122291065356318>',
    custom_id='already',
    row=3
  )
  async def already(self, button: nextcord.Button, interaction: nextcord.Interaction):
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))

    if str(interaction.user.id) not in userJSON:
        embed = nextcord.Embed(description='🏦﹒เติมเงินเพื่อเปิดบัญชี', color=nextcord.Color.red())

    else:
        user_id = str(interaction.user.id)
        price = IDJSON[self.value]['price']

        if float(userJSON[user_id]['point']) >= price:
            # หักเงินออก
            userJSON[user_id]['point'] = str(float(userJSON[user_id]['point']) - price)

            # เพิ่มข้อมูลการสั่งซื้อ
            userJSON[user_id]['buymarket'].append({
                "market": {
                    "market": IDJSON[self.value]['name'],
                    "time": str(datetime.datetime.now()),
                    "code": IDJSON[self.value]['code']
                }
            })

            # บันทึกลงไฟล์
            json.dump(userJSON, open('./database/users.json', 'w', encoding='utf-8'),
                      indent=4, ensure_ascii=False)

            # โหลด point ปัจจุบันใหม่หลังหักเงิน
            with open('database/users.json', encoding="utf-8") as f:
                data_dict = json.load(f)
            transactions = data_dict[user_id]["point"]

            # ---- แจ้ง Log ----
            channelLog = bot.get_channel(config.logbuy)
            if channelLog:
                embed_log = nextcord.Embed(
                    title="📲 รายละเอียดการสั่งซื้อสินค้า",
                    description=(
                        f"```👤 คุณ {interaction.user.name}\n"
                        f"🛒 ซื้อสินค้า: {IDJSON[self.value]['name']}\n"
                        f"✅ สถานะการสั่งซื้อ : สั่งซื้อสำเร็จ\n"
                        f"💴 เงินลดลง : {price}\n"
                        f"💸 เงินคงเหลือ : {transactions}\n"
                        "```"
                    ),
                    color=nextcord.Color.green()
                )
                embed_log.set_author(icon_url=interaction.guild.icon, name="ระบบขายสินค้า นายกัน")
                embed_log.set_footer(
                    icon_url=config.emojidev,
                    text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                if interaction.user.avatar:
                    embed_log.set_thumbnail(url=interaction.user.avatar)
                else:
                    embed_log.set_thumbnail(url=None)

                await channelLog.send(embed=embed_log)

            # ---- ตอบกลับผู้ใช้ ----
            embed = nextcord.Embed(
                description=f'✅﹒สั่งซื้อสินค้าสำเร็จ **{IDJSON[self.value]["name"]}**',
                color=nextcord.Color.green()
            )
            embed.add_field(
                name="⭐ รายละเอียดเพิ่มเติม",
                value="✅ เก็บหลักฐานไว้สำหรับ การกู้คืนสินค้า กับแอดมิน \n(กู้คืนติดต่อ <@1069009480873951404>)",
                inline=False
            )
            embed.add_field(
                name="⭐ ลิงก์รับสินค้า",
                value=f"กดตรงนี้เพื่อรับโค้ด : [คลิกตรงนี้!!]({IDJSON[self.value]['code']})\n```{IDJSON[self.value]['code']}```",
                inline=False
            )
            embed.add_field(
                name="หากโหลดสินค้าไม่ได้",
                value=f"ถ้าโหลดสินค้าไม่ได้รบกวนน้ำลิ้งที่บอทให้ไปแปลงลิ้งในห้อง <#1438963795199525027>",
                inline=False
            )

            await self.message.edit(embed=embed, view=None, content=None)
            await interaction.user.send(embed=embed)

        else:
            # เงินไม่พอ
            missing = price - float(userJSON[user_id]['point'])
            embed = nextcord.Embed(
                description=f'<:squidwardcry:1447123635046187028>﹒เงินของท่านไม่เพียงพอ ขาดอีก ({missing:.2f}) บาท',
                color=nextcord.Color.red()
            )

    return await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='',
                      emoji='<:No:1447122053185409034>',
                      custom_id='cancel',
                      row=3)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='ยกเลิกการการสำเร็จแล้ว',embed=None,view=None)
class sellmarketui(nextcord.ui.Select):
  def __init__(self):
    options = []
    IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
    for role in IDJSON:
      options.append(
          nextcord.SelectOption(label=IDJSON[role]['name'],
                                description=IDJSON[role]['description'],
                                value=role,
                                emoji=IDJSON[role]['emoji']))
    super().__init__(custom_id='sellmarketui',
                     placeholder='[ 🛒 สินค้าสำเร็จรูป ]',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=3)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed = nextcord.Embed()
      embed.description = f'''
E {IDJSON[selected]['name']}**
'''
      await message.edit(content=None,
                         embed=embed,
                         view=sellmarket(message=message, value=selected))
    else:
      
      IDJSON = json.load(open('./database/market.json', 'r',
                                encoding='utf-8'))
      embed=nextcord.Embed(title=IDJSON[selected]['title'], description=f"```{IDJSON[selected]['embeddes']}```\nราคา: {IDJSON[selected]['price']}" , color=nextcord.Color.green()).set_image(url=IDJSON[selected]['image']).set_author(icon_url=interaction.guild.icon, name="ระบบขายสินค้า").set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      await message.edit(content="🟢 รายละเอียดสินค้า",
                         embed=embed,
                         view=sellmarket(message=message, value=selected))

class BankTopupModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="💵 เติมผ่านพร้อมเพย์", timeout=None, custom_id="banktopup-modal")

        self.amount = nextcord.ui.TextInput(
            label="จำนวนเงินที่ต้องการเติม (ขั้นต่ำ 20 บาท)",
            placeholder="เช่น 50",
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.add_item(self.amount)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            amount = float(self.amount.value)
            if amount < 20:
                embed = nextcord.Embed(
                    description="⚠️ จำนวนเงินขั้นต่ำ **20 บาท**",
                    color=nextcord.Color.red()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            final_amount = round(amount + 0.05, 2)

            encoded_number = urllib.parse.quote(config.phone)
            qr_url = f"https://promptpay.io/{encoded_number}/{final_amount:.2f}.png"

            # ✅ สร้าง Embed แสดง QR
            embed = nextcord.Embed(
                title="💵 สแกนเพื่อชำระผ่านพร้อมเพย์",
                description=(
                    f"💰 จำนวนที่คุณกรอก: **{amount:.2f} บาท**\n"
                    f"🧾 จำนวนที่ต้องโอนจริง: **{final_amount:.2f} บาท** *(บวก 0.05 สตางค์เพื่อระบุธุรกรรม)*\n\n"
                ),
                color=nextcord.Color.green()
            )
            embed.set_image(url=qr_url)
            embed.set_footer(text="ระบบจะตรวจสอบต่อเมื่อส่งสลิป")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    description="❌ กรุณากรอกจำนวนเงินเป็นตัวเลขเท่านั้น",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    description=f"❌ เกิดข้อผิดพลาด: {e}",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
class sellmarketui2(nextcord.ui.Select):
    def __init__(self):
        options = []
        IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
        for role in IDJSON:
            options.append(
                nextcord.SelectOption(
                    label=IDJSON[role]['name'],
                    description=IDJSON[role]['description'],
                    value=role,
                    emoji=IDJSON[role]['emoji']
                )
            )
        super().__init__(
            custom_id='sellmarketui',
            placeholder='เลือกสินค้าที่ต้องการ',
            min_values=1,
            max_values=1,
            options=options,
            row=3
        )

    async def callback(self, interaction: nextcord.Interaction):
        selected = self.values[0]
        IDJSON = json.load(open('./database/market.json', 'r', encoding='utf-8'))
        
        # ใช้ Embed เพื่อส่งข้อความยาว
        embed = nextcord.Embed(
            title=IDJSON[selected]['title'],
            description=f"```{IDJSON[selected]['embeddes']}```\nราคา: {IDJSON[selected]['price']}",
            color=nextcord.Color.green()
        ).set_image(url=IDJSON[selected]['image'])\
         .set_author(icon_url=interaction.guild.icon, name="ระบบขายสินค้า")\
         .set_footer(icon_url=config.emojidev, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        await interaction.response.send_message(content="🟢 รายละเอียดสินค้า", embed=embed)
class setupView2(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 50, commands.BucketType.member)

    # ปุ่มเติมเงิน 1
    @nextcord.ui.button(label='', emoji='<:T_wallet:1447119780422225922>', custom_id='topup0', row=1)
    async def topup0(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(topupModal())

    # ปุ่มเติมเงิน 2
    @nextcord.ui.button(label='', emoji='<:KBANK:1447119702433464381>', custom_id='topup1', row=1)
    async def topup1(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(BankTopupModal())

    # ปุ่มแสดงยอดเงิน
    @nextcord.ui.button(label='', emoji='<:Money:1447120406866694217>', custom_id='balance', row=1)
    async def balance(self, button: nextcord.Button, interaction: nextcord.Interaction):

        with open('./database/users.json', 'r', encoding='utf-8') as f:
            userJSON = json.load(f)

        user_id = str(interaction.user.id)

        if user_id not in userJSON:
            userJSON[user_id] = {
                "userId": int(user_id),
                "point": 0.00,
                "all-point": 0.00,
                "historybuy": [],
                "transaction": [],
                "buyrole": [],
                "buymarket": []
            }
            with open('./database/users.json', 'w', encoding='utf-8') as f:
                json.dump(userJSON, f, indent=4, ensure_ascii=False)

        embed = nextcord.Embed(
            description=f'<:Money:1447120406866694217>﹒ยอดเงินคงเหลือ **__{userJSON[user_id]["point"]}__** บาท\n',
            color=nextcord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ปุ่มเข้า Shop (ปุ่มนี้ต้องอยู่ระดับเดียวกับด้านบน!)
    @nextcord.ui.button(label='', emoji='<:Shop:1447124799297028257>', custom_id='shopp', row=1)
    async def shop(self, button: nextcord.Button, interaction: nextcord.Interaction):

        View = nextcord.ui.View()
        View.add_item(sellmarketui())  # เพิ่ม select ของคุณลงใน view ใหม่

        await interaction.response.send_message(view=View, ephemeral=True)

class setupVie(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 50, commands.BucketType.member)

    # ปุ่มเติมเงิน 1
    @nextcord.ui.button(label='', emoji='<:T_wallet:1447119780422225922>', custom_id='topup0', row=1)
    async def topup0(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(topupModal())

    # ปุ่มเติมเงิน 2
    @nextcord.ui.button(label='', emoji='<:KBANK:1447119702433464381>', custom_id='topup1', row=1)
    async def topup1(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(BankTopupModal())

    # ปุ่มแสดงยอดเงิน
    @nextcord.ui.button(label='', emoji='<:Money:1447120406866694217>', custom_id='balance', row=1)
    async def balance(self, button: nextcord.Button, interaction: nextcord.Interaction):

        with open('./database/users.json', 'r', encoding='utf-8') as f:
            userJSON = json.load(f)

        user_id = str(interaction.user.id)

        if user_id not in userJSON:
            userJSON[user_id] = {
                "userId": int(user_id),
                "point": 0.00,
                "all-point": 0.00,
                "historybuy": [],
                "transaction": [],
                "buyrole": [],
                "buymarket": []
            }
            with open('./database/users.json', 'w', encoding='utf-8') as f:
                json.dump(userJSON, f, indent=4, ensure_ascii=False)

        embed = nextcord.Embed(
            description=f'<:Money:1447120406866694217>﹒ยอดเงินคงเหลือ **__{userJSON[user_id]["point"]}__** บาท\n',
            color=nextcord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f'BOT NAME : {bot.user}')
    bot.add_view(setupView2())
    bot.add_view(OneButton())
    bot.add_view(SellRoleSelectMainView())
    bot.add_view(ClaimView())
    bot.add_view(AdminPanelView())

@bot.slash_command( description="🟢 ติดตั้งได้หมด")
async def setuptopup(interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.administrator:
           return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True)
        await interaction.channel.send(embed=nextcord.Embed(title="ร้านขายของสำเร็จรูป",color=nextcord.Color.red())
                                       .set_footer(icon_url=config.emojidev, text="© 2025 ARTY SHOPs All rights reserved")
                                       .set_image(url="https://images-ext-2.discordapp.net/external/k7VY7RvtGPIxcYWSjA9E4s2Aycotavp9Vc-hdrfs3M4/https/i.pinimg.com/originals/f5/03/64/f503648e3e879a1332d2111c88ce09c4.gif?width=1342&height=671"),
                                         view=setupView2())

class SellRoleSelectMainView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellmarketui())

MARKET_PATH = "./database/market.json"

# โหลดข้อมูลสินค้า
def load_market():
    if os.path.exists(MARKET_PATH):
        with open(MARKET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_market(data):
    with open(MARKET_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

OWNER_ID = "1069009480873951404"
@bot.slash_command(description="เพิ่มสินค้าในร้าน (เฉพาะแอดมิน)")
async def addshop(
    interaction: nextcord.Interaction,
    item_id: str,
    name: str,
    title: str,
    price: int,
    code: str,
    embeddes: str  = "",
    emoji: str = "🛒",
    image: str = "",
    description: str = ""
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True
        )
        return

    market = load_market()
    if item_id in market:
        return await interaction.response.send_message(f"❌ มีสินค้ารหัส `{item_id}` อยู่แล้ว", ephemeral=True)

    market[item_id] = {
        "name": name,
        "title": title,
        "embeddes": embeddes,
        "image": image,
        "description": description,
        "price": price,
        "emoji": emoji,
        "code": code
    }

    save_market(market)

    embed = nextcord.Embed(
        title="✅ เพิ่มสินค้าสำเร็จ",
        description=f"**{title}**\nรหัสสินค้า: `{item_id}`\nราคา: `{price} บาท`",
        color=nextcord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# -----------------------------
# 🗑️ คำสั่ง: ลบสินค้า
# -----------------------------
@bot.slash_command(description="ลบสินค้าออกจากร้าน (เฉพาะแอดมิน)")
async def deleteshop(interaction: nextcord.Interaction, item_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True
        )
        return

    market = load_market()
    if item_id not in market:
        return await interaction.response.send_message(f"❌ ไม่พบสินค้ารหัส `{item_id}`", ephemeral=True)

    removed = market.pop(item_id)
    save_market(market)

    embed = nextcord.Embed(
        title="🗑️ ลบสินค้าเรียบร้อย",
        description=f"**{removed['title']}** (`{item_id}`) ถูกลบออกจากร้านแล้ว",
        color=nextcord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="addpoint", description="💰 เพิ่มยอดเงินให้ผู้ใช้")
async def addpoint(interaction: nextcord.Interaction, member: nextcord.Member, amount: float):
    if not interaction.user.guild_permissions.administrator:
           return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True)

    try:
        user_id = str(member.id)
        users_file = "database/users.json"

        # โหลดไฟล์หรือสร้างใหม่
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        # ถ้าไม่มีบัญชี ให้สร้างบัญชีใหม่
        if user_id not in user_data:
            user_data[user_id] = {
                "userId": member.id,
                "point": str(amount),
                "all-point": str(amount),
                "historybuy": [],
                "transaction": [],
                "buyrole": [],
                "buymarket": []
            }
            action = "สร้างบัญชีใหม่และเพิ่มยอด"
        else:
            old_point = float(user_data[user_id].get("point", 0))
            user_data[user_id]["point"] = str(old_point + amount)
            all_point = float(user_data[user_id].get("all-point", 0))
            user_data[user_id]["all-point"] = str(all_point + amount)
            action = "เพิ่มยอดสำเร็จ"

        # บันทึกไฟล์
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False)

        # ส่ง DM แจ้งผู้ใช้
        embed_dm = nextcord.Embed(
            title="💸 แจ้งเตือนการเพิ่มยอดเงิน",
            description=f"คุณได้รับการเพิ่มยอดเงินจำนวน **{amount:.1f} บาท**\nโดย: {interaction.user.mention}",
            color=nextcord.Color.green()
        )
        try:
            await member.send(embed=embed_dm)
        except:
            pass  # กรณีปิด DM

        # ส่ง Log ไปห้องที่กำหนด
        log_channel = bot.get_channel(config.logtopup)
        if log_channel:
            embed_log = nextcord.Embed(
                title="💰 เพิ่มยอดเงินให้ผู้ใช้",
                description=f"👤 ผู้ใช้: {member.mention}\n💵 จำนวน: **+{amount:.1f} บาท**\n🛠️ ดำเนินการโดย: {interaction.user.mention}",
                color=nextcord.Color.green()
            )
            await log_channel.send(embed=embed_log)

        await interaction.response.send_message(f"✅ เพิ่มยอดให้ {member.mention} จำนวน {amount:.1f} บาทสำเร็จ", ephemeral=True)
        print(f"[ADDPOINT] {interaction.user} เพิ่ม {amount} บาทให้ {member}")

    except Exception as e:
        await interaction.response.send_message(f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True)
        print(f"[ADDPOINT ERROR] {e}")

@bot.slash_command(name="checkmoney", description="💰 ตรวจสอบยอดเงินของคุณ หรือของผู้ใช้คนอื่น")
async def checkmoney(
    interaction: nextcord.Interaction,
    member: nextcord.Member = nextcord.SlashOption(
        required=True,
        description="เลือกผู้ใช้ที่ต้องการตรวจสอบ (ถ้าไม่ใส่จะดูของตัวเอง)"
    )
):
    if not interaction.user.guild_permissions.administrator:
           return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True)

    try:
        # ถ้าไม่ได้ระบุ member → ตรวจของตัวเอง
        target = member or interaction.user
        user_id = str(target.id)

        users_file = "database/users.json"

        # โหลดไฟล์ข้อมูลผู้ใช้
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        else:
            user_data = {}

        # ตรวจว่ามีข้อมูลหรือยัง
        if user_id not in user_data:
            embed = nextcord.Embed(
                title="💸 ไม่มีข้อมูลบัญชี",
                description=f"🔍 ไม่พบบัญชีของ {target.mention}\n"
                            f"ระบบจะสร้างบัญชีใหม่เมื่อมีการเติมเงินครั้งแรก 💵",
                color=nextcord.Color.orange()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ดึงข้อมูล
        point = float(user_data[user_id].get("point", 0))
        all_point = float(user_data[user_id].get("all-point", 0))
        tx_count = len(user_data[user_id].get("transaction", []))

        embed = nextcord.Embed(
            title="💰 ข้อมูลยอดเงิน",
            description=(
                f"👤 ผู้ใช้: {target.mention}\n"
                f"💵 ยอดคงเหลือปัจจุบัน: **{point:,.2f} บาท**\n"
                f"💸 ยอดเติมสะสมทั้งหมด: **{all_point:,.2f} บาท**\n"
                f"🧾 จำนวนรายการธุรกรรม: `{tx_count}`"
            ),
            color=nextcord.Color.green()
        )
        embed.set_footer(text=f"เช็คเมื่อ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title="❌ เกิดข้อผิดพลาด",
                description=f"`{e}`",
                color=nextcord.Color.red()
            ),
            ephemeral=True
        )
        print(f"[CHECKMONEY ERROR] {e}")

@bot.slash_command(name="removepoint", description="💸 ลดยอดเงินของผู้ใช้")
async def removepoint(interaction: nextcord.Interaction, member: nextcord.Member, amount: float):
    if not interaction.user.guild_permissions.administrator:
           return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True)

    try:
        user_id = str(member.id)
        users_file = "database/users.json"

        try:
            with open(users_file, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        if user_id not in user_data:
            return await interaction.response.send_message(f"⚠️ ไม่พบข้อมูลของ {member.mention}", ephemeral=True)

        old_point = float(user_data[user_id].get("point", 0))
        new_point = max(old_point - amount, 0)  # กันค่าติดลบ
        user_data[user_id]["point"] = str(new_point)

        # บันทึกไฟล์
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False)

        # DM แจ้งผู้ใช้
        embed_dm = nextcord.Embed(
            title="💸 แจ้งเตือนการลดยอดเงิน",
            description=f"ยอดเงินของคุณถูกลด **-{amount:.1f} บาท**\nโดย: {interaction.user.mention}",
            color=nextcord.Color.red()
        )
        try:
            await member.send(embed=embed_dm)
        except:
            pass

        # Log แจ้งห้อง
        log_channel = bot.get_channel(config.logtopup)
        if log_channel:
            embed_log = nextcord.Embed(
                title="💳 ลดยอดเงินผู้ใช้",
                description=f"👤 ผู้ใช้: {member.mention}\n💰 จำนวน: **-{amount:.1f} บาท**\n🛠️ ดำเนินการโดย: {interaction.user.mention}",
                color=nextcord.Color.red()
            )
            await log_channel.send(embed=embed_log)

        await interaction.response.send_message(f"✅ ลดยอด {member.mention} จำนวน {amount:.1f} บาทสำเร็จ", ephemeral=True)
        print(f"[REMOVEPOINT] {interaction.user} ลบ {amount} บาทจาก {member}")

    except Exception as e:
        await interaction.response.send_message(f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True)
        print(f"[REMOVEPOINT ERROR] {e}")

@bot.slash_command( description="🟢 ")
async def setupsellbot(interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.administrator:
           return await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True)

        embed = nextcord.Embed(
            title="บริการขายของสำเร็จรูป",
            color=nextcord.Color.red()
        )
        embed.set_author(
            icon_url=interaction.guild.icon.url,
            name="ระบบขายสินค้า นายกัน"
        )
        embed.set_footer(
            icon_url=config.emojidev,
            text="© 2025 ARTY SHOPs All rights reserved"
        )
        embed.set_image(url="https://images-ext-2.discordapp.net/external/k7VY7RvtGPIxcYWSjA9E4s2Aycotavp9Vc-hdrfs3M4/https/i.pinimg.com/originals/f5/03/64/f503648e3e879a1332d2111c88ce09c4.gif?width=1342&height=671")

        await interaction.channel.send(embed=embed, view=SellRoleSelectMainView())

logsss = 1448293391493501022

class ClaimModal(nextcord.ui.Modal):
    def __init__(self, user_id):
        super().__init__("แบบฟอร์มเคลมสินค้า")
        self.user_id = user_id

        self.product_name = nextcord.ui.TextInput(
            label="ชื่อสินค้า",
            placeholder="กรอกชื่อสินค้าที่ต้องการเคลม",
            required=True,
            max_length=100
        )
        self.add_item(self.product_name)

        self.product_link = nextcord.ui.TextInput(
            label="ลิงก์สินค้า",
            placeholder="ลิงก์ที่ได้รับตอนซื้อ",
            required=True
        )
        self.add_item(self.product_link)

        self.problem = nextcord.ui.TextInput(
            label="ปัญหาที่เกิดขึ้น",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="อธิบายปัญหาที่พบ",
            required=True,
            max_length=400
        )
        self.add_item(self.problem)

    async def callback(self, interaction: nextcord.Interaction):

        # โหลด user database
        with open("database/users.json", "r", encoding="utf-8") as f:
            users = json.load(f)

        user_id = str(interaction.user.id)

        # ถ้าซื้อ → บันทึกข้อมูลเคลม
        claim_info = {
            "user": interaction.user.id,
            "name": self.product_name.value,
            "link": self.product_link.value,
            "problem": self.problem.value,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # ตอบกลับผู้ใช้
        embed = nextcord.Embed(
            description=(
                "ระบบได้รับเรื่องของคุณแล้ว"
                "กรุณารอแอดมินติดต่อกลับในเร็วๆนี้ "
            ),
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # ---------------------------
        # ส่ง log แจ้งแอดมิน
        # ---------------------------
        log_channel = interaction.client.get_channel(logsss)

        log_embed = nextcord.Embed(
            title="แจ้งเตือนเคลมสินค้าใหม่",
            color=nextcord.Color.orange(),
            timestamp=datetime.datetime.now()
        )
        log_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        log_embed.add_field(name="ผู้ใช้", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
        log_embed.add_field(name="ชื่อสินค้า", value=claim_info["name"], inline=False)
        log_embed.add_field(name="ลิงก์สินค้า", value=claim_info["link"], inline=False)
        log_embed.add_field(name="ปัญหาที่พบ", value=claim_info["problem"], inline=False)
        log_embed.add_field(name="เวลา", value=claim_info["time"], inline=False)

        await log_channel.send(f"{interaction.user.mention} ||<@&1420019312789422292>||",embed=log_embed)


class ClaimView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="", emoji="<:1715pepehelp:1448260984128016386>", style=nextcord.ButtonStyle.blurple, custom_id="claim_button")
    async def claim_btn(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        
        # โหลดข้อมูล users.json แบบ realtime
        try:
            with open("database/users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
        except:
            users = {}

        user_data = users.get(str(interaction.user.id))

        # ❌ ไม่มีประวัติ ไม่ให้เปิดฟอร์ม
        if not user_data or "buymarket" not in user_data or len(user_data["buymarket"]) == 0:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    description="<a:No:1447122053185409034>: คุณไม่เคยซื้อสินค้าใดๆจากบอท ไม่สามารถเคลมสินค้าได้",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return

        # ✔ มีประวัติ → เปิด Modal ได้ทันที
        modal = ClaimModal(interaction.user.id)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(
        label="",
        emoji="<a:Rainbow_ReadRules:1448315223802122343>",
        custom_id="ruleeeee"
    )
    async def claim_info(self, button, interaction: nextcord.Interaction):

        try:
            with open("database/users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
        except:
            users = {}

        user_data = users.get(str(interaction.user.id))

        # ❌ ไม่มีประวัติ ไม่ให้เปิดฟอร์ม
        if not user_data or "buymarket" not in user_data or len(user_data["buymarket"]) == 0:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    description="<a:No:1447122053185409034>: คุณไม่เคยซื้อสินค้าใดๆจากบอท ไม่สามารถอ่านรายระเอียดได้",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return

        text = (
            "**รายละเอียดการเคลม**\n\n"
            "> เปิดรับข้อความจากเซิฟเวอร์เนื่องจากอาจเป็นบอททักไปหรืออาจจะเป็นบัญชีจริงทักไป รบกวนเปิดตามรูปจะเปิดแค่ 2 อันด้านบนเท่านั้น ห้ามปิดโดยเด็ดขาด\n"
            "> \n"
            "> การเคลมสินค้าหากมีการทักไปแล้วไม่มีการตอบกลับภายใน 1 วัน จะถือว่า สิ้นสุดการเคลมแล้วแจ้งเคลมใหม่อีกครั้ง"
        )

        # ส่งข้อความ + รูปทันที
        files = [
            nextcord.File("image.png", filename="image.png"),
            nextcord.File("1image.png", filename="1image.png")
        ]
        await interaction.response.send_message(content=text, files=files, ephemeral=True)

@bot.slash_command()
async def claim(ctx):
    if not ctx.user.guild_permissions.administrator:
        return await ctx.response.send_message("❌ คุณไม่มีสิทธิ์ในการใช้คำสั่งนี้ (ต้องเป็นแอดมินเท่านั้น)", ephemeral=True)

    embed = nextcord.Embed(
        description="หากพบปัญหาเกี่ยวกับสินค้า สามารถกดปุ่มด้านล่างเพื่อส่งคำขอเคลมให้แอดมินตรวจสอบ รบกวนอ่านรายระเอียดก่อนในะครับ กดปุ่มสีเทาเพื่ออ่านลายระเอียด",
        color=nextcord.Color.blue()
    )
    await ctx.channel.send(embed=embed, view=ClaimView())


@bot.slash_command(name="adminpanel")
async def adminpanel(interaction: nextcord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ คุณไม่ใช่แอดมิน", ephemeral=True)

    embed = nextcord.Embed(
        description="เลือกเมนูที่ต้องการจัดการข้อมูลผู้ใช้",
        color=0x2F3136
    )
    await interaction.channel.send(embed=embed, view=AdminPanelView())
    await interaction.response.send_message("ควย", ephemeral=True)

class AdminPanelView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="", emoji="<a:apmoney1:1448616685761200240>", custom_id="fff")
    async def add_point(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: คุณไม่ใช่แอดมิน ไม่สามารถใช้งานได้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_message(
            "เลือกผู้ใช้ที่จะ **เพิ่มเงิน**",
            view=UserSelectView("add"),
            ephemeral=True
        )

    @nextcord.ui.button(label="", emoji="<a:DemonShit:1448616820964720701>", custom_id="ffrf")
    async def remove_point(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: คุณไม่ใช่แอดมิน ไม่สามารถใช้งานได้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.send_message(
            "เลือกผู้ใช้ที่จะ **ลบเงิน**",
            view=UserSelectView("remove"),
            ephemeral=True
        )

    @nextcord.ui.button(label="", emoji="<:Money:1447120406866694217>", custom_id="gfsfgesf")
    async def check_money_btn(self, button, interaction: nextcord.Interaction):

        # ⛔ ตรวจสอบสิทธิ์ก่อน
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: คุณไม่ใช่แอดมิน ไม่สามารถใช้งานได้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ✅ แสดง UserSelect view
        await interaction.response.send_message(
            "เลือกผู้ใช้เพื่อจะ **เช็คจำนวนเงิน**",
            view=CheckBalanceUserSelectView(),
            ephemeral=True
        )

    @nextcord.ui.button(label="", emoji="<a:highstages:1448616985188499497>", custom_id="ffrrff")
    async def view_history(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: คุณไม่ใช่แอดมิน ไม่สามารถใช้งานได้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.send_message(
            "เลือกผู้ใช้เพื่อดู **ประวัติการซื้อสินค้า**",
            view=UserSelectView("view"),
            ephemeral=True
        )

    @nextcord.ui.button(label="", emoji="<a:highstages:1448616985188499497>", custom_id="rff")
    async def delete_history(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: คุณไม่ใช่แอดมิน ไม่สามารถใช้งานได้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.send_message(
            "เลือกผู้ใช้ที่จะ **ลบประวัติการซื้อสินค้า**",
            view=UserSelectView("delete"),
            ephemeral=True
        )

class UserSelect(nextcord.ui.UserSelect):
    def __init__(self, mode):
        self.mode = mode
        super().__init__(placeholder="เลือกผู้ใช้…")

    async def callback(self, interaction: nextcord.Interaction):
        user = self.values[0]

        if self.mode in ["add", "remove"]:
            # เปิด modal ใส่จำนวนเงิน
            await interaction.response.send_modal(AdjustMoneyModal(self.mode, user))

        elif self.mode == "view":
            await send_purchase_history(interaction, user.id)

        elif self.mode == "delete":
            await delete_purchase_history(interaction, user)


class UserSelectView(nextcord.ui.View):
    def __init__(self, mode):
        super().__init__(timeout=None)
        self.add_item(UserSelect(mode))

class AdjustMoneyModal(nextcord.ui.Modal):
    def __init__(self, mode, user):
        self.mode = mode                  # add / remove
        self.target = user
        title = "เพิ่มเงินให้ผู้ใช้" if mode == "add" else "ลบเงินผู้ใช้"
        super().__init__(title=title)

        self.amount = nextcord.ui.TextInput(
            label="จำนวนเงิน",
            style=nextcord.TextInputStyle.short,
            required=True,
            placeholder="กรอกจำนวนเงิน เช่น 50"
        )
        self.add_item(self.amount)

    async def callback(self, interaction: nextcord.Interaction):

        amount = float(self.amount.value)
        user_id = str(self.target.id)
        users_file = "database/users.json"

        try:
            with open(users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}

        if user_id not in data:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลผู้ใช้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        point = float(data[user_id].get("point", 0))

        # --- ปรับยอดเงิน ---
        if self.mode == "add":
            new_point = point + amount
            action_text = f"เพิ่มยอดเงิน **+{amount:.1f} บาท**"
            color = nextcord.Color.green()
            log_title = "เพิ่มยอดเงินผู้ใช้"
        else:
            new_point = max(point - amount, 0)
            action_text = f"ลดยอดเงิน **-{amount:.1f} บาท**"
            color = nextcord.Color.red()
            log_title = "ลดยอดเงินผู้ใช้"

        # ❗ เก็บเป็นตัวเลขจริง ไม่ใช่ string !!!
        data[user_id]["point"] = new_point

        # บันทึกข้อมูล
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # --- DM แจ้งผู้ใช้ ---
        embed_dm = nextcord.Embed(
            title="💸 การปรับยอดเงินของคุณ",
            description=f"{action_text}\nจำนวนที่เหลือ: {new_point:.1f}\nดำเนินการโดย: {interaction.user.mention}",
            color=color
        )
        try:
            await self.target.send(embed=embed_dm)
        except:
            pass

        # --- Log ห้องแอดมิน ---
        log_channel = bot.get_channel(config.logtopup)
        if log_channel:
            embed_log = nextcord.Embed(
                title=log_title,
                description=(
                    f"ผู้ใช้: {self.target.mention}\n"
                    f"รายการ: {action_text}\n"
                    f"จำนวนที่เหลือ: {new_point:.1f}\n"
                    f"ดำเนินการโดย: {interaction.user.mention}"
                ),
                color=color
            )
            await log_channel.send(embed=embed_log)

        # --- ตอบกลับผู้กด ---
        embed = nextcord.Embed(
                description=f"<a:1505_yes:1447122291065356318>: {action_text} ให้ {self.target.mention} → `{new_point:.1f}` บาท",
                color=nextcord.Color.green()
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

async def send_purchase_history(interaction, user_id):
    user_id = str(user_id)
    users_file = "database/users.json"

    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)

    if user_id not in users:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลผู้ใช้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

    history = users[user_id].get("buymarket", [])

    if not history:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลผู้ใช้ใ",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = nextcord.Embed(
        title="ประวัติการซื้อสินค้า",
        color=0x5865F2
    )

    for i, item in enumerate(history, 1):
        m = item["market"]
        embed.add_field(
            name=f"🛒 รายการที่ {i}",
            value=(
                f"**สินค้า:** {m['market']}\n"
                f"**เวลา:** {m['time']}\n"
                f"**โค้ดสินค้า:** {m['code']}"
            ),
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

async def delete_purchase_history(interaction, user):
    user_id = str(user.id)
    users_file = "database/users.json"

    # โหลดไฟล์
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)

    # ตรวจว่ามีข้อมูลไหม
    if user_id not in users:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลผู้ใช้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

    # ตรวจว่ามีประวัติมั้ย
    if not users[user_id].get("buymarket"):
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลให้ลบ",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

    # ลบประวัติ
    users[user_id]["buymarket"] = []

    # บันทึกกลับลงไฟล์
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

    # DM แจ้งผู้ใช้
    embed_dm = nextcord.Embed(
        title="🗑️ ประวัติการซื้อถูกลบ",
        description=f"ประวัติการสั่งซื้อทั้งหมดของคุณถูกลบโดยแอดมิน: {interaction.user.mention}",
        color=nextcord.Color.red()
    )

    try:
        await user.send(embed=embed_dm)
    except:
        pass

    # Log
    log_channel = bot.get_channel(config.logtdele)
    if log_channel:
        embed_log = nextcord.Embed(
            title="📰 ลบประวัติการซื้อ",
            description=f"👤 ผู้ใช้: {user.mention}\n📄 ประวัติการซื้อ **ถูกลบทั้งหมด**\n🛠️ ดำเนินการโดย: {interaction.user.mention}",
            color=nextcord.Color.red()
        )
        await log_channel.send(embed=embed_log)

    # ตอบกลับผู้กดปุ่ม
        embed = nextcord.Embed(
                description=f"<a:1505_yes:1447122291065356318>: ลบข้อมูลการซื้อเรียบร้อย",
                color=nextcord.Color.green()
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class CheckBalanceUserSelectView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        self.add_item(CheckBalanceUserSelect())

class CheckBalanceUserSelect(nextcord.ui.UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="เลือกผู้ใช้…",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: nextcord.Interaction):
        user = self.values[0]
        user_id = str(user.id)

        users_file = "database/users.json"

        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)
        except:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลผู้ใช้ในไฟล์",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if user_id not in users:
            embed = nextcord.Embed(
                description="<a:No:1447122053185409034>: ไม่พบข้อมูลผู้ใช้",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        # ดึง point
        point = users[user_id].get("point", "0.0")

        embed = nextcord.Embed(
            title="💰 เช็คยอดเงินผู้ใช้",
            description=(
                f"👤 ผู้ใช้: {user.mention}\n\n"
                f"💴 **ยอดเงินปัจจุบัน:** `{point}` บาท"
            ),
            color=nextcord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(config.token)