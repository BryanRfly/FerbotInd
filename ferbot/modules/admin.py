# Ferbot, this is a bot for management your group
# This source code copy from UserIndoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
# Copyright (C) 2021 FS Project <https://github.com/FS-Project/FerbotInd.git>
# 
# UserindoBot
# Copyright (C) 2020  UserindoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""This special for you lazy admeme"""

import html
import os

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from ferbot import dispatcher
from ferbot.modules.connection import connected
from ferbot.modules.disable import DisableAbleCommandHandler
from ferbot.modules.helper_funcs.admin_rights import (
    user_can_changeinfo,
    user_can_pin,
    user_can_promote,
)
from ferbot.modules.helper_funcs.alternate import typing_action
from ferbot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    user_admin,
    ADMIN_CACHE,
)
from ferbot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from ferbot.modules.log_channel import loggable


@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def promote(update, context):
    chat_id = update.effective_chat.id
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak yang cukup untuk mempromosikan seseorang!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("sebutkan satu.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if (
        user_member.status == "administrator"
        or user_member.status == "creator"
    ):
        message.reply_text("Dia sudah menjadi admin...!")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya berharap, saya diangkat menjadi admin!")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(context.bot.id)

    context.bot.promoteChatMember(
        chat_id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
    )

    message.reply_text("Promoted❤️")
    return (
        "<b>{}:</b>"
        "\n#PROMOTED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(user_member.user.id, user_member.user.first_name),
        )
    )


@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def demote(update, context):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki hak untuk menurunkan hak orang lain!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Sebutkan satu.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == "creator":
        message.reply_text("I'm not gonna demote Creator this group.... 🙄")
        return ""

    if not user_member.status == "administrator":
        message.reply_text(
            "Bagaimana saya bisa menurunkan hak seseorang yang bahkan bukan admin!"
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yeahhh... Tidak akan menurunkan diriku!")
        return ""

    try:
        context.bot.promoteChatMember(
            int(chat.id),
            int(user_id),
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
        )
        message.reply_text("Berhasil diturunkan hak nya!")
        return (
            "<b>{}:</b>"
            "\n#DEMOTED"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {}".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(user_member.user.id, user_member.user.first_name),
            )
        )

    except BadRequest:
        message.reply_text(
            "Gagal menurunkan. Saya mungkin bukan admin, atau status admin ditunjuk oleh "
            "pengguna, jadi saya tidak bisa bertindak atas mereka!"
        )
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def pin(update, context):
    args = context.args
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Anda kekurangan hak untuk menyematkan pesan!")
        return ""

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            context.bot.pinChatMessage(
                chat.id,
                prev_message.message_id,
                disable_notification=is_silent,
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return (
            "<b>{}:</b>"
            "\n#PINNED"
            "\n<b>Admin:</b> {}".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def unpin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Anda kehilangan hak untuk melepas pin pada pesan!")
        return ""

    try:
        context.bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        elif excp.message == "Message to unpin not found":
            message.reply_text(
                "Saya tidak dapat melihat pesan yang disematkan, Mungkin sudah tidak terhubung, atau hal lainya!"
            )
        else:
            raise

    return (
        "<b>{}:</b>"
        "\n#UNPINNED"
        "\n<b>Admin:</b> {}".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@bot_admin
@user_admin
@typing_action
def invite(update, context):
    user = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat
    context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
    else:
        if msg.chat.type == "private":
            msg.reply_text("Perintah ini dimaksudkan untuk digunakan dalam obrolan bukan di PM")
            return ""
        chat = update.effective_chat

    if chat.username:
        msg.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            invitelink = context.bot.exportChatInviteLink(chat.id)
            msg.reply_text(invitelink)
        else:
            msg.reply_text(
                "Saya tidak memiliki akses ke tautan undangan, coba ubah izin saya!"
            )
    else:
        msg.reply_text(
            "Saya hanya dapat memberi Anda tautan undangan untuk supergrup dan channel, maaf!"
        )


@typing_action
def adminlist(update, context):
    administrators = update.effective_chat.get_administrators()
    text = "Admins di <b>{}</b>:".format(
        update.effective_chat.title or "grup ini"
    )
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "creator":
            text += "\n 🦁 Pembuat:"
            text += "\n • {} \n\n 🦊 Admin:".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "administrator":
            text += "\n • {}".format(name)
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@bot_admin
@can_promote
@user_admin
@typing_action
def set_title(update, context):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except Exception:
        return

    if not user_id:
        message.reply_text("Anda sepertinya tidak mengarah pada pengguna.")
        return

    if user_member.status == "creator":
        message.reply_text(
            "Orang ini yang membuat obrolan, bagaimana saya bisa mengatur judul khusus untuknya?"
        )
        return

    if not user_member.status == "administrator":
        message.reply_text(
            "Tidak dapat menyetel judul untuk non-admin!\nPromosikan mereka terlebih dahulu untuk menyetel judul khusus!"
        )
        return

    if user_id == context.bot.id:
        message.reply_text(
            "Saya tidak dapat menetapkan judul saya sendiri! Dapatkan orang yang menjadikan saya admin untuk melakukannya untuk saya."
        )
        return

    if not title:
        message.reply_text("Menyetel judul kosong tidak akan menghasilkan apa-apa!")
        return

    if len(title) > 16:
        message.reply_text(
            "Panjang judul lebih dari 16 karakter.\nPotong menjadi 16 karakter."
        )

    try:
        context.bot.set_chat_administrator_custom_title(
            chat.id, user_id, title
        )
        message.reply_text(
            "Berhasil menetapkan judul untuk <b>{}</b> ke <code>{}</code>!".format(
                user_member.user.first_name or user_id, title[:16]
            ),
            parse_mode=ParseMode.HTML,
        )

    except BadRequest:
        message.reply_text(
            "Saya tidak dapat menyetel judul khusus untuk nya jika dia bukan saya yang promosikan!"
        )


@bot_admin
@user_admin
@typing_action
def setchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda kekurangan hak untuk mengubah info grup!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Anda hanya dapat mengatur beberapa foto sebagai foto obrolan!")
            return
        dlmsg = msg.reply_text("Tunggu sebentar...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Berhasil menyetel gambar obrolan baru!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Balas beberapa foto atau file untuk mengatur gambar obrolan baru!")


@bot_admin
@user_admin
@typing_action
def rmchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki cukup hak untuk menghapus foto grup")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("Foto profil obrolan berhasil dihapus!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def setchat_title(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki cukup hak untuk mengubah info obrolan!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Masukkan beberapa teks untuk menyetel judul baru dalam obrolan Anda!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Berhasil menyetel <b>{title}</b> sebagai judul obrolan baru!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def set_sticker(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda kekurangan hak untuk mengubah info obrolan!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "Anda perlu membalas beberapa stiker untuk menyetel kumpulan stiker obrolan!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(
                f"Berhasil memasang stiker grup baru di{chat.title}!"
            )
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Maaf, karena pembatasan telegram, grup harus memiliki minimal 100 anggota sebelum mereka dapat memiliki stiker grup!"
                )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text(
            "Anda perlu membalas beberapa stiker untuk menyetel kumpulan stiker obrolan!"
        )


@bot_admin
@user_admin
@typing_action
def set_desc(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda kekurangan hak untuk mengubah info obrolan!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Menyetel deskripsi kosong tidak akan melakukan apa pun!")
    try:
        if len(desc) > 255:
            return msg.reply_text(
                "Deskripsi harus kurang dari 255 karakter!"
            )
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(
            f"Deskripsi obrolan berhasil diperbarui ke {chat.title}!"
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")


@user_admin
@typing_action
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Cache admin disegarkan!")


def __chat_settings__(chat_id, user_id):
    return "Kamu adalah *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status
        in ("administrator", "creator")
    )


__help__ = """
Malas mempromosikan atau menurunkan seseorang sebagai admin? Ingin melihat informasi dasar tentang obrolan? \
Semua hal tentang ruang obrolan seperti daftar admin, menyematkan atau mengambil tautan undangan dapat \
dilakukan dengan mudah menggunakan bot.

 × /adminlist: daftar admin dalam obrolan

*Hanya Admin:*
 × /pin: Pin secara diam-diam pada pesan yang dibalas - tambahkan `loud`, `notify` atau `violent` untuk memberi pemberitahuan kepada pengguna.
 × /unpin: Melepas pesan yang disematkan saat ini.
 × /invitelink: Mendapat invitelink obrolan pribadi.
 × /promote: Mempromosikan balasan pengguna.
 × /demote: Mendemosikan balasan pengguna.
 × /settitle: Menetapkan judul khusus untuk admin yang dipromosikan oleh bot.
 × /setgpic: Sebagai balasan ke file atau foto untuk mengatur foto profil grup!
 × /delgpic: Sama seperti di atas tetapi untuk menghapus foto profil grup.
 × /setgtitle <judulbaru>: Mengatur judul obrolan baru di grup Anda.
 × /setsticker: Sebagai balasan untuk beberapa stiker untuk mengaturnya sebagai set stiker grup!
 × /setdescription: <deskripsi> Mengatur deskripsi obrolan baru dalam grup.

*Catatan*: Untuk mengatur stiker grup, grup harus memiliki minimal 100 anggota.

Contoh mempromosikan seseorang menjadi admin:
`/promote @username`; ini akan mempromosikan pengguna menjadi admin.
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler(
    "pin", pin, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
UNPIN_HANDLER = CommandHandler(
    "unpin", unpin, filters=Filters.chat_type.groups, run_async=True
)
INVITE_HANDLER = CommandHandler("invitelink", invite, run_async=True)
CHAT_PIC_HANDLER = CommandHandler(
    "setgpic", setchatpic, filters=Filters.chat_type.groups, run_async=True
)
DEL_CHAT_PIC_HANDLER = CommandHandler(
    "delgpic", rmchatpic, filters=Filters.chat_type.groups, run_async=True
)
SETCHAT_TITLE_HANDLER = CommandHandler(
    "setgtitle", setchat_title, filters=Filters.chat_type.groups, run_async=True
)
SETSTICKET_HANDLER = CommandHandler(
    "setsticker", set_sticker, filters=Filters.chat_type.groups, run_async=True
)
SETDESC_HANDLER = CommandHandler(
    "setdescription", set_desc, filters=Filters.chat_type.groups, run_async=True
)

PROMOTE_HANDLER = CommandHandler(
    "promote", promote, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
DEMOTE_HANDLER = CommandHandler(
    "demote", demote, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)

SET_TITLE_HANDLER = DisableAbleCommandHandler(
    "settitle", set_title, pass_args=True, run_async=True
)
ADMINLIST_HANDLER = DisableAbleCommandHandler(
    "adminlist", adminlist, filters=Filters.chat_type.groups, run_async=True
)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, run_async=True
)


dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(SETSTICKET_HANDLER)
dispatcher.add_handler(SETDESC_HANDLER)
