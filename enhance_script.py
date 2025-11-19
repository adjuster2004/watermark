import cv2
import numpy as np
import os
import argparse
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path
import json

def load_config():
    """Загрузка конфигурации если есть"""
    config_path = Path("/app/config/config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def upscale_image(image_path, scale_factor=2.0):
    """Увеличивает разрешение изображения с высоким качеством"""
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            new_size = (int(original_size[0] * scale_factor), 
                       int(original_size[1] * scale_factor))
            
            # Качественное увеличение с LANCZOS фильтром
            upscaled = img.resize(new_size, Image.LANCZOS)
            return upscaled, original_size, new_size
            
    except Exception as e:
        print(f"❌ Ошибка апскейла: {str(e)}")
        return None, None, None

def enhance_document_quality(image_path, output_path, method='smooth_quality', config=None):
    """Улучшает качество документа с сохранением деталей"""
    if config is None:
        config = {}
    
    try:
        print(f"Обработка: {os.path.basename(image_path)}")
        
        # Определяем, нужно ли увеличивать разрешение
        scale_factor = 1.0
        base_method = method
        
        if method.endswith('_2x'):
            scale_factor = 2.0
            base_method = method.replace('_2x', '')
        elif method.endswith('_3x'):
            scale_factor = 3.0
            base_method = method.replace('_3x', '')
        
        # Сначала увеличиваем разрешение если нужно
        if scale_factor > 1.0:
            upscaled_img, original_size, new_size = upscale_image(image_path, scale_factor)
            if upscaled_img is None:
                return False
            
            # Сохраняем временное увеличенное изображение
            temp_path = output_path.replace('.jpg', '_temp.jpg')
            upscaled_img.save(temp_path, 'JPEG', quality=95)
            
            # Теперь применяем основной метод к увеличенному изображению
            img = cv2.imread(temp_path)
            print(f"✅ Разрешение увеличено: {original_size} → {new_size} (x{scale_factor})")
        else:
            img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"Не удалось загрузить изображение: {image_path}")
        
        # Применяем основной метод улучшения
        if base_method == 'smooth_quality':
            result = enhance_smooth_quality(img, output_path, config)
        elif base_method == 'natural_enhance':
            result = enhance_natural_enhance_pil(img, output_path, config)
        elif base_method == 'soft_contrast':
            result = enhance_soft_contrast(img, output_path, config)
        elif base_method == 'professional_gentle':
            result = enhance_professional_gentle(img, output_path, config)
        else:
            result = enhance_smooth_quality(img, output_path, config)
        
        # Удаляем временный файл если он был создан
        if scale_factor > 1.0:
            temp_path = output_path.replace('.jpg', '_temp.jpg')
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        if result:
            print(f"✅ Успешно: {os.path.basename(image_path)}")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при обработке {image_path}: {str(e)}")
        import traceback
        print(f"🔍 Детали ошибки: {traceback.format_exc()}")
        return False

def enhance_smooth_quality(img, output_path, config):
    """
    Плавное улучшение качества без артефактов
    """
    try:
        # 1. Очень легкое шумоподавление
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 
                                                  h=3,
                                                  hColor=3, 
                                                  templateWindowSize=5, 
                                                  searchWindowSize=15)
        
        # 2. Плавное увеличение контраста через LAB
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(12,12))
        l_enhanced = clahe.apply(l)
        
        # 3. Плавное смешивание
        blend_ratio = 0.6
        l_final = cv2.addWeighted(l_enhanced, blend_ratio, l, 1 - blend_ratio, 0)
        
        lab_enhanced = cv2.merge([l_final, a, b])
        contrast_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # 4. Мягкое увеличение резкости
        blurred = cv2.GaussianBlur(contrast_enhanced, (0, 0), 1.0)
        sharpness_strength = 0.3
        sharpened = cv2.addWeighted(contrast_enhanced, 1.0 + sharpness_strength, 
                                   blurred, -sharpness_strength, 0)
        
        # 5. Коррекция гаммы
        final = adjust_gamma_smooth(sharpened, gamma=0.95)
        
        # 6. Сохраняем с максимальным качеством
        cv2.imwrite(output_path, final, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в enhance_smooth_quality: {str(e)}")
        return False

def enhance_natural_enhance_pil(img, output_path, config):
    """
    Естественное улучшение через PIL
    """
    try:
        # Конвертируем OpenCV в PIL
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        # 1. Легкий Unsharp Mask
        pil_img = pil_img.filter(ImageFilter.UnsharpMask(
            radius=0.5,
            percent=50,
            threshold=1
        ))
        
        # 2. Мягкое увеличение контраста
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(1.2)
        
        # 3. Мягкое увеличение резкости
        enhancer = ImageEnhance.Sharpness(pil_img)
        pil_img = enhancer.enhance(1.3)
        
        # 4. Сохранение
        pil_img.save(output_path, 'JPEG', 
                    quality=95, 
                    optimize=True, 
                    subsampling=0)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в enhance_natural_enhance_pil: {str(e)}")
        return False

def enhance_soft_contrast(img, output_path, config):
    """
    Мягкое улучшение контраста без артефактов
    """
    try:
        # 1. Конвертация в float32
        img_float = img.astype(np.float32) / 255.0
        result = np.zeros_like(img_float)
        
        # 2. Мягкое растяжение гистограммы
        for channel in range(3):
            channel_data = img_float[:, :, channel]
            p2, p98 = np.percentile(channel_data, (2, 98))
            if p98 - p2 > 0.1:
                channel_enhanced = (channel_data - p2) / (p98 - p2)
                channel_enhanced = np.clip(channel_enhanced, 0, 1)
            else:
                channel_enhanced = channel_data
            result[:, :, channel] = channel_enhanced
        
        # 3. Преобразование обратно
        result = (result * 255).astype(np.uint8)
        
        # 4. Легкое увеличение резкости
        kernel = np.array([[0, -0.1, 0],
                          [-0.1, 1.4, -0.1],
                          [0, -0.1, 0]])
        final = cv2.filter2D(result, -1, kernel)
        
        cv2.imwrite(output_path, final, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в enhance_soft_contrast: {str(e)}")
        return False

def enhance_professional_gentle(img, output_path, config):
    """
    Профессиональная плавная обработка
    """
    try:
        # 1. Коррекция через YUV
        yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        y, u, v = cv2.split(yuv)
        
        y_float = y.astype(np.float32) / 255.0
        y_enhanced = y_float ** 0.9
        y_enhanced = (y_enhanced * 255).astype(np.uint8)
        
        # 2. Мягкий CLAHE
        clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(16,16))
        y_final = clahe.apply(y_enhanced)
        
        yuv_enhanced = cv2.merge([y_final, u, v])
        result = cv2.cvtColor(yuv_enhanced, cv2.COLOR_YUV2BGR)
        
        # 3. Двухэтапное увеличение резкости
        kernel_light = np.array([[0, -0.05, 0],
                                [-0.05, 1.2, -0.05],
                                [0, -0.05, 0]])
        stage1 = cv2.filter2D(result, -1, kernel_light)
        
        blurred = cv2.GaussianBlur(stage1, (0, 0), 0.5)
        final = cv2.addWeighted(stage1, 1.1, blurred, -0.1, 0)
        
        # 4. Коррекция цвета
        hsv = cv2.cvtColor(final, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.multiply(s, 1.05)
        
        hsv_final = cv2.merge([h, s, v])
        final_bgr = cv2.cvtColor(hsv_final, cv2.COLOR_HSV2BGR)
        
        cv2.imwrite(output_path, final_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в enhance_professional_gentle: {str(e)}")
        return False

def adjust_gamma_smooth(image, gamma=1.0):
    """Плавная коррекция гаммы"""
    try:
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                         for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)
    except Exception as e:
        print(f"❌ Ошибка в adjust_gamma_smooth: {str(e)}")
        return image

def process_all_images(input_dir='/app/input', output_dir='/app/output', method='smooth_quality'):
    """Обрабатывает все изображения в директории"""
    config = load_config()
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    output_path.mkdir(exist_ok=True)
    
    supported_formats = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '.tiff', '.tif']
    
    processed_count = 0
    total_count = 0
    
    for format in supported_formats:
        for image_file in input_path.glob(format):
            total_count += 1
            output_file = output_path / f"enhanced_{image_file.stem}.jpg"
            
            if enhance_document_quality(str(image_file), str(output_file), method, config):
                processed_count += 1
    
    print(f"\n🎉 Обработка завершена!")
    print(f"📊 Успешно обработано: {processed_count}/{total_count} изображений")
    return processed_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Продвинутое улучшение документов')
    parser.add_argument('--input', '-i', default='/app/input', help='Входная директория')
    parser.add_argument('--output', '-o', default='/app/output', help='Выходная директория')
    parser.add_argument('--method', '-m', default='smooth_quality', 
                       choices=['smooth_quality', 'natural_enhance', 'soft_contrast', 
                               'professional_gentle', 'smooth_quality_2x', 'smooth_quality_3x',
                               'natural_enhance_2x', 'natural_enhance_3x', 'soft_contrast_2x',
                               'soft_contrast_3x', 'professional_gentle_2x', 'professional_gentle_3x'],
                       help='Метод улучшения')
    
    args = parser.parse_args()
    
    print("=== 🖼️ Advanced Document Enhancer ===")
    print("Доступные методы:")
    print("📊 smooth_quality - плавное улучшение качества")
    print("🌿 natural_enhance - естественное улучшение") 
    print("☁️  soft_contrast - мягкий контраст без артефактов")
    print("🎨 professional_gentle - профессиональная обработка")
    print("🔼 smooth_quality_2x - плавное качество + 2x разрешение")
    print("🚀 smooth_quality_3x - плавное качество + 3x разрешение")
    print("🔼 natural_enhance_2x - естественное + 2x разрешение")
    print("🚀 natural_enhance_3x - естественное + 3x разрешение")
    print("🔼 soft_contrast_2x - мягкий контраст + 2x разрешение")
    print("🚀 soft_contrast_3x - мягкий контраст + 3x разрешение")
    print("🔼 professional_gentle_2x - профессиональное + 2x разрешение")
    print("🚀 professional_gentle_3x - профессиональное + 3x разрешение")
    print("=====================================")
    
    process_all_images(args.input, args.output, args.method)