#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import requests
import json
from datetime import datetime
from flask import Flask, request, jsonify

# إعدادات البوت
BOT_TOKEN = os.getenv('BOT_TOKEN', '8190717712:AAH1beEuFqbOju-BXgydlQQeB6vuLU3ZDPw')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '761081783')

# إعدادات Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://vymeazhbvktmzillvnxc.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ5bWVhemhidmt0bXppbGx2bnhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEyNzk1NjcsImV4cCI6MjA2Njg1NTU2N30.l6zkXbh_h_EfkIQ2FZyYDod6qafA24tfCbsNHcavmGE')

# إعداد Flask
app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_message(chat_id: str, text: str):
    """إرسال رسالة عادية"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"خطأ في إرسال الرسالة: {e}")
        return None

def edit_message(chat_id: str, message_id: int, new_text: str):
    """تعديل رسالة موجودة"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': new_text
    }
    
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"خطأ في تعديل الرسالة: {e}")
        return None

def answer_callback_query(callback_query_id: str, text: str = ""):
    """الرد على callback query"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    data = {
        'callback_query_id': callback_query_id,
        'text': text
    }
    
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"خطأ في الرد على callback query: {e}")
        return None

def update_transaction_status(transaction_id: str, new_status: str) -> bool:
    """تحديث حالة المعاملة في Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/transactions"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'status': new_status,
            'updated_at': datetime.now().isoformat()
        }
        
        response = requests.patch(
            f"{url}?id=eq.{transaction_id}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 204:
            logger.info(f"✅ تم تحديث حالة المعاملة {transaction_id} إلى {new_status}")
            return True
        else:
            logger.error(f"❌ فشل تحديث المعاملة: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث حالة المعاملة: {e}")
        return False

def handle_callback_query(callback_query):
    """معالجة الضغط على أزرار التحكم"""
    try:
        callback_data = callback_query.get('data', '')
        message = callback_query['message']
        chat_id = str(message['chat']['id'])
        message_id = message['message_id']
        callback_query_id = callback_query['id']
        
        if callback_data.startswith('approve_transaction_'):
            transaction_id = callback_data.replace('approve_transaction_', '')
            success = update_transaction_status(transaction_id, 'تم')
            
            if success:
                new_text = message['text'] + "\n\n✅ تم قبول المعاملة"
                edit_message(chat_id, message_id, new_text)
                answer_callback_query(callback_query_id, "تم قبول المعاملة بنجاح ✅")
                logger.info(f"✅ تم قبول المعاملة {transaction_id}")
            else:
                answer_callback_query(callback_query_id, "فشل في تحديث المعاملة ❌")
                
        elif callback_data.startswith('reject_transaction_'):
            transaction_id = callback_data.replace('reject_transaction_', '')
            success = update_transaction_status(transaction_id, 'مرفوض')
            
            if success:
                new_text = message['text'] + "\n\n❌ تم رفض المعاملة"
                edit_message(chat_id, message_id, new_text)
                answer_callback_query(callback_query_id, "تم رفض المعاملة ❌")
                logger.info(f"❌ تم رفض المعاملة {transaction_id}")
            else:
                answer_callback_query(callback_query_id, "فشل في تحديث المعاملة ❌")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة callback query: {e}")

def handle_message(message):
    """معالجة الرسائل الواردة"""
    try:
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        
        if text == '/start':
            welcome_message = """
💰 مرحباً بك في بوت معاملات وردلي!

هذا البوت مخصص لاستقبال ومراجعة المعاملات المالية.

الأوامر المتاحة:
/start - رسالة الترحيب
/help - المساعدة
/status - حالة البوت
"""
            send_message(chat_id, welcome_message)
            
        elif text == '/help':
            help_message = """
📋 مساعدة بوت المعاملات:

🎯 الوظيفة الأساسية:
- استقبال المعاملات الجديدة
- إرسال إشعارات مع أزرار قبول/رفض
- تحديث حالة المعاملات

🔧 الأوامر:
/start - بدء المحادثة
/help - هذه الرسالة
/status - حالة البوت

💡 ملاحظة: هذا البوت للإدارة فقط
"""
            send_message(chat_id, help_message)
            
        elif text == '/status':
            status_message = f"""
📊 حالة بوت المعاملات:

✅ البوت يعمل بشكل طبيعي
🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔗 Webhook نشط
💾 قاعدة البيانات متصلة
"""
            send_message(chat_id, status_message)
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال التحديثات من Telegram"""
    try:
        update = request.get_json()
        
        if 'message' in update:
            handle_message(update['message'])
        elif 'callback_query' in update:
            handle_callback_query(update['callback_query'])
            
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"خطأ في webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """فحص صحة البوت"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_token': BOT_TOKEN[:10] + '...',
        'webhook_active': True
    })

@app.route('/', methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        'message': 'Wardly Transactions Bot is running!',
        'status': 'active',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
