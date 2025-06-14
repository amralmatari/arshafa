from datetime import datetime
import pytz

def localize_datetime(dt):
    """تحويل التاريخ إلى المنطقة الزمنية المحلية (السعودية)"""
    if dt is None:
        return None

    # إذا كان التاريخ بدون منطقة زمنية، نفترض أنه UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)

    # تحويل إلى المنطقة الزمنية السعودية
    saudi_tz = pytz.timezone('Asia/Riyadh')
    return dt.astimezone(saudi_tz)

def display_datetime(dt):
    """عرض التاريخ بالتوقيت المحلي الصحيح"""
    if dt is None:
        return None

    # إذا كان التاريخ مخزن بـ UTC، نحوله للتوقيت المحلي
    # إذا كان مخزن بالتوقيت المحلي، نعرضه كما هو
    if dt.tzinfo is None:
        # التاريخ بدون timezone، نفترض أنه بالتوقيت المحلي
        return dt
    elif dt.tzinfo == pytz.UTC:
        # التاريخ بـ UTC، نحوله للتوقيت المحلي
        saudi_tz = pytz.timezone('Asia/Riyadh')
        return dt.astimezone(saudi_tz)
    else:
        # التاريخ له timezone آخر، نعرضه كما هو
        return dt