"""Bale /pay command — subscription plan selection and payment flow."""

from __future__ import annotations

import json

import requests as _requests
from telebot import types

from app.db.session import get_db_session
from app.plans import PLAN_CONFIG, PLAN_PRICES
from app.services import payment_service, subscription_service
from integrations.bale.handlers.deps import BaleHandlerDeps, log_bale_incoming

_DURATION_LABEL = {1: "۱ ماهه", 3: "۳ ماهه"}


def _plan_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for (plan_key, months), price in PLAN_PRICES.items():
        plan_label = PLAN_CONFIG[plan_key]["label"]
        dur_label = _DURATION_LABEL.get(months, f"{months} ماهه")
        btn_label = f"{plan_label} — {dur_label}  |  {price:,} ریال"
        markup.add(types.InlineKeyboardButton(
            btn_label, callback_data=f"pay_plan:{plan_key}:{months}"
        ))
    return markup


def _send_invoice_direct(
    bot_token: str,
    api_url_template: str,
    chat_id: int,
    title: str,
    description: str,
    payload: str,
    provider_token: str,
    amount: int,
) -> None:
    """POST sendInvoice directly to Bale API — bypasses telebot's request sender."""
    url = api_url_template.format(bot_token, "sendInvoice")
    body = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": payload,
        "provider_token": provider_token,
        "currency": "IRR",
        "prices": json.dumps([{"label": title, "amount": amount}]),
    }
    resp = _requests.post(url, data=body, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"sendInvoice failed [{resp.status_code}]: {resp.text}")
    resp.raise_for_status()


def register_payment_handler(deps: BaleHandlerDeps) -> None:
    bot = deps.bot
    logger = deps.logger
    provider_token = deps.payment_provider_token
    api_url = deps.api_url

    # ------------------------------------------------------------------ /pay
    @bot.message_handler(commands=["pay"])
    def handle_pay(message: types.Message) -> None:
        uid = message.from_user.id if message.from_user else None
        log_bale_incoming(
            "command /pay",
            chat_id=message.chat.id,
            user_id=uid,
            text=getattr(message, "text", None),
        )
        if uid:
            deps.log_message(uid, "in", "command", "/pay", message.message_id)
        try:
            plan_text = "💳 *انتخاب پلن اشتراک*\n\nیک پلن را انتخاب کنید:"
            bot.send_message(
                message.chat.id,
                plan_text,
                parse_mode="Markdown",
                reply_markup=_plan_keyboard(),
            )
            if uid:
                deps.log_message(uid, "out", "text", plan_text)
        except Exception as e:
            logger.error(f"Error sending plan selection: {e}", exc_info=True)

    # -------------------------------------------------------- plan selection
    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("pay_plan:"))
    def handle_plan_selection(call: types.CallbackQuery) -> None:
        uid = call.from_user.id if call.from_user else None
        cid = call.message.chat.id if call.message else None
        log_bale_incoming(
            "callback pay_plan",
            chat_id=cid,
            user_id=uid,
            callback_data=call.data,
        )
        if uid and call.data:
            deps.log_message(uid, "in", "callback", call.data)
        try:
            if not call.data:
                bot.answer_callback_query(call.id)
                return
            # callback_data format: "pay_plan:basic:1"
            parts = call.data.split(":")
            if len(parts) != 3:
                bot.answer_callback_query(call.id, "پلن نامعتبر است!")
                return
            plan_key = parts[1]
            duration_months = int(parts[2])
            amount = PLAN_PRICES.get((plan_key, duration_months))
            if amount is None or plan_key not in PLAN_CONFIG:
                bot.answer_callback_query(call.id, "پلن نامعتبر است!")
                return

            bale_user_id = call.from_user.id if call.from_user else None
            if bale_user_id is None:
                bot.answer_callback_query(call.id, "خطا: کاربر شناسایی نشد.")
                return

            bot.answer_callback_query(call.id, "در حال ارسال فاکتور...")

            plan_label = PLAN_CONFIG[plan_key]["label"]
            dur_label = _DURATION_LABEL.get(duration_months, f"{duration_months} ماهه")
            invoice_payload = json.dumps({"plan": plan_key, "months": duration_months, "uid": bale_user_id})
            chat_id = call.message.chat.id if call.message else bale_user_id

            _send_invoice_direct(
                bot_token=bot.token,
                api_url_template=api_url,
                chat_id=chat_id,
                title=f"اشتراک {plan_label} — {dur_label}",
                description=f"دسترسی {dur_label} به دستیار هوشمند SGPT",
                payload=invoice_payload,
                provider_token=provider_token,
                amount=amount,
            )
        except Exception as e:
            logger.error(f"Error sending invoice: {e}", exc_info=True)
            try:
                bot.answer_callback_query(call.id, "خطا در ارسال فاکتور!")
            except Exception:
                pass

    # -------------------------------------------------- pre-checkout query
    @bot.pre_checkout_query_handler(func=lambda q: True)
    def handle_pre_checkout(query: types.PreCheckoutQuery) -> None:
        uid = query.from_user.id if query.from_user else None
        log_bale_incoming(
            "pre_checkout_query",
            query_id=query.id,
            user_id=uid,
            currency=query.currency,
            total_amount=query.total_amount,
        )
        try:
            bot.answer_pre_checkout_query(query.id, ok=True)
        except Exception as e:
            logger.error(f"Error answering pre_checkout_query: {e}", exc_info=True)
            try:
                bot.answer_pre_checkout_query(
                    query.id, ok=False, error_message="خطای داخلی. لطفاً دوباره تلاش کنید."
                )
            except Exception:
                pass

    # -------------------------------------------------- successful payment
    @bot.message_handler(content_types=["successful_payment"])
    def handle_successful_payment(message: types.Message) -> None:
        uid = message.from_user.id if message.from_user else None
        sp0 = message.successful_payment
        log_bale_incoming(
            "message successful_payment",
            chat_id=message.chat.id,
            user_id=uid,
            total_amount=getattr(sp0, "total_amount", None),
            currency=getattr(sp0, "currency", None),
        )
        if uid:
            deps.log_message(uid, "in", "payment", f"successful_payment: {getattr(sp0, 'total_amount', '')} {getattr(sp0, 'currency', '')}", message.message_id)
        try:
            sp = message.successful_payment
            if sp is None:
                return

            bale_user_id = message.from_user.id if message.from_user else 0

            try:
                payload = json.loads(sp.invoice_payload)
                plan_key = payload.get("plan", "basic")
                duration_months = int(payload.get("months", 1))
            except Exception:
                plan_key = "basic"
                duration_months = 1

            try:
                db = get_db_session()
                try:
                    payment_service.record_payment(
                        db,
                        bale_user_id=bale_user_id,
                        plan_key=plan_key,
                        amount=sp.total_amount,
                        currency=sp.currency,
                        invoice_payload=sp.invoice_payload,
                        provider_payment_charge_id=sp.provider_payment_charge_id,
                    )
                    subscription_service.activate_plan(db, bale_user_id, plan_key, duration_months, paid_irr=sp.total_amount)
                    logger.info(
                        f"Payment + plan activated | user={bale_user_id} plan={plan_key} "
                        f"months={duration_months} amount={sp.total_amount}"
                    )
                except Exception as db_err:
                    db.rollback()
                    logger.error(f"Failed to save payment/activate plan: {db_err}", exc_info=True)
                finally:
                    db.close()
            except Exception as session_err:
                logger.error(f"DB session error on payment: {session_err}", exc_info=True)

            plan_label = PLAN_CONFIG.get(plan_key, {}).get("label", plan_key)
            dur_label = _DURATION_LABEL.get(duration_months, f"{duration_months} ماهه")
            success_text = (
                f"✅ *پرداخت موفق!*\n\n"
                f"پلن *{plan_label}* — {dur_label} با موفقیت فعال شد! 🎉\n"
                f"مبلغ: {sp.total_amount:,} {sp.currency}\n"
                f"کد پیگیری: `{sp.provider_payment_charge_id}`"
            )
            bot.send_message(message.chat.id, success_text, parse_mode="Markdown")
            deps.log_message(bale_user_id, "out", "text", success_text)
        except Exception as e:
            logger.error(f"Error handling successful_payment: {e}", exc_info=True)
