# smeller/models/interpolation.py
class InterpolationType:
    LINEAR       = "linear"       #– Линейная интерполяция.
    EXPONENTIAL  = "exponential"  #– Экспоненциальная интерполяция.
    SINUSOIDAL   = "sinusoidal"   #– Синусоидальная интерполяция.
    STEP         = "step"         #– Шаговая (ступенчатая) интерполяция.
    FUNCTION     = "function"     #– Пользовательская функция (для расширения).