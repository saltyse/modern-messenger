import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from PIL import Image, ImageTk, ImageOps, ImageDraw
import json
import hashlib
import os
import base64
import io
from datetime import datetime
import threading
import socket
import cv2
import numpy as np
from tkinter import Frame, Label, Button
import subprocess
import platform
import shutil
import time
import pyaudio
import wave
import tempfile

# Импортируем клиент
from client import ChatClient

class ModernChatBubble:
    """Современный стиль сообщения с поддержкой медиа"""
    def __init__(self, parent, message, is_own=False, is_admin=False, avatar_image=None, on_delete=None):
        self.parent = parent
        self.message = message
        self.is_own = is_own
        self.is_admin = is_admin
        self.avatar_image = avatar_image
        self.on_delete = on_delete
        
    def create_widget(self):
        # Основной контейнер сообщения
        main_frame = tk.Frame(self.parent, bg='#FFFFFF')
        main_frame.pack(fill='x', padx=20, pady=2)
        
        # Контейнер для аватарки и сообщения
        content_frame = tk.Frame(main_frame, bg='#FFFFFF')
        if self.is_own:
            content_frame.pack(side=tk.RIGHT, anchor='e')
        else:
            content_frame.pack(side=tk.LEFT, anchor='w')
        
        # Аватарка (только для чужих сообщений)
        if not self.is_own:
            avatar_container = tk.Frame(content_frame, bg='#FFFFFF')
            avatar_container.pack(side=tk.LEFT)
            
            if self.avatar_image:
                avatar_label = tk.Label(
                    avatar_container,
                    image=self.avatar_image,
                    bg='#FFFFFF'
                )
                avatar_label.pack()
            else:
                # Аватарка с инициалами
                avatar_bg = '#6366F1' if not self.is_admin else '#8B5CF6'
                avatar_canvas = tk.Canvas(avatar_container, width=32, height=32, bg=avatar_bg, highlightthickness=0)
                avatar_canvas.pack()
                initials = self.message['user'][:2].upper() if len(self.message['user']) >= 2 else self.message['user'][0].upper()
                avatar_canvas.create_text(16, 16, text=initials, fill='white', font=('Segoe UI', 10, 'bold'))
        
        # Контейнер для текста сообщения
        text_container = tk.Frame(content_frame, bg='#FFFFFF')
        text_container.pack(side=tk.LEFT if self.is_own else tk.RIGHT)
        
        # Имя пользователя (только для чужих сообщений)
        if not self.is_own:
            name_frame = tk.Frame(text_container, bg='#FFFFFF')
            name_frame.pack(anchor='w')
            
            name_label = tk.Label(
                name_frame,
                text=self.message['user'],
                font=('Segoe UI', 11, 'bold'),
                fg='#1F2937',
                bg='#FFFFFF'
            )
            name_label.pack(side=tk.LEFT)
            
            if self.is_admin:
                admin_label = tk.Label(
                    name_frame,
                    text=" 👑",
                    font=('Segoe UI', 10),
                    fg='#F59E0B',
                    bg='#FFFFFF'
                )
                admin_label.pack(side=tk.LEFT)
        
        # Основной пузырь сообщения
        bubble_frame = tk.Frame(text_container, bg='#FFFFFF')
        bubble_frame.pack(fill='x', pady=(2, 0))
        
        # Цвет пузыря
        if self.is_own:
            bubble_color = '#6366F1'  # Синий для своих сообщений
            text_color = '#FFFFFF'
        else:
            bubble_color = '#F3F4F6'  # Светло-серый для чужих
            text_color = '#1F2937'
        
        # Текст сообщения
        if self.message.get('message'):
            message_label = tk.Label(
                bubble_frame,
                text=self.message['message'],
                font=('Segoe UI', 14),
                fg=text_color,
                bg=bubble_color,
                justify='left',
                wraplength=400,
                padx=16,
                pady=12
            )
            message_label.pack(anchor='e' if self.is_own else 'w')
        
        # Голосовое сообщение
        if self.message.get('voice'):
            voice_frame = tk.Frame(bubble_frame, bg=bubble_color)
            voice_frame.pack(anchor='e' if self.is_own else 'w', padx=16, pady=8)
            
            voice_btn = tk.Button(
                voice_frame,
                text="🎤 Голосовое сообщение",
                command=lambda: self.play_voice(self.message['voice']),
                font=('Segoe UI', 12),
                fg=text_color,
                bg=bubble_color,
                relief='flat',
                bd=0,
                cursor='hand2',
                padx=12,
                pady=8
            )
            voice_btn.pack()
            voice_btn.bind('<Enter>', lambda e: voice_btn.config(bg='#E5E7EB' if not self.is_own else '#5B58E5'))
            voice_btn.bind('<Leave>', lambda e: voice_btn.config(bg=bubble_color))
        
        # Изображение
        if self.message.get('image'):
            self.create_media_preview(bubble_frame, self.message['image'], 'image', bubble_color)
        
        # Видео
        if self.message.get('video'):
            self.create_media_preview(bubble_frame, self.message['video'], 'video', bubble_color)
        
        # Время отправки и кнопка удаления
        time_frame = tk.Frame(text_container, bg='#FFFFFF')
        time_frame.pack(fill='x', pady=(4, 0))
        
        try:
            timestamp = datetime.fromisoformat(self.message['timestamp'])
            time_text = timestamp.strftime("%H:%M")
        except:
            time_text = "??:??"
        
        time_label = tk.Label(
            time_frame,
            text=time_text,
            font=('Segoe UI', 10),
            fg='#6B7280',
            bg='#FFFFFF'
        )
        
        if self.is_own:
            time_label.pack(side=tk.RIGHT)
            # Кнопка удаления для своих сообщений
            if self.on_delete:
                delete_btn = tk.Label(
                    time_frame,
                    text="🗑️",
                    font=('Arial', 10),
                    fg='#EF4444',
                    bg='#FFFFFF',
                    cursor='hand2'
                )
                delete_btn.pack(side=tk.RIGHT, padx=(5, 0))
                delete_btn.bind('<Button-1>', lambda e: self.on_delete())
                delete_btn.bind('<Enter>', lambda e: delete_btn.config(fg='#DC2626'))
                delete_btn.bind('<Leave>', lambda e: delete_btn.config(fg='#EF4444'))
        else:
            time_label.pack(side=tk.LEFT)
        
        return main_frame
    
    def create_media_preview(self, parent, filename, media_type, bg_color):
        """Создает превью медиа файла"""
        try:
            media_frame = tk.Frame(parent, bg=bg_color)
            media_frame.pack(anchor='w', padx=16, pady=(0, 8))
            
            if media_type == 'image':
                # Для изображений из сети можем использовать временные файлы
                image_path = filename
                if not os.path.exists(image_path):
                    return
                    
                image = Image.open(image_path)
                image.thumbnail((200, 200), Image.LANCZOS)
                
                # Добавляем скругленные углы
                mask = Image.new('L', image.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([(0, 0), image.size], radius=12, fill=255)
                
                result = Image.new('RGBA', image.size, (0, 0, 0, 0))
                result.paste(image, mask=mask)
                photo = ImageTk.PhotoImage(result)
                
                img_label = tk.Label(media_frame, image=photo, bg=bg_color, cursor='hand2')
                img_label.image = photo
                img_label.pack()
                img_label.bind("<Button-1>", lambda e, path=image_path: self.show_image(path))
            
            elif media_type == 'video':
                video_path = filename
                if not os.path.exists(video_path):
                    return
                    
                # Создаем превью видео
                cap = cv2.VideoCapture(video_path)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.resize(frame, (200, 150))
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Добавляем overlay с иконкой play
                    pil_img = Image.fromarray(frame_rgb)
                    draw = ImageDraw.Draw(pil_img)
                    
                    # Полупрозрачный черный overlay
                    overlay = Image.new('RGBA', pil_img.size, (0, 0, 0, 128))
                    pil_img = Image.alpha_composite(pil_img.convert('RGBA'), overlay)
                    
                    # Иконка play
                    play_size = 40
                    play_x = (200 - play_size) // 2
                    play_y = (150 - play_size) // 2
                    draw.ellipse([play_x, play_y, play_x + play_size, play_y + play_size], 
                               fill='#FFFFFF', outline='#FFFFFF')
                    
                    photo = ImageTk.PhotoImage(pil_img)
                    
                    video_label = tk.Label(media_frame, image=photo, bg=bg_color, cursor='hand2')
                    video_label.image = photo
                    video_label.pack()
                    video_label.bind("<Button-1>", lambda e, path=video_path: self.show_video(path))
                
                cap.release()
                    
        except Exception as e:
            print(f"Ошибка создания превью {media_type}: {e}")
    
    def show_image(self, image_path):
        """Показывает изображение в полном размере"""
        try:
            image_window = tk.Toplevel(self.parent)
            image_window.title("Просмотр изображения")
            image_window.geometry("800x600")
            image_window.configure(bg='#FFFFFF')
            
            image = Image.open(image_path)
            image.thumbnail((750, 550), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            img_label = tk.Label(image_window, image=photo, bg='#FFFFFF')
            img_label.image = photo
            img_label.pack(padx=20, pady=20)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение: {str(e)}")
    
    def show_video(self, video_path):
        """Показывает видео"""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(video_path)
            elif system == "Darwin":
                subprocess.run(["open", video_path])
            else:
                subprocess.run(["xdg-open", video_path])
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть видео: {str(e)}")
    
    def play_voice(self, voice_filename):
        """Воспроизводит голосовое сообщение"""
        try:
            voice_path = voice_filename
            if os.path.exists(voice_path):
                system = platform.system()
                if system == "Windows":
                    os.startfile(voice_path)
                elif system == "Darwin":
                    subprocess.run(["afplay", voice_path])
                else:
                    subprocess.run(["aplay", voice_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось воспроизвести голосовое сообщение: {str(e)}")

class ModernSidePanel:
    """Боковая панель в современном стиле с полным функционалом"""
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.is_visible = False
        
        # Создаем основную рамку
        self.side_frame = tk.Frame(parent, bg='#FFFFFF', width=350)
        self.side_frame.pack_propagate(False)
        
        # Заголовок панели
        self.header_frame = tk.Frame(self.side_frame, bg='#FFFFFF')
        self.header_frame.pack(fill=tk.X, pady=(20, 10), padx=20)
        
        self.title_label = tk.Label(
            self.header_frame,
            text="Управление",
            font=('Segoe UI', 18, 'bold'),
            fg='#1F2937',
            bg='#FFFFFF'
        )
        self.title_label.pack(side=tk.LEFT)
        
        # Кнопка закрытия
        self.close_btn = tk.Label(
            self.header_frame,
            text="✕",
            font=('Arial', 16, 'bold'),
            fg='#6B7280',
            bg='#FFFFFF',
            cursor='hand2'
        )
        self.close_btn.pack(side=tk.RIGHT)
        self.close_btn.bind('<Button-1>', lambda e: self.hide())
        self.close_btn.bind('<Enter>', lambda e: self.close_btn.config(fg='#374151'))
        self.close_btn.bind('<Leave>', lambda e: self.close_btn.config(fg='#6B7280'))
        
        # Разделитель
        separator = tk.Frame(self.side_frame, bg='#E5E7EB', height=1)
        separator.pack(fill=tk.X, padx=20, pady=10)
        
        # Контентная область
        self.content_frame = tk.Frame(self.side_frame, bg='#FFFFFF')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        self.hide()
    
    def show_admin_panel(self):
        """Показывает админ-панель в современном стиле"""
        if not self.is_visible:
            self.show()
        
        self.clear_content_safe()
        self.title_label.config(text="Админ-панель")
        
        # Прокручиваемая область
        canvas = tk.Canvas(self.content_frame, bg='#FFFFFF', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#FFFFFF')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Статус сервера
        status_frame = tk.Frame(scrollable_frame, bg='#FFFFFF')
        status_frame.pack(fill='x', pady=12)
        
        status_text = "🟢 Сервер подключен" if self.main_app.client.connected else "🔴 Сервер отключен"
        tk.Label(
            status_frame,
            text=status_text,
            font=('Segoe UI', 12, 'bold'),
            fg='#059669' if self.main_app.client.connected else '#EF4444',
            bg='#FFFFFF'
        ).pack(anchor='w')
        
        # IP информация
        if self.main_app.client.connected:
            tk.Label(
                status_frame,
                text=f"IP: {self.main_app.client.host}:{self.main_app.client.port}",
                font=('Segoe UI', 10),
                fg='#6B7280',
                bg='#FFFFFF'
            ).pack(anchor='w', pady=(5, 0))
        
        # Секции админ-панели
        sections = [
            {
                "title": "📊 Статистика системы",
                "content": self.create_stats_section
            },
            {
                "title": "👥 Онлайн пользователи", 
                "content": self.create_online_users_section
            },
            {
                "title": "🔒 Приватные чаты",
                "content": self.create_private_chats_section
            },
            {
                "title": "💬 Управление сообщениями",
                "content": self.create_messages_section
            },
            {
                "title": "📡 Управление каналами",
                "content": self.create_channels_admin_section
            }
        ]
        
        for section in sections:
            section_frame = self.create_section_frame(scrollable_frame, section["title"])
            section["content"](section_frame)
    
    def create_stats_section(self, parent):
        """Создает секцию статистики"""
        stats_frame = tk.Frame(parent, bg='#FFFFFF')
        stats_frame.pack(fill='x', pady=10)
        
        # Здесь можно добавить реальную статистику с сервера
        stats = [
            ("👥 Всего пользователей", "Загрузка..."),
            ("💬 Сообщений сегодня", "Загрузка..."),
            ("📡 Активных каналов", "Загрузка..."),
            ("🟢 Онлайн сейчас", "Загрузка...")
        ]
        
        for text, value in stats:
            stat_frame = tk.Frame(stats_frame, bg='#FFFFFF')
            stat_frame.pack(fill='x', pady=2)
            
            tk.Label(
                stat_frame,
                text=text,
                font=('Segoe UI', 11),
                fg='#6B7280',
                bg='#FFFFFF',
                anchor='w'
            ).pack(side=tk.LEFT)
            
            tk.Label(
                stat_frame,
                text=str(value),
                font=('Segoe UI', 11, 'bold'),
                fg='#1F2937',
                bg='#FFFFFF',
                anchor='e'
            ).pack(side=tk.RIGHT)
    
    def create_online_users_section(self, parent):
        """Создает секцию онлайн пользователей"""
        # Запрашиваем список пользователей
        self.main_app.client.get_users()
        
        users_frame = tk.Frame(parent, bg='#FFFFFF')
        users_frame.pack(fill='x', pady=10)
        
        # Заголовок с кнопкой обновления
        header_frame = tk.Frame(users_frame, bg='#FFFFFF')
        header_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="Онлайн пользователи",
            font=('Segoe UI', 12, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(side=tk.LEFT)
        
        refresh_btn = tk.Button(
            header_frame,
            text="🔄",
            command=lambda: self.main_app.client.get_users(),
            font=('Segoe UI', 10),
            fg='#6366F1',
            bg='#FFFFFF',
            relief='flat',
            bd=0,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Список пользователей будет обновляться через колбэк
    
    def update_online_users(self, users_data):
        """Обновляет список онлайн пользователей"""
        # Этот метод будет вызываться из основного приложения
        pass
    
    def create_private_chats_section(self, parent):
        """Создает секцию приватных чатов"""
        view_btn = tk.Button(
            parent,
            text="👁️ Просмотреть все приватные чаты",
            command=self.show_private_messages_admin,
            font=('Segoe UI', 11),
            fg='#6366F1',
            bg='#FFFFFF',
            relief='flat',
            bd=0,
            pady=10,
            cursor='hand2'
        )
        view_btn.pack(fill='x', pady=(8, 0))
        view_btn.bind('<Enter>', lambda e: view_btn.config(bg='#F3F4F6'))
        view_btn.bind('<Leave>', lambda e: view_btn.config(bg='#FFFFFF'))
    
    def create_messages_section(self, parent):
        """Создает секцию управления сообщениями"""
        view_btn = tk.Button(
            parent,
            text="📋 Просмотреть все сообщения",
            command=self.show_all_messages,
            font=('Segoe UI', 11),
            fg='#6366F1',
            bg='#FFFFFF',
            relief='flat',
            bd=0,
            pady=10,
            cursor='hand2'
        )
        view_btn.pack(fill='x', pady=(8, 0))
        view_btn.bind('<Enter>', lambda e: view_btn.config(bg='#F3F4F6'))
        view_btn.bind('<Leave>', lambda e: view_btn.config(bg='#FFFFFF'))
        
        clear_btn = tk.Button(
            parent,
            text="🧹 Очистить все сообщения",
            command=self.clear_all_messages,
            font=('Segoe UI', 11),
            fg='#EF4444',
            bg='#FFFFFF',
            relief='flat',
            bd=0,
            pady=10,
            cursor='hand2'
        )
        clear_btn.pack(fill='x', pady=(5, 0))
        clear_btn.bind('<Enter>', lambda e: clear_btn.config(bg='#FEF2F2'))
        clear_btn.bind('<Leave>', lambda e: clear_btn.config(bg='#FFFFFF'))
    
    def create_channels_admin_section(self, parent):
        """Создает секцию управления каналами для админа"""
        manage_btn = tk.Button(
            parent,
            text="🔧 Управление каналами",
            command=self.show_channels_management,
            font=('Segoe UI', 11),
            fg='#6366F1',
            bg='#FFFFFF',
            relief='flat',
            bd=0,
            pady=10,
            cursor='hand2'
        )
        manage_btn.pack(fill='x', pady=(8, 0))
        manage_btn.bind('<Enter>', lambda e: manage_btn.config(bg='#F3F4F6'))
        manage_btn.bind('<Leave>', lambda e: manage_btn.config(bg='#FFFFFF'))
    
    def create_section_frame(self, parent, title):
        """Создает рамку для секции"""
        section_frame = tk.Frame(parent, bg='#FFFFFF')
        section_frame.pack(fill='x', pady=12)
        
        tk.Label(
            section_frame,
            text=title,
            font=('Segoe UI', 14, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(fill='x', pady=(0, 8))
        
        return section_frame
    
    def show_private_messages_admin(self):
        """Показывает приватные сообщения для админа"""
        # Реализация просмотра приватных чатов
        pass
    
    def show_all_messages(self):
        """Показывает все сообщения"""
        # Реализация просмотра всех сообщений
        pass
    
    def show_channels_management(self):
        """Управление каналами для админа"""
        self.clear_content_safe()
        self.title_label.config(text="Управление каналами")
        
        # Запрашиваем список каналов
        self.main_app.client.get_channels()
        
        # Здесь будет отображение каналов
        
    def clear_all_messages(self):
        """Очищает все сообщения"""
        if messagebox.askyesno("Подтверждение", "Очистить все сообщения?"):
            # Реализация очистки сообщений через сервер
            pass
    
    def show_user_list(self):
        """Показывает список пользователей для приватного чата"""
        if not self.is_visible:
            self.show()
            
        self.clear_content_safe()
        self.title_label.config(text="Выберите пользователя")
        
        # Запрашиваем список пользователей
        self.main_app.client.get_users()
        
        # Список пользователей будет обновлен через колбэк
    
    def show_channels_list(self):
        """Показывает список каналов"""
        if not self.is_visible:
            self.show()
            
        self.clear_content_safe()
        self.title_label.config(text="Каналы")
        
        # Запрашиваем список каналов
        self.main_app.client.get_channels()
        
        # Список каналов будет обновлен через колбэк
    
    def update_channels_list(self, channels_data):
        """Обновляет список каналов"""
        # Этот метод будет вызываться из основного приложения
        pass
    
    def show_create_channel(self):
        """Показывает форму создания канала"""
        self.clear_content_safe()
        self.title_label.config(text="Создание канала")
        
        # Форма создания канала
        form_frame = tk.Frame(self.content_frame, bg='#FFFFFF')
        form_frame.pack(fill='x', pady=10)
        
        # Название канала
        tk.Label(
            form_frame,
            text="Название канала:",
            font=('Segoe UI', 11, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        name_entry = tk.Entry(
            form_frame,
            font=('Segoe UI', 12),
            relief='flat',
            bd=1,
            bg='#F9FAFB'
        )
        name_entry.pack(fill='x', pady=(0, 15))
        
        # Описание
        tk.Label(
            form_frame,
            text="Описание:",
            font=('Segoe UI', 11, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        desc_entry = tk.Entry(
            form_frame,
            font=('Segoe UI', 12),
            relief='flat',
            bd=1,
            bg='#F9FAFB'
        )
        desc_entry.pack(fill='x', pady=(0, 15))
        
        # Настройки канала
        settings_frame = tk.Frame(form_frame, bg='#FFFFFF')
        settings_frame.pack(fill='x', pady=10)
        
        # Тип канала
        type_var = tk.StringVar(value="public")
        
        tk.Label(
            settings_frame,
            text="Тип канала:",
            font=('Segoe UI', 11, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(fill='x', pady=(0, 8))
        
        type_frame = tk.Frame(settings_frame, bg='#FFFFFF')
        type_frame.pack(fill='x', pady=5)
        
        tk.Radiobutton(
            type_frame,
            text="🌐 Публичный канал",
            variable=type_var,
            value="public",
            bg='#FFFFFF',
            fg='#374151',
            selectcolor='#6366F1',
            font=('Segoe UI', 11)
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Radiobutton(
            type_frame,
            text="🔒 Приватный канал",
            variable=type_var,
            value="private",
            bg='#FFFFFF',
            fg='#374151',
            selectcolor='#6366F1',
            font=('Segoe UI', 11)
        ).pack(side=tk.LEFT)
        
        # Права подписчиков
        write_var = tk.BooleanVar(value=True)
        
        write_frame = tk.Frame(settings_frame, bg='#FFFFFF')
        write_frame.pack(fill='x', pady=10)
        
        write_check = tk.Checkbutton(
            write_frame,
            text="Разрешить подписчикам писать в канал",
            variable=write_var,
            bg='#FFFFFF',
            fg='#374151',
            selectcolor='#6366F1',
            font=('Segoe UI', 11)
        )
        write_check.pack(anchor='w')
        
        def create_channel():
            name = name_entry.get().strip()
            description = desc_entry.get().strip()
            is_public = type_var.get() == "public"
            subscribers_can_write = write_var.get()
            
            if not name:
                messagebox.showwarning("Внимание", "Введите название канала")
                return
            
            self.main_app.client.create_channel(name, description, is_public, subscribers_can_write)
            messagebox.showinfo("Успех", f"Канал '{name}' создан!")
            self.show_channels_list()
        
        create_btn = tk.Button(
            form_frame,
            text="Создать канал",
            command=create_channel,
            font=('Segoe UI', 12, 'bold'),
            fg='#FFFFFF',
            bg='#6366F1',
            relief='flat',
            bd=0,
            pady=12,
            cursor='hand2'
        )
        create_btn.pack(fill='x', pady=10)
        create_btn.bind('<Enter>', lambda e: create_btn.config(bg='#5B58E5'))
        create_btn.bind('<Leave>', lambda e: create_btn.config(bg='#6366F1'))
    
    def start_private_chat(self, username):
        self.main_app.start_private_chat_with(username)
        self.hide()
    
    def join_channel(self, channel_id):
        self.main_app.join_channel(channel_id)
        self.hide()
    
    def clear_content_safe(self):
        """Безопасное очищение содержимого"""
        try:
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        except tk.TclError:
            pass
    
    def show(self):
        """Показывает панель"""
        if not self.is_visible:
            self.side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
            self.side_frame.pack_propagate(False)
            self.is_visible = True
    
    def hide(self):
        """Скрывает панель"""
        if self.is_visible:
            self.side_frame.pack_forget()
            self.is_visible = False

class ModernMessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tandau Messenger")
        self.root.geometry("1200x800")
        self.root.configure(bg='#FFFFFF')
        
        # Клиент для подключения к серверу
        self.client = ChatClient(host='localhost', port=5555)  # Измените на IP сервера
        
        # Настройка колбэков
        self.client.on_message_received = self.handle_server_message
        self.client.on_users_updated = self.handle_users_update
        self.client.on_channels_updated = self.handle_channels_update
        self.client.on_connection_status_changed = self.handle_connection_status
        
        # Современная цветовая схема
        self.colors = {
            'primary': '#6366F1',
            'background': '#FFFFFF',
            'sidebar': '#F9FAFB',
            'text_primary': '#1F2937',
            'text_secondary': '#6B7280',
            'border': '#E5E7EB',
            'hover': '#F3F4F6'
        }
        
        self.current_user = None
        self.is_admin = False
        self.avatar_path = None
        
        # Переменные для чатов
        self.current_chat_type = "public"
        self.current_private_chat_with = None
        self.current_channel_id = None
        self.current_image_path = None
        self.current_video_path = None
        
        # Переменные для голосовых сообщений
        self.is_recording = False
        self.audio_frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Кэш аватарок
        self.avatar_cache = {}
        
        # Создаем интерфейс
        self.create_connection_screen()
    
    def create_connection_screen(self):
        """Создает экран подключения к серверу"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_container = tk.Frame(self.root, bg='#FFFFFF')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        center_frame = tk.Frame(main_container, bg='#FFFFFF')
        center_frame.place(relx=0.5, rely=0.5, anchor='center', width=400)
        
        # Логотип
        logo_frame = tk.Frame(center_frame, bg='#FFFFFF')
        logo_frame.pack(pady=(0, 30))
        
        tk.Label(
            logo_frame,
            text="💬",
            font=('Segoe UI', 48),
            fg='#6366F1',
            bg='#FFFFFF'
        ).pack()
        
        tk.Label(
            logo_frame,
            text="Tandau Messenger",
            font=('Segoe UI', 24, 'bold'),
            fg='#1F2937',
            bg='#FFFFFF'
        ).pack()
        
        tk.Label(
            logo_frame,
            text="Современный мессенджер",
            font=('Segoe UI', 14),
            fg='#6B7280',
            bg='#FFFFFF'
        ).pack(pady=(5, 0))
        
        # Настройки подключения
        settings_frame = tk.Frame(center_frame, bg='#FFFFFF')
        settings_frame.pack(fill='x', pady=20)
        
        tk.Label(
            settings_frame,
            text="Настройки подключения",
            font=('Segoe UI', 16, 'bold'),
            fg='#374151',
            bg='#FFFFFF'
        ).pack(pady=(0, 15))
        
        # Поле IP сервера
        tk.Label(
            settings_frame,
            text="IP адрес сервера:",
            font=('Segoe UI', 12, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        self.host_entry = tk.Entry(
            settings_frame,
            font=('Segoe UI', 14),
            relief='flat',
            bd=1,
            bg='#F9FAFB'
        )
        self.host_entry.insert(0, "localhost")
        self.host_entry.pack(fill='x', pady=(0, 15), ipady=8)
        
        # Поле порта
        tk.Label(
            settings_frame,
            text="Порт:",
            font=('Segoe UI', 12, 'bold'),
            fg='#374151',
            bg='#FFFFFF',
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        self.port_entry = tk.Entry(
            settings_frame,
            font=('Segoe UI', 14),
            relief='flat',
            bd=1,
            bg='#F9FAFB'
        )
        self.port_entry.insert(0, "5555")
        self.port_entry.pack(fill='x', pady=(0, 25), ipady=8)
        
        # Кнопка подключения
        connect_btn = tk.Button(
            settings_frame,
            text="Подключиться к серверу",
            command=self.connect_to_server,
            font=('Segoe UI', 14, 'bold'),
            fg='#FFFFFF',
            bg='#6366F1',
            relief='flat',
            bd=0,
            pady=12,
            cursor='hand2'
        )
        connect_btn.pack(fill='x', pady=(0, 15))
        connect_btn.bind('<Enter>', lambda e: connect_btn.config(bg='#5B58E5'))
        connect_btn.bind('<Leave>', lambda e: connect_btn.config(bg='#6366F1'))
        
        # Статус подключения
        self.connection_status = tk.Label(
            settings_frame,
            text="Не подключено",
            font=('Segoe UI', 12),
            fg='#EF4444',
            bg='#FFFFFF'
        )
        self.connection_status.pack(pady=10)
    
    def connect_to_server(self):
        """Подключается к серверу"""
        host = self.host_entry.get().strip()
        port = int(self.port_entry.get().strip())
        
        self.client.host = host
        self.client.port = port
        
        if self.client.connect():
            self.connection_status.config(text="✅ Подключение установлено", fg='#059669')
            # Переходим к экрану входа
            self.create_login_screen()
        else:
            self.connection_status.config(text="❌ Ошибка подключения", fg='#EF4444')
    
    def handle_connection_status(self, connected):
        """Обрабатывает изменение статуса подключения"""
        if connected:
            print("Подключение к серверу установлено")
        else:
            print("Соединение с сервером разорвано")
            messagebox.showerror("Ошибка", "Соединение с сервером разорвано")
    
    def handle_server_message(self, message_data):
        """Обрабатывает сообщения от сервера"""
        message_type = message_data.get('type')
        
        if message_type == 'login_response':
            self.root.after(0, lambda: self.handle_login_response(message_data))
        
        elif message_type == 'register_response':
            self.root.after(0, lambda: self.handle_register_response(message_data))
        
        elif message_type == 'new_message':
            self.root.after(0, lambda: self.handle_new_message(message_data))
        
        elif message_type == 'messages_data':
            self.root.after(0, lambda: self.handle_messages_data(message_data))
        
        elif message_type == 'users_list':
            self.root.after(0, lambda: self.handle_users_list(message_data))
        
        elif message_type == 'channels_list':
            self.root.after(0, lambda: self.handle_channels_list(message_data))
    
    def handle_login_response(self, message_data):
        """Обрабатывает ответ на вход"""
        if message_data.get('success'):
            self.current_user = message_data.get('user')
            self.is_admin = message_data.get('is_admin', False)
            messagebox.showinfo("Успех", f"Добро пожаловать, {self.current_user}!")
            self.create_messenger_screen()
        else:
            messagebox.showerror("Ошибка", message_data.get('error', 'Ошибка входа'))
    
    def handle_register_response(self, message_data):
        """Обрабатывает ответ на регистрацию"""
        if message_data.get('success'):
            messagebox.showinfo("Успех", "Регистрация завершена!")
            self.create_login_screen()
        else:
            messagebox.showerror("Ошибка", message_data.get('error', 'Ошибка регистрации'))
    
    def handle_new_message(self, message_data):
        """Обрабатывает новое сообщение"""
        # Обновляем интерфейс с новым сообщением
        if hasattr(self, 'scrollable_frame'):
            self.load_messages()
    
    def handle_messages_data(self, message_data):
        """Обрабатывает загруженные сообщения"""
        # Отображаем сообщения в интерфейсе
        if hasattr(self, 'scrollable_frame'):
            self.display_messages(message_data.get('messages', []))
    
    def handle_users_list(self, message_data):
        """Обрабатывает список пользователей"""
        # Обновляем список пользователей в интерфейсе
        if hasattr(self, 'side_panel'):
            # Здесь можно обновить список пользователей в боковой панели
            pass
    
    def handle_channels_list(self, message_data):
        """Обрабатывает список каналов"""
        # Обновляем список каналов в интерфейсе
        if hasattr(self, 'side_panel'):
            # Здесь можно обновить список каналов в боковой панели
            pass
    
    def handle_users_update(self, message_data):
        """Обрабатывает обновление списка пользователей"""
        self.root.after(0, lambda: self.update_users_list(message_data))
    
    def handle_channels_update(self, message_data):
        """Обрабатывает обновление списка каналов"""
        self.root.after(0, lambda: self.update_channels_list(message_data))
    
    def update_users_list(self, users_data):
        """Обновляет список пользователей в UI"""
        # Реализация обновления списка пользователей
        pass
    
    def update_channels_list(self, channels_data):
        """Обновляет список каналов в UI"""
        # Реализация обновления списка каналов
        pass
    
    # Остальные методы (create_login_screen, create_register_screen, create_messenger_screen, etc.)
    # остаются аналогичными предыдущей версии, но используют self.client для общения с сервером
    
    def create_login_screen(self):
        """Создает экран входа (аналогично предыдущей версии, но использует client)"""
        # Реализация аналогична предыдущей, но использует self.client.login()
        pass
    
    def create_register_screen(self):
        """Создает экран регистрации (аналогично предыдущей версии, но использует client)"""
        # Реализация аналогична предыдущей, но использует self.client.register()
        pass
    
    def create_messenger_screen(self):
        """Создает основной экран мессенджера (аналогично предыдущей версии)"""
        # Реализация аналогична предыдущей
        pass
    
    def send_message(self):
        """Отправляет сообщение через клиент"""
        message_text = self.message_entry.get().strip()
        
        if not message_text and not self.current_image_path and not self.current_video_path:
            return
        
        # Отправляем через клиент
        self.client.send_chat_message(
            chat_type=self.current_chat_type,
            message_text=message_text,
            target=self.current_private_chat_with if self.current_chat_type == 'private' else self.current_channel_id if self.current_chat_type == 'channel' else None
        )
        
        # Очищаем поле ввода
        self.message_entry.delete(0, tk.END)
    
    def load_messages(self):
        """Загружает сообщения через клиент"""
        self.client.load_messages(
            chat_type=self.current_chat_type,
            target=self.current_private_chat_with if self.current_chat_type == 'private' else self.current_channel_id if self.current_chat_type == 'channel' else None
        )
    
    def display_messages(self, messages):
        """Отображает сообщения в интерфейсе"""
        # Очищаем текущие сообщения
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if messages:
            for msg in messages[-50:]:
                if not isinstance(msg, dict):
                    continue
                
                is_own = msg.get('user') == self.current_user
                is_admin = msg.get('is_admin', False)
                
                # Создаем пузырь сообщения
                bubble = ModernChatBubble(
                    self.scrollable_frame, 
                    msg, 
                    is_own, 
                    is_admin,
                    on_delete=lambda mid=msg.get('id'): self.delete_message(mid)
                )
                bubble.create_widget()
        else:
            # Сообщение когда чат пустой
            empty_label = tk.Label(
                self.scrollable_frame,
                text="Начните общение! 👋",
                font=('Segoe UI', 16),
                fg='#6B7280',
                bg='#FFFFFF',
                pady=50
            )
            empty_label.pack(expand=True)
        
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def delete_message(self, message_id):
        """Удаляет сообщение через клиент"""
        self.client.delete_message(
            message_id=message_id,
            chat_type=self.current_chat_type,
            target=self.current_private_chat_with if self.current_chat_type == 'private' else self.current_channel_id if self.current_chat_type == 'channel' else None
        )
    
    # Остальные методы остаются аналогичными предыдущей версии

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = ModernMessengerApp(root)
    root.mainloop()