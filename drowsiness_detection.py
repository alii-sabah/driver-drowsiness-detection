import cv2  # مكتبة معالجة الصور والفيديو (تستخدم لفتح الكاميرا ومعالجة الفريمات)
import mediapipe as mp  # مكتبة الذكاء الاصطناعي من جوجل (تستخدم لتحديد نقاط الوجه)
import numpy as np  # مكتبة العمليات الحسابية (تستخدم لحساب المسافات بين النقاط)
import tkinter as tk  # مكتبة بناء الواجهات الرسومية (لعمل نافذة البرنامج)
import requests  # مكتبة لإرسال طلبات HTTP (تستخدم للتواصل اللاسلكي مع الـ ESP32)
from datetime import datetime  # مكتبة للتعامل مع الوقت والتاريخ

# --- إعدادات الذكاء الاصطناعي (MediaPipe) ---
mp_face_mesh = mp.solutions.face_mesh  # استدعاء حلول "شبكة الوجه"
# تهيئة الموديل: تحديد النقاط الدقيقة، وتحديد وجه واحد فقط للمعالجة
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# مصفوفة تحتوي على أرقام النقاط التي ترسم محيط العين اليسرى واليمنى بالكامل
LEFT_EYE_FULL = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE_FULL = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

def get_ear(landmarks, eye_points):
    """ دالة حساب نسبة فتحة العين (Eye Aspect Ratio) """
    # حساب المسافة بين الجفن العلوي والسفلي (نقطتين عمودية)
    p2_p6 = np.linalg.norm(np.array([landmarks[eye_points[12]].x, landmarks[eye_points[12]].y]) - 
                           np.array([landmarks[eye_points[4]].x, landmarks[eye_points[4]].y]))
    # حساب المسافة العمودية الثانية لزيادة الدقة
    p3_p5 = np.linalg.norm(np.array([landmarks[eye_points[11]].x, landmarks[eye_points[11]].y]) - 
                           np.array([landmarks[eye_points[5]].x, landmarks[eye_points[5]].y]))
    # حساب المسافة الأفقية (عرض العين)
    p1_p4 = np.linalg.norm(np.array([landmarks[eye_points[8]].x, landmarks[eye_points[8]].y]) - 
                           np.array([landmarks[eye_points[0]].x, landmarks[eye_points[0]].y]))
    # المعادلة الرياضية للنسبة: مجموع الارتفاعات مقسوم على ضعف العرض
    return (p2_p6 + p3_p5) / (2.0 * p1_p4)

# --- إعداد نافذة البرنامج (Tkinter) ---
root = tk.Tk()  # إنشاء النافذة الرئيسية
root.title("Driver Safety System")  # وضع عنوان للنافذة
root.configure(bg="#121212")  # تلوين الخلفية بالأسود الغامق

video_label = tk.Label(root, bg="#121212")  # مكان مخصص لعرض فيديو الكاميرا
video_label.pack(pady=10)  # تثبيت المكان في النافذة مع ترك مسافة (Padding)

# --- إعدادات الكاميرا والعدادات ---
cap = cv2.VideoCapture(0)  # فتح الكاميرا الافتراضية للابتوب
COUNTER = 0  # عداد يحسب كم "فريم" بقيت العين فيها مغمضة
ALARM_THRESHOLD = 55  # عدد الفريمات المطلوب (حوالي ثانيتين) قبل إطلاق الإنذار

# --- إعدادات التواصل اللاسلكي ---
ESP32_URL = "http://192.168.4.1/"  # عنوان الـ IP الخاص بالـ ESP32 (وضع الـ AP)

def send_to_esp32(state):
    """ دالة إرسال إشارة للـ ESP32 لتشغيل أو إطفاء الجرس """
    try:
        # إرسال طلب للمتصفح: state=1 تشغيل، state=0 إطفاء
        requests.get(f"{ESP32_URL}?state={state}", timeout=0.05)
    except:
        pass  # في حال عدم وجود اتصال، البرنامج يستمر ولا يتوقف

def update():
    """ الدالة الأساسية التي تتكرر باستمرار لمعالجة الفيديو """
    global COUNTER
    ret, frame = cap.read()  # قراءة صورة (فريم) من الكاميرا
    if not ret: return  # إذا فشلت القراءة، اخرج من الدالة

    frame = cv2.flip(frame, 1)  # قلب الصورة لتكون مثل المرآة
    h, w, _ = frame.shape  # الحصول على أبعاد الصورة (الطول والعرض)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # تحويل الألوان ليفهمها Mediapipe
    results = face_mesh.process(rgb_frame)  # معالجة الصورة لاستخراج نقاط الوجه

    status = "AWAKE"  # الحالة الافتراضية (مستيقظ)
    color = (0, 255, 0)  # اللون الافتراضي (أخضر)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark  # استخراج نقاط أول وجه مكتشف
        ear_l = get_ear(landmarks, LEFT_EYE_FULL)  # حساب نسبة العين اليسرى
        ear_r = get_ear(landmarks, RIGHT_EYE_FULL)  # حساب نسبة العين اليمنى
        avg_ear = (ear_l + ear_r) / 2.0  # حساب متوسط النسبتين للعينين


        # رسم نقاط خضراء صغيرة حول مدار العين بالكامل للتوضيح
        for idx in LEFT_EYE_FULL + RIGHT_EYE_FULL:
            pt = landmarks[idx]
            cv2.circle(frame, (int(pt.x * w), int(pt.y * h)), 1, (0, 255, 0), -1)

       # فحص هل العين مغلقة (النسبة أقل من 0.20)
        if avg_ear < 0.20:
            COUNTER += 1  # زيادة العداد لأن العين مغلقة
            
            # 1. رسم خط أحمر سميك فوق العين اليمنى (النقاط 159 و 145)
            cv2.line(frame, (int(landmarks[159].x*w), int(landmarks[159].y*h)), 
                     (int(landmarks[145].x*w), int(landmarks[145].y*h)), (0, 0, 255), 3)
            
            # 2. رسم خط أحمر سميك فوق العين اليسرى (النقاط 386 و 374)
            cv2.line(frame, (int(landmarks[386].x*w), int(landmarks[386].y*h)), 
                     (int(landmarks[374].x*w), int(landmarks[374].y*h)), (0, 0, 255), 3)
            
            # إذا استمر الإغلاق وتجاوز الحد المسموح (ثانيتين)
            if COUNTER >= ALARM_THRESHOLD:
                status = "DANGER: SLEEPING!"  # تغيير النص إلى خطر: نائم
                color = (0, 0, 255)  # تغيير لون النص للآحمر
                send_to_esp32("1")  # إرسال إشارة للـ ESP32 لتشغيل الجرس فوراً
        else:
            # إذا فتح السائق عينه وكان العداد أكبر من صفر (يعني كان نايم وصحى)
            if COUNTER > 0:
                send_to_esp32("0")  # إرسال إشارة لإطفاء الجرس
            COUNTER = 0  # تصفير العداد للبدء من جديد

    # كتابة الحالة (مستيقظ/نائم) على شاشة الفيديو
    cv2.putText(frame, f"STATUS: {status}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    # تحويل الصورة من صيغة OpenCV إلى صيغة تفهمها واجهة Tkinter لعرضها
    img = cv2.imencode('.png', frame)[1].tobytes()
    img_tk = tk.PhotoImage(data=img)
    
    video_label.imgtk = img_tk  # حفظ الصورة في الذاكرة لمنع اختفائها
    video_label.configure(image=img_tk)  # تحديث الصورة المعروضة في النافذة
    video_label.after(10, update)  # تكرار الدالة بعد 10 أجزاء من الثانية (لعمل الفيديو)

update()  # تشغيل الدالة لأول مرة
root.mainloop()  # بقاء النافذة مفتوحة وعدم إغلاق البرنامج
cap.release()  # تحرير الكاميرا عند إغلاق البرنامج
