import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import telegram
from telegram.ext import Application, MessageHandler, filters
from .base_interface import BaseInterface
from .message import Message
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)

class TelegramBotInterface(BaseInterface):
    def __init__(self, bot_token: Optional[str] = None):
        super().__init__('telegram')
        self.bot_token = bot_token
        self.application = None
        self.bot = None
        self.message_queue = asyncio.Queue()
        self.formatter = MessageFormatter()
        
    async def start_bot(self):
        """Initialize and start the Telegram bot"""
        if not self.bot_token:
            raise ValueError("Bot token required")
            
        self.application = Application.builder().token(self.bot_token).build()
        self.bot = self.application.bot
        
        # Add message handler
        message_handler = MessageHandler(filters.TEXT, self._handle_telegram_message)
        self.application.add_handler(message_handler)
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
    
    async def _handle_telegram_message(self, update, context):
        """Handle incoming Telegram messages"""
        user_message = update.message.text
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Send to Claude API for processing
        await self.send_message(
            prefix='@claude',
            payload={
                'text': user_message,
                'user_id': user_id,
                'chat_id': chat_id
            },
            correlation_id=f"telegram_{chat_id}_{update.message.message_id}"
        )
    
    async def process_message(self, message: Message):
        """Process outgoing messages to Telegram users"""
        try:
            chat_id = message.payload.get('chat_id')
            
            # Use the unified formatter for all message types
            if message.payload.get('success') is not None:
                # This is a command result
                if message.payload.get('success'):
                    text = self.formatter.format_message(message.payload)
                else:
                    text = f"ERROR: {message.payload.get('error', 'Unknown error')}"
            else:
                # Regular text message - could be Claude JSON or plain text
                raw_text = message.payload.get('text', '')
                text = self.formatter.format_message(raw_text)
            
            if not chat_id:
                # Try to extract from correlation_id
                if message.correlation_id and 'telegram_' in message.correlation_id:
                    parts = message.correlation_id.split('_')
                    if len(parts) >= 2:
                        chat_id = int(parts[1])
            
            if chat_id and text:
                # Use Operator's chunking for long messages
                chunks = self._chunk_for_telegram(text)
                
                for chunk in chunks:
                    await self.bot.send_message(chat_id=chat_id, text=chunk)
            else:
                logging.warning(f"Cannot send Telegram message: missing chat_id or text")
                
        except Exception as e:
            logging.error(f"Telegram send error: {str(e)}")
    
    def _chunk_for_telegram(self, text: str, max_length: int = 4096) -> list[str]:
        """Split long messages for Telegram's character limit"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Try splitting by lines first
        lines = text.split('\n')
        for line in lines:
            # If a single line is too long, split it by characters
            if len(line) > max_length:
                # Finish current chunk first if it has content
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                    current_chunk = ""
                
                # Split the long line into character chunks
                for i in range(0, len(line), max_length):
                    chunks.append(line[i:i + max_length])
            else:
                # Check if adding this line would exceed the limit
                if len(current_chunk) + len(line) + 1 <= max_length:
                    current_chunk += line + '\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.rstrip())
                    current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.rstrip())
            
        return chunks
    
    async def start(self):
        """Start the Telegram bot interface with both bot and message processing"""
        logger.info("Telegram bot interface started")
        try:
            # Start the Telegram bot if token is available
            if self.bot_token:
                logger.info("Starting Telegram bot with polling...")
                bot_task = asyncio.create_task(self.start_bot())
            else:
                logger.warning("No bot token - Telegram bot polling disabled")
                bot_task = None
            
            # Start the message processing loop
            message_task = asyncio.create_task(self._process_messages())
            
            # Run both concurrently
            tasks = [message_task]
            if bot_task:
                tasks.append(bot_task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except asyncio.CancelledError:
            logger.info("Telegram bot interface stopping...")
            if self.application:
                await self.stop_bot()
            raise
        except Exception as e:
            logger.error(f"Error in Telegram bot interface: {e}")
            raise
    
    async def _process_messages(self):
        """Process messages from inbox"""
        while True:
            try:
                # Check for messages in inbox
                if hasattr(self, 'inbox') and not self.inbox.empty():
                    message = await self.inbox.get()
                    await self.process_message(message)
                    self.inbox.task_done()
                else:
                    await asyncio.sleep(0.1)  # Brief sleep when no messages
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(0.1)
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()