from flask import Flask, request, redirect, url_for, flash, send_file, render_template_string, jsonify, get_flashed_messages
import os
import uuid
from pathlib import Path
from enhance_script import enhance_document_quality
import cv2
from PIL import Image
import io
import logging
from datetime import datetime
import base64
import shutil

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'dev-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file

# Директории
UPLOAD_FOLDER = '/app/uploads'
PROCESSED_FOLDER = '/app/processed'

for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
    Path(folder).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_dimensions(image_path):
    """Получить размеры изображения"""
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        logger.error(f"Error getting image dimensions: {str(e)}")
        return (0, 0)

def get_file_info(file_path):
    """Получить информацию о файле: размер и разрешение"""
    try:
        # Размер файла
        size_bytes = os.path.getsize(file_path)
        
        # Размеры изображения
        width, height = get_image_dimensions(file_path)
        
        return {
            'size_bytes': size_bytes,
            'width': width,
            'height': height
        }
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return {'size_bytes': 0, 'width': 0, 'height': 0}

def cleanup_folders():
    """Очистка папок uploads и processed"""
    try:
        logger.info("Начинаем очистку папок...")
        
        # Очистка папки uploads
        if os.path.exists(UPLOAD_FOLDER):
            for file_path in Path(UPLOAD_FOLDER).glob("*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Удален файл из uploads: {file_path.name}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}")
        
        # Очистка папки processed
        if os.path.exists(PROCESSED_FOLDER):
            for file_path in Path(PROCESSED_FOLDER).glob("*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Удален файл из processed: {file_path.name}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}")
        
        # Очистка глобальных переменных
        global processed_files_db, file_variants
        processed_files_db.clear()
        file_variants.clear()
        
        logger.info("Очистка папок завершена успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при очистке папок: {str(e)}")
        return False

# HTML шаблон главной страницы
MAIN_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Улучшение качества документов</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .upload-area {
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s;
            background: #f8f9fa;
            margin-bottom: 1rem;
            cursor: pointer;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #e9ecef;
        }
        .upload-area.has-file {
            border-color: #198754;
            background: #f8fff9;
        }
        .file-info {
            background: white;
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
            border: 1px solid #dee2e6;
        }
        .file-name {
            font-weight: bold;
            color: #198754;
        }
        .file-size {
            color: #6c757d;
            font-size: 0.9em;
        }
        .comparison-container {
            display: flex;
            gap: 15px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .image-comparison {
            flex: 1;
            min-width: 280px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .comparison-image {
            max-width: 100%;
            max-height: 350px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .image-label {
            margin-top: 8px;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 4px;
            display: inline-block;
            font-size: 0.9em;
        }
        .original-label {
            background: #dc3545;
            color: white;
        }
        .enhanced-label {
            background: #198754;
            color: white;
        }
        .file-card {
            transition: all 0.3s;
            border-left: 3px solid #007bff;
            margin-bottom: 0.75rem;
        }
        .file-card:hover {
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .method-badge {
            font-size: 0.75em;
        }
        .comparison-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        .compact-form {
            margin-bottom: 1rem;
        }
        .btn-group-compact .btn {
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
        }
        .file-input-wrapper {
            position: relative;
            overflow: hidden;
            display: inline-block;
            width: 100%;
        }
        .file-input-wrapper input[type=file] {
            position: absolute;
            left: 0;
            top: 0;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        .processing-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .processing-spinner {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
        }
        .variants-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .variant-card {
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
        }
        .variant-card:hover {
            border-color: #007bff;
            transform: translateY(-2px);
        }
        .variant-card.selected {
            border-color: #198754;
            background-color: #f8fff9;
        }
        .variant-checkbox {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 20px;
            height: 20px;
        }
        .variant-image {
            max-width: 100%;
            max-height: 250px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .variant-actions {
            margin-top: 10px;
        }
        .selection-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .method-description {
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 5px;
        }
        .file-stats {
            font-size: 0.8em;
            color: #6c757d;
            margin-top: 8px;
            line-height: 1.3;
        }
        .file-size-badge {
            background: #6c757d;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.75em;
        }
        .resolution-badge {
            background: #17a2b8;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.75em;
        }
        .cleanup-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 10px;
            margin: 10px 0;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="processing-overlay" id="processingOverlay">
        <div class="processing-spinner">
            <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
            <h5>Обработка изображения...</h5>
            <p class="text-muted">Создаем все варианты улучшения</p>
            <div class="cleanup-info mt-3">
                <i class="fas fa-info-circle text-warning"></i>
                <small>Выполняется очистка предыдущих файлов и создание новых вариантов</small>
            </div>
        </div>
    </div>

    <nav class="navbar navbar-expand-lg navbar-dark bg-primary py-2">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-magic"></i>Система улучшения качества документов
            </a>
        </div>
    </nav>

    <div class="container mt-3" id="messages">
        <!-- Сообщения будут здесь -->
    </div>

    <div class="container mt-3">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <!-- Форма загрузки -->
                <div class="card shadow-sm compact-form">
                    <div class="card-header bg-primary text-white py-2">
                        <h5 class="mb-0"><i class="fas fa-upload"></i> Загрузка изображения</h5>
                    </div>
                    <div class="card-body py-3">
                                           
                        <form action="/process_all" method="post" enctype="multipart/form-data" id="uploadForm">
                            <div class="file-input-wrapper">
                                <div class="upload-area" id="uploadArea">
                                    <i class="fas fa-cloud-upload-alt fa-2x mb-2 text-primary"></i>
                                    <h6 class="mb-2" id="uploadText">Нажмите для выбора файла</h6>
                                    <p class="text-muted small mb-3">JPG, PNG, BMP, TIFF (макс. 16MB)</p>
                                    <div id="fileInfo" class="file-info" style="display: none;">
                                        <div>
                                            <i class="fas fa-file-image text-success me-2"></i>
                                            <span id="fileName" class="file-name"></span>
                                            <span id="fileSize" class="file-size ms-2"></span>
                                        </div>
                                    </div>
                                    <input type="file" name="file" id="fileInput" required 
                                           accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif">
                                </div>
                            </div>

                            <div class="row g-2 align-items-center mt-3">
                                <div class="col-md-12">
                                    <button type="submit" class="btn btn-primary w-100" id="submitBtn" disabled>
                                        <i class="fas fa-bolt"></i> Создать все варианты улучшения
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Секция выбора варианта -->
                <div class="selection-section" id="selectionSection" style="display: none;">
                    <h5 class="text-center mb-4"><i class="fas fa-clipboard-check"></i> Выберите лучший вариант</h5>
                    <div class="variants-grid" id="variantsGrid">
                        <!-- Варианты будут здесь -->
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-success" id="confirmSelection" onclick="confirmSelection()" style="display: none;">
                            <i class="fas fa-check"></i> Подтвердить выбор
                        </button>
                    </div>
                </div>

                <!-- Секция сравнения -->
                <div class="comparison-section" id="comparisonSection" style="display: none;">
                    <h5 class="text-center mb-4"><i class="fas fa-columns"></i> Сравнение результатов</h5>
                    <div class="comparison-container" id="comparisonContainer">
                        <!-- Сравнение будет здесь -->
                    </div>
                </div>

                <!-- Список файлов -->
                <div class="card shadow-sm mt-4">
                    <div class="card-header bg-secondary text-white py-2">
                        <h6 class="mb-0"><i class="fas fa-history"></i> История обработки (последние 10 файлов)</h6>
                    </div>
                    <div class="card-body py-2">
                        <div id="filesList">
                            <!-- Список файлов будет здесь -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-4">
        <div class="container">
            <p class="small mb-0">&copy; 2025-2026 <a href="https://web.telegram.org/k/#@adjuster2004">@Adjuster2004</a>  Система улучшения качества документов</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentFileId = null;
        let processedVariants = {};
        
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const message = urlParams.get('message');
            const type = urlParams.get('type');
            const fileId = urlParams.get('fileId');
            
            if (message) {
                showMessage(message, type || 'success');
            }

            if (fileId) {
                showComparison(fileId);
            }

            loadFilesList();
            setupFileInput();
        });

        function setupFileInput() {
            const fileInput = document.getElementById('fileInput');
            const uploadArea = document.getElementById('uploadArea');
            const uploadText = document.getElementById('uploadText');
            const fileInfo = document.getElementById('fileInfo');
            const fileName = document.getElementById('fileName');
            const fileSize = document.getElementById('fileSize');
            const submitBtn = document.getElementById('submitBtn');

            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    updateFileDisplay(file);
                } else {
                    resetFileDisplay();
                }
            });

            function updateFileDisplay(file) {
                fileName.textContent = file.name;
                fileSize.textContent = `(${formatFileSize(file.size)})`;
                fileInfo.style.display = 'block';
                uploadText.textContent = 'Файл выбран';
                uploadArea.classList.add('has-file');
                submitBtn.disabled = false;
            }

            function resetFileDisplay() {
                fileInfo.style.display = 'none';
                uploadText.textContent = 'Нажмите для выбора файла';
                uploadArea.classList.remove('has-file');
                submitBtn.disabled = true;
            }

            // Drag and drop
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, highlight, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, unhighlight, false);
            });

            function highlight() {
                uploadArea.style.borderColor = '#667eea';
                uploadArea.style.background = '#e9ecef';
            }

            function unhighlight() {
                const hasFile = uploadArea.classList.contains('has-file');
                uploadArea.style.borderColor = hasFile ? '#198754' : '#dee2e6';
                uploadArea.style.background = hasFile ? '#f8fff9' : '#f8f9fa';
            }

            uploadArea.addEventListener('drop', function(e) {
                const dt = e.dataTransfer;
                const file = dt.files[0];
                if (file && file.type.startsWith('image/')) {
                    fileInput.files = dt.files;
                    fileInput.dispatchEvent(new Event('change'));
                }
            });
        }

        function formatFileSize(bytes) {
            if (!bytes || bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function formatResolution(width, height) {
            if (!width || !height) return 'Неизвестно';
            return `${width} × ${height}`;
        }

        function showMessage(message, type) {
            const messagesDiv = document.getElementById('messages');
            const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
            const icon = type === 'error' ? 'fa-exclamation-triangle' : 'fa-check-circle';
            
            messagesDiv.innerHTML = `
                <div class="alert ${alertClass} alert-dismissible fade show py-2">
                    <i class="fas ${icon}"></i> ${message}
                    <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
                </div>
            `;
        }

        function showVariantsSelection(fileId, variants) {
            currentFileId = fileId;
            processedVariants = variants;
            
            const selectionSection = document.getElementById('selectionSection');
            const variantsGrid = document.getElementById('variantsGrid');
            
            selectionSection.style.display = 'block';
            selectionSection.scrollIntoView({ behavior: 'smooth' });
            
            let variantsHtml = '';
            
            // Добавляем оригинал для сравнения
            variantsHtml += `
                <div class="variant-card" onclick="selectVariant('original')">
                    <input type="radio" class="variant-checkbox" name="selectedVariant" value="original">
                    <img src="/preview-original/${fileId}" class="variant-image" alt="Оригинал">
                    <h6>Оригинал</h6>
                    <div class="method-description">Исходное изображение без изменений</div>
                    <div class="file-stats" id="originalStats">
                        <i class="fas fa-spinner fa-spin"></i> Загрузка информации...
                    </div>
                    <div class="variant-actions">
                        <a href="/preview-original/${fileId}" class="btn btn-outline-primary btn-sm" target="_blank">
                            <i class="fas fa-eye"></i> Просмотр
                        </a>
                    </div>
                </div>
            `;
            
            // Добавляем все обработанные варианты
            Object.entries(variants).forEach(([method, variant]) => {
                const methodNames = {
                    'smooth_quality': 'Плавное качество',
                    'natural_enhance': 'Естественное улучшение', 
                    'soft_contrast': 'Мягкий контраст',
                    'professional_gentle': 'Профессиональная',
                    'smooth_quality_2x': 'Плавное качество + 2x',
                    'smooth_quality_3x': 'Плавное качество + 3x',
                    'natural_enhance_2x': 'Естественное + 2x',
                    'natural_enhance_3x': 'Естественное + 3x',
                    'soft_contrast_2x': 'Мягкий контраст + 2x',
                    'soft_contrast_3x': 'Мягкий контраст + 3x',
                    'professional_gentle_2x': 'Профессиональная + 2x',
                    'professional_gentle_3x': 'Профессиональная + 3x'
                };

                const descriptions = {
                    'smooth_quality': 'Лучше для документов',
                    'natural_enhance': 'Сохраняет натуральность',
                    'soft_contrast': 'Без резких переходов', 
                    'professional_gentle': 'Максимальное качество',
                    'smooth_quality_2x': 'Плавное качество + увеличение разрешения 2x',
                    'smooth_quality_3x': 'Плавное качество + увеличение разрешения 3x',
                    'natural_enhance_2x': 'Естественное улучшение + увеличение разрешения 2x',
                    'natural_enhance_3x': 'Естественное улучшение + увеличение разрешения 3x',
                    'soft_contrast_2x': 'Мягкий контраст + увеличение разрешения 2x',
                    'soft_contrast_3x': 'Мягкий контраст + увеличение разрешения 3x',
                    'professional_gentle_2x': 'Профессиональная обработка + увеличение разрешения 2x',
                    'professional_gentle_3x': 'Профессиональная обработка + увеличение разрешения 3x'
                };
                
                variantsHtml += `
                    <div class="variant-card" onclick="selectVariant('${method}')">
                        <input type="radio" class="variant-checkbox" name="selectedVariant" value="${method}">
                        <img src="/preview-variant/${fileId}/${method}" class="variant-image" alt="${methodNames[method]}">
                        <h6>${methodNames[method]}</h6>
                        <div class="method-description">${descriptions[method]}</div>
                        <div class="file-stats" id="stats-${method}">
                            <i class="fas fa-spinner fa-spin"></i> Загрузка информации...
                        </div>
                        <div class="variant-actions">
                            <a href="/preview-variant/${fileId}/${method}" class="btn btn-outline-primary btn-sm" target="_blank">
                                <i class="fas fa-eye"></i> Просмотр
                            </a>
                            <a href="/download-variant/${fileId}/${method}" class="btn btn-outline-success btn-sm">
                                <i class="fas fa-download"></i> Скачать
                            </a>
                        </div>
                    </div>
                `;
            });
            
            variantsGrid.innerHTML = variantsHtml;
            
            // Загружаем информацию о размерах файлов
            loadFileStats(fileId, variants);
        }

        function loadFileStats(fileId, variants) {
            // Загружаем информацию для оригинала
            fetch(`/file-info/original/${fileId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.info;
                        document.getElementById('originalStats').innerHTML = `
                            <span class="file-size-badge">${formatFileSize(stats.size_bytes)}</span>
                            <span class="resolution-badge">${formatResolution(stats.width, stats.height)}</span>
                        `;
                    }
                });
            
            // Загружаем информацию для каждого варианта
            Object.keys(variants).forEach(method => {
                fetch(`/file-info/variant/${fileId}/${method}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const stats = data.info;
                            document.getElementById(`stats-${method}`).innerHTML = `
                                <span class="file-size-badge">${formatFileSize(stats.size_bytes)}</span>
                                <span class="resolution-badge">${formatResolution(stats.width, stats.height)}</span>
                            `;
                        }
                    });
            });
        }

        function selectVariant(method) {
            // Снимаем выделение со всех карточек
            document.querySelectorAll('.variant-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // Выделяем выбранную карточку
            const selectedCard = document.querySelector(`.variant-card input[value="${method}"]`).closest('.variant-card');
            selectedCard.classList.add('selected');
            
            // Отмечаем чекбокс
            document.querySelectorAll('.variant-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
            document.querySelector(`.variant-checkbox[value="${method}"]`).checked = true;
            
            // Показываем кнопку подтверждения
            document.getElementById('confirmSelection').style.display = 'inline-block';
        }

        function confirmSelection() {
            const selectedVariant = document.querySelector('input[name="selectedVariant"]:checked');
            if (!selectedVariant) {
                showMessage('Пожалуйста, выберите вариант', 'error');
                return;
            }
            
            const method = selectedVariant.value;
            if (method === 'original') {
                // Для оригинала просто показываем сообщение
                showMessage('Выбран оригинальный файл', 'success');
                return;
            }
            
            // Сохраняем выбранный вариант как основной
            fetch(`/save-selected/${currentFileId}/${method}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Выбранный вариант сохранен как основной!', 'success');
                    loadFilesList();
                    
                    // Показываем сравнение
                    showComparison(currentFileId);
                } else {
                    showMessage('Ошибка при сохранении варианта', 'error');
                }
            })
            .catch(error => {
                console.error('Error saving selection:', error);
                showMessage('Ошибка при сохранении варианта', 'error');
            });
        }

        function showComparison(fileId) {
            document.getElementById('comparisonSection').style.display = 'block';
            document.getElementById('comparisonSection').scrollIntoView({ 
                behavior: 'smooth' 
            });
            
            fetch('/api/files')
                .then(response => response.json())
                .then(files => {
                    const file = files.find(f => f.id === fileId);
                    if (file) {
                        displayComparison(file);
                    }
                });
        }

        function displayComparison(file) {
            const container = document.getElementById('comparisonContainer');
            container.innerHTML = `
                <div class="image-comparison">
                    <img src="/preview-original/${file.id}" class="comparison-image" alt="Оригинал">
                    <div class="image-label original-label">
                        <i class="fas fa-image"></i> ОРИГИНАЛ
                    </div>
                </div>
                <div class="image-comparison">
                    <img src="/preview/${file.id}" class="comparison-image" alt="Улучшенная версия">
                    <div class="image-label enhanced-label">
                        <i class="fas fa-magic"></i> УЛУЧШЕННАЯ ВЕРСИЯ
                    </div>
                    <div class="mt-2 text-center">
                        <small class="text-muted">
                            <strong>Метод:</strong> <span class="badge bg-primary method-badge">${file.method}</span><br>
                            <strong>Обработано:</strong> ${file.processed_time}
                        </small>
                    </div>
                </div>
            `;
        }

        function loadFilesList() {
            fetch('/api/files')
                .then(response => response.json())
                .then(files => {
                    const filesListDiv = document.getElementById('filesList');
                    
                    if (files.length === 0) {
                        filesListDiv.innerHTML = '<p class="text-muted text-center small my-2">Нет обработанных файлов</p>';
                        return;
                    }

                    let filesHtml = '';
                    files.slice(-10).reverse().forEach(file => {
                        filesHtml += `
                            <div class="card file-card">
                                <div class="card-body py-2">
                                    <div class="row align-items-center">
                                        <div class="col-md-7">
                                            <h6 class="mb-1 small">
                                                <i class="fas fa-file-image text-primary me-1"></i> 
                                                ${file.original_name}
                                            </h6>
                                            <p class="text-muted mb-0 small">
                                                <span class="badge bg-primary method-badge">${file.method}</span>
                                                <span class="ms-2">${file.processed_time}</span>
                                            </p>
                                        </div>
                                        <div class="col-md-5 text-end">
                                            <div class="btn-group btn-group-compact">
                                                <a href="/download/${file.id}" class="btn btn-success btn-sm" title="Скачать">
                                                    <i class="fas fa-download"></i>
                                                </a>
                                                <a href="/preview/${file.id}" class="btn btn-info btn-sm" target="_blank" title="Просмотр">
                                                    <i class="fas fa-eye"></i>
                                                </a>
                                                <button onclick="showComparison('${file.id}')" class="btn btn-warning btn-sm" title="Сравнение">
                                                    <i class="fas fa-columns"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });

                    filesListDiv.innerHTML = filesHtml;
                })
                .catch(error => {
                    console.error('Error loading files:', error);
                    document.getElementById('filesList').innerHTML = '<p class="text-muted text-center small my-2">Ошибка загрузки списка файлов</p>';
                });
        }

        document.getElementById('uploadForm')?.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            const submitBtn = document.getElementById('submitBtn');
            const processingOverlay = document.getElementById('processingOverlay');
            
            // Проверяем, что файл действительно выбран
            if (!fileInput.files || fileInput.files.length === 0) {
                showMessage('Пожалуйста, выберите файл', 'error');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Обработка...';
            processingOverlay.style.display = 'flex';
            
            // Отправляем форму через fetch
            const formData = new FormData(document.getElementById('uploadForm'));
            
            fetch('/process_all', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                processingOverlay.style.display = 'none';
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-bolt"></i> Создать все варианты улучшения';
                
                if (data.success) {
                    showVariantsSelection(data.file_id, data.variants);
                } else {
                    showMessage(data.message || 'Ошибка при обработке', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                processingOverlay.style.display = 'none';
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-bolt"></i> Создать все варианты улучшения';
                showMessage('Ошибка при обработке файла', 'error');
            });
        });

        // Глобальные функции
        window.showComparison = function(fileId) {
            document.getElementById('comparisonSection').style.display = 'block';
            document.getElementById('comparisonSection').scrollIntoView({ 
                behavior: 'smooth' 
            });
            
            fetch('/api/files')
                .then(response => response.json())
                .then(files => {
                    const file = files.find(f => f.id === fileId);
                    if (file) {
                        displayComparison(file);
                    }
                });
        };
        
        window.selectVariant = selectVariant;
        window.confirmSelection = confirmSelection;
    </script>
</body>
</html>
'''

# Глобальный список для хранения информации о файлах
processed_files_db = []
# Словарь для хранения всех вариантов обработки
file_variants = {}

@app.route('/')
def index():
    """Главная страница"""
    try:
        message = request.args.get('message')
        message_type = request.args.get('type', 'success')
        file_id = request.args.get('fileId')
        
        messages_html = ''
        if message:
            alert_class = 'alert-danger' if message_type == 'error' else 'alert-success'
            icon = 'fa-exclamation-triangle' if message_type == 'error' else 'fa-check-circle'
            messages_html = f'''
                <div class="alert {alert_class} alert-dismissible fade show py-2">
                    <i class="fas {icon}"></i> {message}
                    <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
                </div>
            '''
        
        html = MAIN_PAGE.replace(
            '<!-- Сообщения будут здесь -->',
            messages_html
        )
        
        return html
        
    except Exception as e:
        logger.error(f"Error in index: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/file-info/original/<file_id>')
def file_info_original(file_id):
    """Информация о оригинальном файле"""
    try:
        original_files = list(Path(UPLOAD_FOLDER).glob(f"{file_id}_original.*"))
        if original_files:
            info = get_file_info(original_files[0])
            return jsonify({'success': True, 'info': info})
        return jsonify({'success': False, 'message': 'Файл не найден'})
    except Exception as e:
        logger.error(f"Error getting original file info: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/file-info/variant/<file_id>/<method>')
def file_info_variant(file_id, method):
    """Информация о варианте обработки"""
    try:
        if file_id in file_variants and method in file_variants[file_id]:
            variant_path = file_variants[file_id][method]['path']
            if os.path.exists(variant_path):
                info = get_file_info(variant_path)
                return jsonify({'success': True, 'info': info})
        return jsonify({'success': False, 'message': 'Вариант не найден'})
    except Exception as e:
        logger.error(f"Error getting variant file info: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/process_all', methods=['POST'])
def process_all_variants():
    """Обработка файла всеми методами с предварительной очисткой"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Файл не выбран'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Файл не выбран'})
        
        if file and allowed_file(file.filename):
            # Выполняем очистку перед обработкой
            cleanup_success = cleanup_folders()
            if not cleanup_success:
                logger.warning("Очистка папок завершена с предупреждениями, но продолжаем обработку")
            
            # Проверяем, что файл действительно был загружен
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size == 0:
                return jsonify({'success': False, 'message': 'Файл пустой или не был загружен'})
            
            file_id = str(uuid.uuid4())
            original_ext = Path(file.filename).suffix
            original_filename = f"{file_id}_original{original_ext}"
            
            # Сохраняем оригинальный файл
            original_path = os.path.join(UPLOAD_FOLDER, original_filename)
            file.save(original_path)
            logger.info(f"Файл сохранен: {original_path}, размер: {file_size} байт")
            
            # Методы обработки
            methods = [
            'smooth_quality', 'natural_enhance', 'soft_contrast', 'professional_gentle',
            'smooth_quality_2x', 'smooth_quality_3x',
            'natural_enhance_2x', 'natural_enhance_3x', 
            'soft_contrast_2x', 'soft_contrast_3x',
            'professional_gentle_2x', 'professional_gentle_3x']
            variants = {}
            
            # Обрабатываем каждым методом
            for method in methods:
                processed_filename = f"{file_id}_{method}.jpg"
                processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
                
                logger.info(f"Обработка методом: {method}")
                success = enhance_document_quality(original_path, processed_path, method)
                
                if success and os.path.exists(processed_path):
                    # Получаем информацию о файле
                    file_info = get_file_info(processed_path)
                    variants[method] = {
                        'path': processed_path,
                        'filename': processed_filename,
                        'info': file_info
                    }
                    logger.info(f"Успешно обработан методом {method}")
                else:
                    logger.error(f"Ошибка обработки методом {method}")
            
            # Сохраняем информацию о вариантах
            file_variants[file_id] = variants
            
            # По умолчанию выбираем первый успешный метод как основной
            default_method = next(iter(variants.keys())) if variants else 'smooth_quality'
            if variants:
                file_info = {
                    'id': file_id,
                    'original_name': file.filename,
                    'original_path': original_path,
                    'processed_path': variants[default_method]['path'],
                    'method': default_method,
                    'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                processed_files_db.append(file_info)
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'variants': {method: data['filename'] for method, data in variants.items()}
            })
            
        else:
            return jsonify({'success': False, 'message': f'Недопустимый формат файла: {file.filename}'})
            
    except Exception as e:
        error_msg = f'Ошибка при обработке: {str(e)}'
        logger.error(f"Ошибка в process_all_variants: {str(e)}")
        return jsonify({'success': False, 'message': error_msg})

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """API для очистки всех файлов"""
    try:
        success = cleanup_folders()
        if success:
            return jsonify({'success': True, 'message': 'Все файлы успешно удалены'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка при удалении файлов'})
    except Exception as e:
        logger.error(f"Ошибка при очистке файлов: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# Остальные маршруты остаются без изменений
@app.route('/save-selected/<file_id>/<method>', methods=['POST'])
def save_selected_variant(file_id, method):
    """Сохраняет выбранный вариант как основной"""
    try:
        # Находим файл в базе
        file_info = None
        for i, f in enumerate(processed_files_db):
            if f['id'] == file_id:
                file_info = f
                break
        
        if file_info and file_id in file_variants and method in file_variants[file_id]:
            # Обновляем информацию о файле
            file_info['processed_path'] = file_variants[file_id][method]['path']
            file_info['method'] = method
            file_info['processed_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"Выбран вариант {method} для файла {file_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Файл или вариант не найден'})
            
    except Exception as e:
        logger.error(f"Ошибка при сохранении варианта: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/preview-variant/<file_id>/<method>')
def preview_variant(file_id, method):
    """Просмотр варианта обработки"""
    try:
        if file_id in file_variants and method in file_variants[file_id]:
            variant_path = file_variants[file_id][method]['path']
            if os.path.exists(variant_path):
                return send_file(variant_path)
        
        return "Вариант не найден", 404
            
    except Exception as e:
        logger.error(f"Ошибка при preview варианта: {str(e)}")
        return f"Ошибка: {str(e)}", 500

@app.route('/download-variant/<file_id>/<method>')
def download_variant(file_id, method):
    """Скачать вариант обработки"""
    try:
        if file_id in file_variants and method in file_variants[file_id]:
            variant_path = file_variants[file_id][method]['path']
            if os.path.exists(variant_path):
                original_name = "enhanced_image.jpg"
                for file_info in processed_files_db:
                    if file_info['id'] == file_id:
                        name_without_ext = Path(file_info['original_name']).stem
                        original_name = f"enhanced_{name_without_ext}_{method}.jpg"
                        break
                
                return send_file(
                    variant_path,
                    as_attachment=True,
                    download_name=original_name
                )
        
        return "Вариант не найден", 404
            
    except Exception as e:
        logger.error(f"Ошибка при скачивании варианта: {str(e)}")
        return f"Ошибка: {str(e)}", 500

@app.route('/preview-original/<file_id>')
def preview_original(file_id):
    """Просмотр оригинального файла"""
    try:
        original_files = list(Path(UPLOAD_FOLDER).glob(f"{file_id}_original.*"))
        if original_files:
            return send_file(original_files[0])
        else:
            return "Файл не найден", 404
    except Exception as e:
        logger.error(f"Ошибка при preview оригинала: {str(e)}")
        return f"Ошибка: {str(e)}", 500

@app.route('/preview/<file_id>')
def preview_file(file_id):
    """Просмотр основного обработанного файла"""
    try:
        for file_info in processed_files_db:
            if file_info['id'] == file_id:
                if os.path.exists(file_info['processed_path']):
                    return send_file(file_info['processed_path'])
        return "Файл не найден", 404
    except Exception as e:
        logger.error(f"Ошибка при preview: {str(e)}")
        return f"Ошибка: {str(e)}", 500

@app.route('/download/<file_id>')
def download_file(file_id):
    """Скачать основной обработанный файл"""
    try:
        for file_info in processed_files_db:
            if file_info['id'] == file_id:
                if os.path.exists(file_info['processed_path']):
                    name_without_ext = Path(file_info['original_name']).stem
                    original_name = f"enhanced_{name_without_ext}.jpg"
                    return send_file(
                        file_info['processed_path'],
                        as_attachment=True,
                        download_name=original_name
                    )
        return "Файл не найден", 404
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {str(e)}")
        return f"Ошибка: {str(e)}", 500

@app.route('/api/files')
def api_files():
    """API для получения списка файлов"""
    return jsonify(processed_files_db)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'document_enhancer',
        'processed_files': len(processed_files_db),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Document Enhancer Web Server...")
    print("📍 Web interface: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)